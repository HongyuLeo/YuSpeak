from __future__ import annotations
import logging
import queue
import threading
import time
import wave
import numpy as np
from PySide6.QtCore import QObject, Signal
from .audio import Capture, Segmenter, StreamingResampler
from .config import data_dir
from .domain import Caption, Stabilizer

log = logging.getLogger(__name__)


class InferenceMailbox:
    def __init__(self, capacity=4):
        self.condition = threading.Condition(); self.finals = []; self.partial = None; self.capacity = capacity
        self.skipped = 0; self.closed = False

    def put(self, u):
        with self.condition:
            if u.final:
                if self.partial and self.partial.id == u.id: self.partial = None
                if len(self.finals) >= self.capacity:
                    old = self.finals.pop(0); self.skipped += 1
                    log.warning('asr_dropped_final start=%.3f end=%.3f', old.start, old.end)
                self.finals.append(u)
            else: self.partial = u
            self.condition.notify()

    def get(self):
        with self.condition:
            self.condition.wait_for(lambda: self.finals or self.partial or self.closed)
            if self.finals: return self.finals.pop(0)
            u, self.partial = self.partial, None
            return u

    def close(self):
        with self.condition: self.closed = True; self.condition.notify_all()


class Pipeline(QObject):
    caption = Signal(object)
    status = Signal(str, str)
    level = Signal(float)
    metrics = Signal(dict)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, settings):
        super().__init__(); self.settings = settings; self.running = False; self.paused = threading.Event()
        self.model_key = None; self.asr = None; self.translator = None; self.stop_event = threading.Event()
        self.threads = []; self.capture = None

    def start(self):
        if self.running: return
        self.running = True; self.stop_event.clear(); self.paused.clear()
        self.blocks = queue.Queue(100); self.mailbox = InferenceMailbox(4); self.translations = queue.Queue(12)
        self.epoch = time.monotonic(); self.record_path = None; self.diagnostics = dict(audio_dropped=0, asr_dropped=0, translation_dropped=0)
        t = threading.Thread(target=self._supervise, name='yuspeak-session', daemon=True); self.threads = [t]; t.start()

    def _supervise(self):
        workers = []
        try:
            from .engines import ASR, Translator
            key = (str(self.settings.models), self.settings.model, self.settings.inference)
            if key != self.model_key:
                self.status.emit('loading', '')
                self.asr = None
                self.asr = ASR(self.settings.models / f'whisper-{self.settings.model}', self.settings.inference)
                self.model_key = key
            if self.translator is None: self.translator = Translator()
            if self.stop_event.is_set(): return
            self.capture = Capture(self.settings.source, self.settings.device_name, self.blocks, self._event)
            self.epoch = time.monotonic()
            workers = [threading.Thread(target=fn, name=name, daemon=True) for fn,name in
                       [(self.capture.run, 'capture'), (self._segment, 'segment'), (self._asr, 'asr'), (self._translate, 'translate')]]
            self.threads.extend(workers)
            for t in workers: t.start()
            self.status.emit('listening', '')
            while not self.stop_event.wait(.2):
                self.metrics.emit(dict(device=self.asr.device, precision=self.asr.precision,
                                       audio_queue=self.blocks.qsize(), asr_queue=len(self.mailbox.finals),
                                       translation_queue=self.translations.qsize(), audio_dropped=self.capture.dropped,
                                       asr_dropped=self.mailbox.skipped, **{k:v for k,v in self.diagnostics.items() if k not in ('audio_dropped', 'asr_dropped')}))
        except Exception as exc:
            log.exception('session_failure'); self.failed.emit(str(exc))
        finally:
            self.stop_event.set()
            if self.capture: self.capture.stop()
            for t in workers[:2]: t.join()
            if hasattr(self, 'mailbox'): self.mailbox.close()
            for t in workers[2:]: t.join()
            self.running = False; self.finished.emit()

    def _event(self, kind, value): self.status.emit('audio_error' if kind == 'error' else 'device', value)

    def _segment(self):
        segmenter = Segmenter(self.mailbox.put); resampler = None; expected = None; output_start = 0.0; output_count = 0; writer = None
        if self.settings.save_audio:
            p = data_dir() / 'recordings'; p.mkdir(exist_ok=True)
            self.record_path = p / (time.strftime('%Y%m%d-%H%M%S') + '.wav')
            writer = wave.open(str(self.record_path), 'wb'); writer.setnchannels(1); writer.setsampwidth(2); writer.setframerate(16000)
        try:
            while not self.stop_event.is_set() or not self.blocks.empty():
                try: block = self.blocks.get(timeout=.1)
                except queue.Empty: continue
                if self.paused.is_set():
                    segmenter.flush(); resampler = None; continue
                if resampler is None or resampler.rate != block.rate or block.discontinuity or (expected is not None and abs(block.start - expected) > .01):
                    segmenter.flush(); resampler = StreamingResampler(block.rate); output_start = block.start; output_count = 0
                expected = block.start + len(block.samples) / block.rate
                a = resampler.process(block.samples)
                self.level.emit(float(np.sqrt(np.mean(block.samples ** 2))) if len(block.samples) else 0)
                segmenter.feed(a, output_start + output_count / 16000); output_count += len(a)
                if writer: writer.writeframes((np.clip(a,-1,1)*32767).astype('<i2').tobytes())
            if resampler:
                a = resampler.process(np.empty(0,np.float32), final=True)
                segmenter.feed(a, output_start + output_count / 16000)
            segmenter.flush()
        except Exception as exc: self.failed.emit(str(exc)); self.stop_event.set()
        finally:
            if writer: writer.close()
            self.mailbox.close()

    def _asr(self):
        stabilize = Stabilizer(); current_id = None
        try:
            while True:
                u = self.mailbox.get()
                if u is None: break
                if current_id != u.id: stabilize = Stabilizer(); current_id = u.id
                text, language, elapsed = self.asr.transcribe(u.audio, self.settings.language, u.final)
                if not text: continue
                text = stabilize.update(text, u.final)
                c = Caption(u.id, u.start, u.end, text, '', language, self.settings.source, u.final,
                            max(0, time.monotonic() - self.epoch - u.end))
                self.caption.emit(c)
                self.diagnostics.update(asr_seconds=elapsed, rtf=elapsed / max(.02, u.end-u.start), latency=c.latency,
                                        language_confidence=self.asr.language_confidence)
                if u.final:
                    try: self.translations.put(c, timeout=.05)
                    except queue.Full:
                        self.diagnostics['translation_dropped'] += 1
                        log.warning('translation_queue_full start=%.3f end=%.3f', c.start,c.end)
                        self.status.emit('translation_error', 'Translation queue full')
        except Exception as exc: self.failed.emit(str(exc)); self.stop_event.set()
        finally: self.translations.put(None)

    def _translate(self):
        from dataclasses import replace
        while True:
            c = self.translations.get()
            if c is None: break
            t = time.perf_counter()
            try:
                result = self.translator.translate(c.original, c.language)
                self.caption.emit(replace(c, translation=result, latency=max(0,time.monotonic()-self.epoch-c.end)))
            except Exception as exc: self.status.emit('translation_error', str(exc))
            self.diagnostics['translation_seconds'] = time.perf_counter() - t

    def pause(self):
        if self.paused.is_set(): self.paused.clear(); self.status.emit('listening','')
        else: self.paused.set(); self.status.emit('paused','')

    def stop(self): self.stop_event.set()

    def shutdown(self):
        self.stop()
        if self.threads: self.threads[0].join()
