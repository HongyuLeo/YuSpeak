from __future__ import annotations
import logging
import queue
import threading
import time
from collections import deque
import numpy as np
import soxr
import webrtcvad
from .domain import AudioBlock, Utterance

log = logging.getLogger(__name__)


class StreamingResampler:
    def __init__(self, rate: int):
        self.rate = rate
        self.stream = soxr.ResampleStream(rate, 16000, 1, dtype='float32', quality='HQ') if rate != 16000 else None

    def process(self, audio: np.ndarray, final: bool = False):
        mono = audio.mean(axis=1) if audio.ndim == 2 else audio
        mono = np.asarray(mono, dtype=np.float32)
        return self.stream.resample_chunk(mono, last=final) if self.stream else mono


class Segmenter:
    """20 ms VAD frames; 200 ms pre-roll, 400 ms end silence, 5 s cap.

    Partial windows are replaced in the ASR mailbox. Final windows are never
    silently overwritten. Audio start/end stay in the capture sample timeline.
    """
    def __init__(self, emit, vad=None, max_seconds=5.0):
        self.emit = emit
        self.vad = vad or webrtcvad.Vad(2)
        self.pre = deque(maxlen=10)
        self.frames = []
        self.pending = np.empty(0, np.float32)
        self.pending_start = 0.0
        self.start = 0.0
        self.silence = 0
        self.voice = 0
        self.id = 0
        self.active = False
        self.last_partial = 0
        self.limit = int(max_seconds / .02)

    def feed(self, samples, start):
        if not len(self.pending):
            self.pending_start = start
        self.pending = np.concatenate((self.pending, samples))
        offset = 0
        while len(self.pending) - offset >= 320:
            frame = self.pending[offset:offset + 320].copy()
            stamp = self.pending_start + offset / 16000
            pcm = (np.clip(frame, -1, 1) * 32767).astype('<i2').tobytes()
            speech = self.vad.is_speech(pcm, 16000)
            if not self.active:
                self.pre.append((frame, stamp))
                if speech:
                    self.voice += 1
                else:
                    self.voice = 0
                if self.voice >= 3:
                    self.id += 1
                    self.active = True
                    self.start = self.pre[0][1]
                    self.frames = [f for f, _ in self.pre]
                    self.pre.clear()
                    self.silence = 0
                    self.last_partial = 0
            else:
                self.frames.append(frame)
                self.silence = 0 if speech else self.silence + 1
                if self.silence >= 20 or len(self.frames) >= self.limit:
                    self._emit(True)
                    self._reset()
                elif len(self.frames) >= 40 and len(self.frames) - self.last_partial >= 35:
                    self._emit(False)
                    self.last_partial = len(self.frames)
            offset += 320
        self.pending = self.pending[offset:]
        self.pending_start += offset / 16000

    def _emit(self, final):
        frames = self.frames[:-max(0, self.silence - 5)] if self.silence > 5 else self.frames
        if frames:
            a = np.concatenate(frames)
            self.emit(Utterance(self.id, a, self.start, self.start + len(a) / 16000, final, time.monotonic()))

    def _reset(self):
        self.frames = []
        self.pre.clear()
        self.active = False
        self.silence = self.voice = 0

    def flush(self):
        if self.active:
            self._emit(True)
        self._reset()
        self.pending = np.empty(0, np.float32)


def devices(source: str):
    import pyaudiowpatch as pa
    with pa.PyAudio() as p:
        if source == 'system':
            return [dict(d) for d in p.get_loopback_device_info_generator()]
        return [dict(p.get_device_info_by_index(i)) for i in range(p.get_device_count())
                if p.get_device_info_by_index(i)['maxInputChannels'] > 0
                and not p.get_device_info_by_index(i).get('isLoopbackDevice')]


class Capture:
    def __init__(self, source, name, output, event):
        self.source, self.name, self.output, self.event = source, name, output, event
        self.stop_event = threading.Event()
        self.pa = self.stream = None
        self.dropped = 0
        self.samples = 0
        self.epoch = None

    def run(self):
        import pyaudiowpatch as pa
        while not self.stop_event.is_set():
            try:
                self.pa = pa.PyAudio()
                wasapi = self.pa.get_host_api_info_by_type(pa.paWASAPI)
                if self.source == 'system':
                    if self.name:
                        d = next((x for x in self.pa.get_loopback_device_info_generator() if x['name'] == self.name), None)
                        if not d:
                            raise RuntimeError('Selected playback device is disconnected')
                    else:
                        d = self.pa.get_default_wasapi_loopback()
                else:
                    d = next((self.pa.get_device_info_by_index(i) for i in range(self.pa.get_device_count())
                              if self.pa.get_device_info_by_index(i)['name'] == self.name
                              and self.pa.get_device_info_by_index(i)['maxInputChannels'] > 0), None) if self.name else None
                    d = d or self.pa.get_device_info_by_index(wasapi['defaultInputDevice'])
                rate, channels = int(d['defaultSampleRate']), min(2, int(d['maxInputChannels']))
                if channels < 1:
                    raise RuntimeError('Device has no capture channels')
                self.event('device', d['name'])
                self.epoch = self.epoch or time.monotonic()
                self.samples = round((time.monotonic() - self.epoch) * rate)
                last_callback = time.monotonic()
                discontinuity = True

                def callback(raw, count, info, status):
                    nonlocal last_callback, discontinuity
                    last_callback = time.monotonic()
                    a = np.frombuffer(raw, '<f4').reshape(-1, channels).copy()
                    block = AudioBlock(a, self.samples / rate, rate, discontinuity or bool(status))
                    self.samples += count
                    discontinuity = False
                    try:
                        self.output.put_nowait(block)
                    except queue.Full:
                        self.dropped += 1
                        discontinuity = True
                        log.warning('capture_overflow start=%.3f duration=%.3f', block.start, count / rate)
                    return (None, pa.paComplete if self.stop_event.is_set() else pa.paContinue)

                self.stream = self.pa.open(format=pa.paFloat32, channels=channels, rate=rate,
                                           input=True, input_device_index=d['index'],
                                           frames_per_buffer=round(rate * .02), stream_callback=callback)
                next_default_check = time.monotonic() + 2
                while not self.stop_event.wait(.2):
                    if not self.stream.is_active() or time.monotonic() - last_callback > 5:
                        raise RuntimeError('Audio stream stopped; reconnecting')
                    if self.source == 'system' and not self.name and time.monotonic() >= next_default_check:
                        next_default_check = time.monotonic() + 2
                        if self.pa.get_default_wasapi_loopback()['name'] != d['name']:
                            raise RuntimeError('Default playback device changed; reconnecting')
                break
            except Exception as exc:
                log.warning('audio_device_error %s', exc)
                self.event('error', str(exc))
            finally:
                if self.stream:
                    self.stream.close()
                    self.stream = None
                if self.pa:
                    self.pa.terminate()
                    self.pa = None
            self.stop_event.wait(2)

    def stop(self):
        self.stop_event.set()
