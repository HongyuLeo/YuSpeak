import ctypes
import sys
from ctypes import wintypes
from PySide6.QtCore import QAbstractNativeEventFilter, QObject, Signal
from PySide6.QtWidgets import QApplication


def parse_hotkey(text):
    tokens=text.upper().replace(' ','').split('+'); mods=0
    values={'ALT':1,'CTRL':2,'CONTROL':2,'SHIFT':4,'WIN':8}
    for token in tokens[:-1]:
        if token not in values: raise ValueError(f'Invalid modifier: {token}')
        mods |= values[token]
    if not mods:raise ValueError('Global shortcut requires a modifier')
    key=tokens[-1]
    if len(key)==1 and key.isalnum():vk=ord(key)
    elif key.startswith('F') and key[1:].isdigit() and 1<=int(key[1:])<=24:vk=111+int(key[1:])
    else:raise ValueError(f'Invalid key: {key}')
    return mods|0x4000,vk


class Filter(QAbstractNativeEventFilter):
    def __init__(self, owner):super().__init__(); self.owner=owner
    def nativeEventFilter(self,event_type,message):
        if sys.platform=='win32':
            msg=wintypes.MSG.from_address(int(message))
            if msg.message==0x0312 and int(msg.wParam) in self.owner.actions:
                self.owner.actions[int(msg.wParam)](); return True,0
        return False,0


class GlobalHotkeys(QObject):
    error=Signal(str)
    def __init__(self,parent,bindings,callbacks):
        super().__init__(parent); self.bindings=bindings; self.callbacks=callbacks; self.actions={}; self.filter=Filter(self); QApplication.instance().installNativeEventFilter(self.filter)
    def register(self):
        self.unregister()
        if sys.platform!='win32':return
        seen=set()
        for i,(action,callback) in enumerate(zip(('overlay','listen','lock'),self.callbacks),0x5900):
            try:
                mods,key=parse_hotkey(self.bindings[action])
                if (mods,key) in seen:raise ValueError('Duplicate shortcut')
                seen.add((mods,key))
                if not ctypes.windll.user32.RegisterHotKey(None,i,mods,key):raise ValueError(f'Shortcut conflict: {self.bindings[action]}')
                self.actions[i]=callback
            except Exception as exc:self.error.emit(str(exc))
    def unregister(self):
        if sys.platform=='win32':
            for key in self.actions:ctypes.windll.user32.UnregisterHotKey(None,key)
        self.actions.clear()
