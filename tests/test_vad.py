import numpy as np
from yuspeak.audio import Segmenter

class FixedVad:
    def is_speech(self,pcm,rate):return np.frombuffer(pcm,'<i2').max()>100

def test_vad_silence_does_not_infer():
    out=[]; s=Segmenter(out.append,FixedVad()); s.feed(np.zeros(16000,np.float32),0); s.flush(); assert out==[]
def test_vad_end_and_timestamps():
    out=[]; s=Segmenter(out.append,FixedVad()); s.feed(np.ones(16000,np.float32)*.1,3); s.feed(np.zeros(8000,np.float32),4); assert out[-1].final; assert out[-1].start==3; assert 4<=out[-1].end<=4.2
def test_vad_max_segment_bounds():
    out=[]; s=Segmenter(out.append,FixedVad(),max_seconds=2); s.feed(np.ones(64000,np.float32)*.1,0); s.flush(); assert all(len(x.audio)<=32000 for x in out); assert len([x for x in out if x.final])>=2
