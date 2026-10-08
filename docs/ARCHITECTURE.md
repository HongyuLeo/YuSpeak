# Architecture
`launcher.py` / `yuspeak.__main__` → `ui.Window`.
Qt signals are the only worker-to-GUI communication path. SQLite is written in
the GUI thread; caption translation updates upsert an existing audio interval.

`Capture` uses PyAudioWPatch WASAPI callback at 20 ms. A bounded 100-block queue
feeds `Pipeline._segment`. Stateful SoXR resampling creates mono 16 kHz samples.
Discontinuities flush segments and reset the resampler. WebRTC VAD gates speech,
with 200 ms pre-roll and 400 ms silence closure; final windows cap at 5 seconds.

`InferenceMailbox` holds at most four final windows and one replaceable interim.
An ASR thread uses faster-whisper (CPU INT8 or CUDA FP16), a stabilizer tracks
common partial prefixes, and a separate bounded translation queue feeds Argos
model weights through CTranslate2 with the package tokenizer. No sentence model
is downloaded during inference. The original is emitted before translation.
Stale translation cannot replace a newer displayed audio interval.

Audio overflow, final-window drops, translation overflow and device reconnect
are diagnosed without transcript text. Drop counters and RTF are displayed.
Stop requests capture shutdown, drains bounded audio, flushes VAD and joins workers.

The overlay uses QPainter text paths for fill/outline/shadow and fixed geometry.
Windows transparent-input flags provide actual click-through. RegisterHotKey
provides configurable global shortcuts and conflict checks. SQLite stores audio
timeline start/end, source, language and bilingual text. Config persists locally.
