from __future__ import annotations
import logging, os, shutil, sys, threading, time
from pathlib import Path
from PySide6.QtCore import QObject, Signal, Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication,QCheckBox,QComboBox,QFileDialog,QFormLayout,QHBoxLayout,QLabel,QLineEdit,QMainWindow,QMenu,QMessageBox,QProgressBar,QPushButton,QSpinBox,QStackedWidget,QSystemTrayIcon,QTableWidget,QTableWidgetItem,QVBoxLayout,QWidget
from .config import Settings,data_dir,resource
from .audio import devices
from .overlay import CaptionOverlay
from .pipeline import Pipeline
from .storage import Store
from .hotkeys import GlobalHotkeys


class ModelJob(QObject):
    progress=Signal(str,int,object); done=Signal(str); failed=Signal(str)
    def __init__(self):super().__init__(); self.cancel=threading.Event(); self.thread=None
    def run(self,fn):
        if self.thread and self.thread.is_alive():return
        self.cancel.clear()
        def work():
            try:self.done.emit(str(fn(lambda name,n,total:self.progress.emit(name,n,total),self.cancel)))
            except Exception as e:self.failed.emit(str(e))
        self.thread=threading.Thread(target=work,daemon=True); self.thread.start()


class Window(QMainWindow):
    def __init__(self):
        super().__init__(); self.s=Settings.load(); self.store=Store(); self.sid=None; self.latest=-1.0
        self.pipeline=Pipeline(self.s); self.pipeline.caption.connect(self.caption); self.pipeline.status.connect(self.status); self.pipeline.failed.connect(self.error); self.pipeline.finished.connect(self.finished); self.pipeline.metrics.connect(self.metrics_changed)
        self.pipeline.level.connect(lambda v:self.level.setValue(min(100,int(v*350))))
        self.overlay=CaptionOverlay(self.s.caption); self.overlay.moved.connect(self.remember)
        self.job=ModelJob(); self.job.progress.connect(self.progress); self.job.done.connect(self.download_done); self.job.failed.connect(self.error)
        self.build(); self.tray=QSystemTrayIcon(self); self.tray.setIcon(self.windowIcon()); self.tray.activated.connect(lambda *_:self.showNormal()); self.make_tray()
        self.hotkeys=GlobalHotkeys(self,self.s.hotkeys,[self.toggle_overlay,self.start_pause,self.unlock]); self.hotkeys.error.connect(self.error); QTimer.singleShot(100,self.hotkeys.register)
        r=self.screen().availableGeometry(); self.overlay.move(self.s.caption.x or r.x()+(r.width()-self.overlay.width())//2,self.s.caption.y or r.bottom()-self.overlay.height()-35)
        if not (self.s.models/f'whisper-{self.s.model}'/'model.bin').exists():self.pages.setCurrentIndex(2)
    def t(self,zh,en):return zh if self.s.ui_language=='zh' else en
    def b(self,zh,en,fn):
        b=QPushButton(self.t(zh,en)); b.clicked.connect(fn); return b
    def page(self,zh,en):
        w=QWidget(); l=QVBoxLayout(w); l.setContentsMargins(28,24,28,24); q=QLabel(self.t(zh,en)); q.setObjectName('heading'); l.addWidget(q); self.pages.addWidget(w); return l
    def build(self):
        self.setWindowTitle('YuSpeak'); self.setWindowIcon(QIcon(str(resource('icon.svg')))); self.resize(1040,740); self.setMinimumSize(840,650)
        root=QWidget(); row=QHBoxLayout(root); sidebar=QWidget(); sidebar.setObjectName('sidebar'); nav=QVBoxLayout(sidebar); brand=QLabel('YuSpeak'); brand.setObjectName('brand'); nav.addWidget(brand); nav.addWidget(QLabel(self.t('本地 AI 双语字幕','Local AI subtitles'))); nav.addSpacing(24); self.pages=QStackedWidget()
        for i,(zh,en) in enumerate([('工作台','Workspace'),('字幕外观','Captions'),('模型管理','Models'),('会话记录','History'),('设置','Settings')]):nav.addWidget(self.b(zh,en,lambda _,n=i:self.open_page(n)))
        nav.addStretch(); nav.addWidget(QLabel('v0.1.0')); sidebar.setFixedWidth(185); row.addWidget(sidebar); row.addWidget(self.pages,1); self.setCentralWidget(root)
        l=self.page('实时字幕工作台','Live Caption Workspace'); self.state=QLabel(self.t('已停止 · 不采集音频','Stopped · no audio capture')); l.addWidget(self.state); f=QFormLayout()
        self.source=QComboBox(); self.source.addItem(self.t('系统音频 · WASAPI','System audio · WASAPI'),'system'); self.source.addItem(self.t('麦克风','Microphone'),'microphone'); self.source.setCurrentIndex(0 if self.s.source=='system' else 1); self.device=QComboBox(); self.source.currentIndexChanged.connect(self.refresh_devices); self.refresh_devices(); f.addRow(self.t('音频来源','Audio source'),self.source); f.addRow(self.t('输入设备','Input device'),self.device); f.addRow('',self.b('重新检测设备','Refresh devices',self.refresh_devices))
        self.language=QComboBox()
        for zh,en,value in [('英语 → 中文','English → Chinese','en'),('中文 → 英语','Chinese → English','zh'),('自动检测','Automatic detection','auto')]:self.language.addItem(self.t(zh,en),value)
        self.language.setCurrentIndex(max(0,self.language.findData(self.s.language))); f.addRow(self.t('语言方向','Language direction'),self.language); l.addLayout(f)
        self.level=QProgressBar(); self.level.setTextVisible(False); self.level.setFixedHeight(6); l.addWidget(self.level); self.preview=QLabel(self.t('等待真实识别结果','Waiting for speech')); self.preview.setObjectName('preview'); self.preview.setWordWrap(True); l.addWidget(self.preview,1)
        controls=QHBoxLayout(); self.start=self.b('开始识别','Start recognition',self.start_pause); self.start.setObjectName('primary'); controls.addWidget(self.start); controls.addWidget(self.b('停止','Stop',self.stop)); controls.addWidget(self.b('显示/隐藏字幕','Toggle captions',self.toggle_overlay)); l.addLayout(controls); self.metrics_label=QLabel(self.t('推理设备尚未初始化','Backend not initialized')); self.metrics_label.setWordWrap(True); l.addWidget(self.metrics_label)
        l=self.page('字幕外观','Caption Appearance'); f=QFormLayout()
        for zh,en,key,low,high in [('字号','Font size','size',14,64),('宽度','Width','width',400,1800),('最大行数','Max lines','lines',1,5),('描边','Outline','outline',0,5),('行间距','Spacing','spacing',0,30),('背景透明度','Background opacity','opacity',0,100)]:
            spin=QSpinBox(); spin.setRange(low,high); spin.setValue(getattr(self.s.caption,key)); spin.valueChanged.connect(lambda v,k=key:self.style(k,v)); f.addRow(self.t(zh,en),spin)
        font=QLineEdit(self.s.caption.font); font.editingFinished.connect(lambda:self.style('font',font.text())); f.addRow(self.t('字体','Font'),font)
        mode=QComboBox()
        for zh,en,key in [('双语','Bilingual','bilingual'),('仅中文','Chinese only','zh'),('仅英文','English only','en')]:mode.addItem(self.t(zh,en),key)
        mode.setCurrentIndex(max(0,mode.findData(self.s.caption.mode))); mode.currentIndexChanged.connect(lambda:self.style('mode',mode.currentData())); f.addRow(self.t('显示模式','Display mode'),mode)
        l.addLayout(f); l.addWidget(self.b('锁定/解锁字幕位置','Lock/unlock position',self.unlock)); l.addStretch()
        l=self.page('本地模型管理','Local Model Manager'); f=QFormLayout(); self.model=QComboBox(); self.model.addItems(['tiny','base','small','medium','large-v3']); self.model.setCurrentText(self.s.model); self.backend=QComboBox(); self.backend.addItem('CPU · INT8','cpu'); self.backend.addItem('CUDA · FP16','cuda'); self.backend.setCurrentIndex(1 if self.s.inference=='cuda' else 0); f.addRow('ASR',self.model); f.addRow(self.t('推理设备','Inference device'),self.backend); l.addLayout(f)
        l.addWidget(self.b('下载选中 ASR 模型','Download selected ASR model',self.download_asr)); l.addWidget(self.b('导入本地 ASR 目录','Import local ASR folder',self.import_asr)); l.addWidget(self.b('安装英文 → 中文翻译','Install English → Chinese',lambda:self.download_argos('en','zh'))); l.addWidget(self.b('安装中文 → 英文翻译','Install Chinese → English',lambda:self.download_argos('zh','en'))); self.modelpath=QLabel(str(self.s.models)); self.modelpath.setWordWrap(True); l.addWidget(self.modelpath); self.download_label=QLabel(); l.addWidget(self.download_label); self.download_bar=QProgressBar(); l.addWidget(self.download_bar); l.addWidget(self.b('取消下载','Cancel download',self.job.cancel.set)); l.addStretch()
        l=self.page('本地会话记录','Local Session History'); self.sessions=QComboBox(); self.sessions.currentIndexChanged.connect(self.load_history); l.addWidget(self.sessions); self.table=QTableWidget(0,4); self.table.setHorizontalHeaderLabels([self.t('开始','Start'),self.t('结束','End'),self.t('原文','Original'),self.t('译文','Translation')]); self.table.setColumnWidth(2,260); self.table.horizontalHeader().setStretchLastSection(True); l.addWidget(self.table,1)
        controls=QHBoxLayout(); controls.addWidget(self.b('保存编辑','Save edits',self.save_edits)); controls.addWidget(self.b('删除会话','Delete session',self.delete_history)); l.addLayout(controls); controls=QHBoxLayout()
        for fmt in ('txt','json','srt','vtt'):controls.addWidget(self.b(fmt.upper(),fmt.upper(),lambda _,k=fmt:self.export(k)))
        l.addLayout(controls)
        l=self.page('偏好设置','Preferences'); f=QFormLayout(); lang=QComboBox(); lang.addItem('简体中文','zh'); lang.addItem('English','en'); lang.setCurrentIndex(0 if self.s.ui_language=='zh' else 1); lang.currentIndexChanged.connect(lambda:self.change_language(lang.currentData())); f.addRow(self.t('界面语言','UI language'),lang)
        theme=QComboBox(); theme.addItem(self.t('深色','Dark'),'dark'); theme.addItem(self.t('浅色','Light'),'light'); theme.setCurrentIndex(0 if self.s.theme=='dark' else 1); theme.currentIndexChanged.connect(lambda:self.theme(theme.currentData())); f.addRow(self.t('主题','Theme'),theme)
        for zh,en,key in [('保存文字会话','Save text sessions','save_sessions'),('保存音频（开启后会录音）','Save audio (records when enabled)','save_audio'),('关闭到系统托盘','Close to tray','close_to_tray')]:
            c=QCheckBox(); c.setChecked(getattr(self.s,key)); c.toggled.connect(lambda v,k=key:self.setting(k,v)); f.addRow(self.t(zh,en),c)
        for key,zh,en in [('overlay','字幕快捷键','Caption shortcut'),('listen','开始/暂停快捷键','Start/pause shortcut'),('lock','锁定快捷键','Lock shortcut')]:
            e=QLineEdit(self.s.hotkeys[key]); e.editingFinished.connect(lambda k=key,editor=e:self.hotkey(k,editor.text())); f.addRow(self.t(zh,en),e)
        l.addLayout(f); l.addWidget(QLabel(self.t('运行时不上传音频、文字或日志。','No audio, text or logs are uploaded.'))); l.addStretch(); self.theme(self.s.theme)
    def refresh_devices(self):
        self.device.clear(); self.device.addItem(self.t('跟随系统默认','Follow system default'),'')
        try:
            for name in dict.fromkeys(d['name'] for d in devices(self.source.currentData())):self.device.addItem(name,name)
        except Exception as e:self.device.addItem(str(e),'')
    def open_page(self,n):
        self.pages.setCurrentIndex(n)
        if n==3:
            self.sessions.clear()
            for sid,start,end,source,lang in self.store.search():self.sessions.addItem(time.strftime('%Y-%m-%d %H:%M',time.localtime(start))+f' · {source} · {lang}',sid)
    def load_history(self):
        self.table.setRowCount(0); sid=self.sessions.currentData()
        if sid is None:return
        for row in self.store.db.execute('SELECT id,start,end,original,translation FROM captions WHERE session_id=? ORDER BY start',(sid,)):
            r=self.table.rowCount(); self.table.insertRow(r)
            for c,value in enumerate(row[1:]):item=QTableWidgetItem(str(value)); item.setData(Qt.UserRole,row[0]); self.table.setItem(r,c,item)
    def save_edits(self):
        try:
            for r in range(self.table.rowCount()):
                a,b=map(float,[self.table.item(r,c).text() for c in (0,1)])
                if a<0 or b<=a:raise ValueError('Invalid interval')
                self.store.db.execute('UPDATE captions SET start=?,end=?,original=?,translation=? WHERE id=?',(a,b,self.table.item(r,2).text(),self.table.item(r,3).text(),self.table.item(r,0).data(Qt.UserRole)))
            self.store.db.commit()
        except Exception as e:self.store.db.rollback(); self.error(str(e))
    def delete_history(self):
        sid=self.sessions.currentData()
        if sid and QMessageBox.question(self,'YuSpeak',self.t('删除会话？','Delete session?'))==QMessageBox.Yes:self.store.db.execute('DELETE FROM captions WHERE session_id=?',(sid,)); self.store.db.execute('DELETE FROM sessions WHERE id=?',(sid,)); self.store.db.commit(); self.open_page(3)
    def export(self,kind):
        sid=self.sessions.currentData()
        if sid is None:return
        p,_=QFileDialog.getSaveFileName(self,self.t('导出','Export'),f'YuSpeak.{kind}',f'{kind.upper()} (*.{kind})')
        if p:self.store.export(sid,p,kind)
    def start_pause(self):
        if self.pipeline.running:self.pipeline.pause(); return
        self.s.source=self.source.currentData(); self.s.device_name=self.device.currentData(); self.s.language=self.language.currentData(); self.s.model=self.model.currentText(); self.s.inference=self.backend.currentData(); self.s.save(); self.sid=self.store.session(time.time(),self.s.source,self.s.language) if self.s.save_sessions else None; self.latest=-1; self.pipeline.start(); self.source.setEnabled(False); self.start.setText(self.t('暂停 / 继续','Pause / resume'))
    def stop(self):self.pipeline.stop()
    def finished(self):
        if self.sid:self.store.close(self.sid,time.time())
        self.sid=None; self.source.setEnabled(True); self.start.setText(self.t('开始识别','Start recognition')); self.state.setText(self.t('已停止','Stopped'))
    def caption(self,c):
        if self.sid and c.final:self.store.upsert(self.sid,c)
        if c.start<self.latest:return
        self.latest=c.start; self.preview.setText(c.original+'\n'+c.translation); self.overlay.set_caption(c.original,c.translation,not c.final,c.language)
    def status(self,code,value):
        names={'loading':self.t('加载本地模型','Loading local models'),'listening':self.t('正在监听','Listening'),'paused':self.t('已暂停','Paused'),'device':self.t('设备','Device'),'audio_error':self.t('音频异常，正在重试','Audio error; retrying'),'translation_error':self.t('翻译不可用，保留原文','Translation unavailable; original retained')}; self.state.setText(names.get(code,code)+(' · '+value if value else ''))
    def metrics_changed(self,m):self.metrics_label.setText(f'{m["device"]} · {m["precision"]} · {self.s.model} | RTF {m.get("rtf",0):.2f} | '+self.t('延迟估计','Latency estimate')+f' {m.get("latency",0):.2f}s | '+self.t('队列','Queues')+f' {m["audio_queue"]}/{m["asr_queue"]}/{m["translation_queue"]} | '+self.t('丢失','Drops')+f' {m["audio_dropped"]}/{m["asr_dropped"]}/{m["translation_dropped"]}')
    def error(self,e):self.statusBar().showMessage(self.t('错误：','Error: ')+e,30000); logging.error('%s',e)
    def style(self,k,v):setattr(self.s.caption,k,v); self.overlay.relayout(); self.overlay.update(); self.s.save()
    def remember(self,x,y):self.s.caption.x=x; self.s.caption.y=y; self.s.save()
    def unlock(self):self.overlay.set_locked(not self.s.caption.locked); self.s.save(); self.overlay.show()
    def toggle_overlay(self):self.overlay.setVisible(not self.overlay.isVisible())
    def setting(self,k,v):setattr(self.s,k,v); self.s.save()
    def hotkey(self,k,v):self.s.hotkeys[k]=v; self.hotkeys.register(); self.s.save()
    def change_language(self,language):
        if language==self.s.ui_language:return
        self.s.ui_language=language; self.s.save(); QTimer.singleShot(0,self.rebuild)
    def rebuild(self):old=self.takeCentralWidget(); self.build(); old.deleteLater(); self.make_tray()
    def theme(self,value):
        self.s.theme=value; self.s.save(); dark=value=='dark'; bg='#121619' if dark else '#f4f6f8'; panel='#1c2328' if dark else '#ffffff'; fg='#e5edf0' if dark else '#202a30'; border='#354249' if dark else '#d3dce0'
        self.setStyleSheet(f'QWidget{{background:{bg};color:{fg};font-family:"Microsoft YaHei UI";font-size:14px}} #sidebar{{background:{panel}}} #brand{{font-size:30px;font-weight:bold;color:#2eb69e}} #heading{{font-size:23px;font-weight:bold;margin-bottom:18px}} QPushButton{{padding:9px;background:{panel};border:1px solid {border};border-radius:6px}} QPushButton:hover{{border-color:#2eb69e}} #primary{{background:#168b77;color:white}} QComboBox,QLineEdit,QSpinBox{{padding:5px;border:1px solid {border};border-radius:4px}} #preview{{font-size:22px;padding:18px;background:{panel};border:1px solid {border};border-radius:6px}} QProgressBar{{border:0;background:{panel}}} QProgressBar::chunk{{background:#2eb69e}}')
    def download_asr(self):
        from .models import install_asr
        size=self.model.currentText(); self.job.run(lambda p,c:install_asr(size,self.s.models,p,c))
    def download_argos(self,a,b):
        from .models import install_argos
        self.job.run(lambda p,c:install_argos(a,b,data_dir()/'packages',p,c))
    def import_asr(self):
        src=QFileDialog.getExistingDirectory(self)
        if not src:return
        if not (Path(src)/'model.bin').exists():self.error('model.bin missing'); return
        dest=self.s.models/f'whisper-{self.model.currentText()}'
        self.job.run(lambda p,c:shutil.copytree(src,dest))
    def progress(self,name,n,total):
        self.download_label.setText(f'{name}: {n/1048576:.1f} MiB'+(f' / {total/1048576:.1f} MiB' if total else '')); self.download_bar.setRange(0,100 if total else 0)
        if total:self.download_bar.setValue(min(100,int(n*100/total)))
    def download_done(self,p):self.download_label.setText(p); self.download_bar.setRange(0,100); self.download_bar.setValue(100); self.pipeline.translator=None
    def make_tray(self):
        menu=QMenu(self)
        for zh,en,fn in [('显示主窗口','Show window',self.showNormal),('开始/暂停','Start/pause',self.start_pause),('停止','Stop',self.stop),('显示/隐藏字幕','Toggle captions',self.toggle_overlay),('退出','Quit',self.quit)]:menu.addAction(self.t(zh,en),fn)
        self.tray.setContextMenu(menu); self.tray.show()
    def quit(self):
        self.job.cancel.set(); self.hotkeys.unregister(); self.pipeline.shutdown()
        if self.job.thread:self.job.thread.join()
        self.s.save(); self.store.close_db(); self.tray.hide(); QApplication.quit()
    def closeEvent(self,e):
        e.ignore()
        if self.s.close_to_tray:self.hide()
        else:self.quit()


def run():
    from logging.handlers import RotatingFileHandler
    logging.basicConfig(level=logging.INFO,handlers=[RotatingFileHandler(data_dir()/'diagnostics.log',maxBytes=2_000_000,backupCount=2,encoding='utf-8')],format='%(asctime)s %(levelname)s %(message)s')
    app=QApplication(sys.argv); app.setApplicationName('YuSpeak'); app.setApplicationVersion('0.1.0'); app.setQuitOnLastWindowClosed(False); win=Window(); win.show()
    if '--smoke-test' in sys.argv:
        def smoke():
            import json
            win.grab().save(str(data_dir()/'exe-smoke.png'))
            (data_dir()/'exe-smoke.json').write_text(json.dumps(dict(version='0.1.0',frozen=bool(getattr(sys,'frozen',False)),window_visible=win.isVisible(),pages=win.pages.count(),test_type='GUI_startup_only_not_model_inference')), 'utf-8')
            win.quit()
        QTimer.singleShot(1500,smoke)
    return app.exec()
