import time
from PySide6.QtCore import Qt, QTimer, Signal, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QTextLayout, QTextOption
from PySide6.QtWidgets import QWidget


class CaptionOverlay(QWidget):
    moved = Signal(int,int)
    def __init__(self,style):
        super().__init__(); self.style=style; self.original=self.translation=''; self.language='en'; self.interim=False; self.visible_until=0; self.dragging=False; self.alpha=0.0
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.Tool|Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground); self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.set_locked(style.locked); self.relayout()
        self.timer=QTimer(self); self.timer.timeout.connect(self.tick); self.timer.start(40)
    def relayout(self):
        line_height=round(self.style.size*1.5)
        self.setFixedSize(self.style.width, (line_height*self.style.lines*2)+self.style.spacing+32)
    def set_locked(self,locked):
        self.style.locked=locked
        flags=self.windowFlags()
        flags=flags|Qt.WindowTransparentForInput if locked else flags & ~Qt.WindowTransparentForInput
        was=self.isVisible(); self.setWindowFlags(flags); self.setAttribute(Qt.WA_TransparentForMouseEvents,locked)
        if was:self.show()
    def set_caption(self,original,translation='',interim=False,language='en'):
        self.original,self.translation,self.interim,self.language=original,translation,interim,language
        self.visible_until=time.monotonic()+self.style.expiry; self.show(); self.update()
    def tick(self):
        target=1.0 if time.monotonic()<self.visible_until or not self.style.locked else 0.0
        self.alpha += max(-.15,min(.15,target-self.alpha)); self.update()
    def lines(self,text,font,width):
        layout=QTextLayout(text,font); option=QTextOption(); option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere); layout.setTextOption(option)
        layout.beginLayout(); result=[]
        for _ in range(self.style.lines):
            line=layout.createLine()
            if not line.isValid():break
            line.setLineWidth(width); result.append(text[line.textStart():line.textStart()+line.textLength()].strip())
        layout.endLayout(); return result
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.setOpacity(self.alpha)
        if not self.original and self.style.locked:return
        p.setPen(Qt.NoPen); p.setBrush(QColor(8,12,17,round(self.style.opacity*2.55))); p.drawRoundedRect(self.rect(),6,6)
        font=QFont(self.style.font,self.style.size,QFont.Bold if self.style.bold else QFont.Normal)
        pairs=[(self.original,self.style.original_color,self.language),(self.translation,self.style.translation_color,'zh' if self.language=='en' else 'en')]
        if self.style.mode!='bilingual':pairs=[x for x in pairs if x[2]==self.style.mode]
        if self.style.order=='translation':pairs.reverse()
        fm=__import__('PySide6.QtGui',fromlist=['QFontMetricsF']).QFontMetricsF(font); y=18+fm.ascent()
        for text,color,lang in pairs:
            if not text:continue
            if self.interim:text+=' …'
            for line in self.lines(text,font,self.width()-40):
                x=max(20,(self.width()-fm.horizontalAdvance(line))/2)
                path=QPainterPath(); path.addText(x,y,font,line)
                if self.style.shadow:
                    p.save(); p.translate(2,3); p.fillPath(path,QColor(0,0,0,180)); p.restore()
                if self.style.outline:p.setPen(QPen(QColor('#101218'),self.style.outline*2,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin)); p.drawPath(path)
                p.fillPath(path,QColor(color)); y+=fm.height()
            y+=self.style.spacing
        if not self.style.locked:p.setPen(QPen(QColor('#29bba4'),1)); p.setBrush(Qt.NoBrush); p.drawRoundedRect(self.rect().adjusted(1,1,-1,-1),6,6)
    def mousePressEvent(self,e):
        if not self.style.locked:self.dragging=True; self.origin=e.globalPosition().toPoint()-self.pos()
    def mouseMoveEvent(self,e):
        if self.dragging:self.move(e.globalPosition().toPoint()-self.origin)
    def mouseReleaseEvent(self,e):self.dragging=False; self.moved.emit(self.x(),self.y())
