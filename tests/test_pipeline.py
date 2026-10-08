import numpy as np
from yuspeak.pipeline import InferenceMailbox
from yuspeak.domain import Utterance

def u(i,final):return Utterance(i,np.zeros(320,np.float32),i,i+.02,final,0)
def test_mailbox_bounded_and_partial_replaced():
    q=InferenceMailbox(2); q.put(u(1,False)); q.put(u(2,False)); assert q.get().id==2
    q.put(u(1,True)); q.put(u(2,True)); q.put(u(3,True)); assert q.skipped==1; assert q.get().id==2; assert q.get().id==3
    q.close(); assert q.get() is None

def test_final_invalidates_same_partial():
    q=InferenceMailbox(); q.put(u(1,False)); q.put(u(1,True)); assert q.get().final; q.close(); assert q.get() is None
