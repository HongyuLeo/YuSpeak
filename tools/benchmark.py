"""Reproducible local benchmark. Requires an installed model and WAV input."""
from __future__ import annotations
import argparse, json, platform, subprocess, time
from pathlib import Path
import psutil
from yuspeak.config import Settings
from yuspeak.engines import ASR, Translator

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('wav', type=Path); ap.add_argument('--model',default='base'); ap.add_argument('--device',default='cpu'); ap.add_argument('--language',default='auto'); args=ap.parse_args()
    import wave, numpy as np
    with wave.open(str(args.wav),'rb') as w:
        if w.getsampwidth()!=2:raise ValueError('Benchmark expects PCM16 WAV')
        rate,channels=w.getframerate(),w.getnchannels(); audio=np.frombuffer(w.readframes(w.getnframes()),'<i2').reshape(-1,channels).astype('float32')/32768; duration=w.getnframes()/rate
    from yuspeak.audio import StreamingResampler
    audio=StreamingResampler(rate).process(audio,True)
    s=Settings(); init=time.perf_counter(); asr=ASR(s.models/f'whisper-{args.model}', args.device); initialization=time.perf_counter()-init; t=time.perf_counter(); text,lang,asr_sec=asr.transcribe(audio,args.language,True); trans=Translator(); tt=time.perf_counter(); translation=trans.translate(text,lang) if text else ''; trans_sec=time.perf_counter()-tt
    result=dict(timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()), hardware=platform.platform(), cpu=platform.processor(), model=args.model, device=asr.device, precision=asr.precision, duration_seconds=duration, asr_seconds=asr_sec, translation_seconds=trans_sec, real_time_factor=asr_sec/max(.001,duration), text=text, translation=translation, rss_bytes=psutil.Process().memory_info().rss, gpu_verified=args.device=='cuda')
    result.update(test_type='offline_file_inference_not_live_capture',initialization_seconds=initialization,end_to_end_caption_latency=None,gpu_vram_bytes=None,accuracy=None)
    print(json.dumps(result,ensure_ascii=False,indent=2)); Path('benchmark-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
if __name__=='__main__': main()
