import numpy as np
from yuspeak.domain import Stabilizer

def test_stabilizer_common_prefix():
    s=Stabilizer(); assert s.update('hello wor') == 'hello wor'; assert s.update('hello world') == 'hello'
    assert s.update('hello world', True) == 'hello world'

def test_caption_timestamps_are_audio_timeline():
    from yuspeak.domain import AudioBlock
    b=AudioBlock(np.zeros((480,2), np.float32), 3.5, 48000)
    assert b.start == 3.5 and len(b.samples) / b.rate == .01
