"""No microphone capture by default. Native smoke test and real Qt screenshots."""
import argparse, json, os, queue, threading, time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from yuspeak.ui import Window
from yuspeak.audio import Capture, devices

ap=argparse.ArgumentParser(); ap.add_argument('--screenshots',type=Path,required=True); ap.add_argument('--report',type=Path,required=True); args=ap.parse_args()
args.screenshots.mkdir(parents=True,exist_ok=True); report={'mode':'native_windows_smoke','microphone_verified':False,'loopback_verified':False,'ui_pages':[]}
report['loopback_devices']=len(devices('system')); report['microphone_devices']=len(devices('microphone'))
blocks=queue.Queue(1000); errors=[]; cap=Capture('system','',blocks,lambda k,v:errors.append([k,v])); t=threading.Thread(target=cap.run); t.start(); time.sleep(3); cap.stop(); t.join(10)
report['loopback_verified']=blocks.qsize()>0 and not t.is_alive(); report['captured_blocks']=blocks.qsize(); report['device_events']=errors
app=QApplication([]); app.setQuitOnLastWindowClosed(False); win=Window(); win.show(); win.hotkeys.unregister()
def capture():
    for lang in ('zh','en'):
        win.s.ui_language=lang; old=win.takeCentralWidget(); win.build(); old.deleteLater()
        for i,name in enumerate(('workspace','captions','models','history','settings')):
            win.pages.setCurrentIndex(i); app.processEvents(); win.grab().save(str(args.screenshots/f'{lang}-{name}.png')); report['ui_pages'].append(f'{lang}-{name}')
    win.s.ui_language='zh'; win.s.save(); win.tray.hide(); win.store.close_db(); args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8'); app.quit()
QTimer.singleShot(1000,capture); app.exec()
