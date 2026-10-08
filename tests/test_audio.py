import numpy as np
from yuspeak.audio import StreamingResampler

def test_resample_rate_and_shape():
    r=StreamingResampler(48000); out=r.process(np.zeros((480,2),np.float32), True)
    assert out.dtype == np.float32 and 150 <= len(out) <= 170
