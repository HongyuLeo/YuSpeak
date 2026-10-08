# Project Status
Date: 2026-10-08. Version: 0.1.0. **Development preview; full requested project
is not complete and stable publication is not recommended yet.**

## Implemented and exercised
Native Qt startup and both language page rendering; real WASAPI audio blocks;
Final packaged EXE GUI startup passed (frozen=true, visible window, five pages);
unit tests for resampling, VAD gating/time bounds, bounded ASR mailbox, missing
models, propagated GPU failure, no fabricated translation, shortcut parsing,
config persistence, cancellation, checksum checks and four export formats.

## Implemented but not accepted end-to-end
Whisper CPU/CUDA adapters, Argos bidirectional translation weights/tokenizers,
concurrent capture/segmentation/ASR/translation pipeline, recovery loop,
optional recording, partial stabilization, caption click-through and live
rendering, hotkeys/tray, history editing and model download/import.
Real model inference results are not yet available; code presence is not proof.

## Partial / missing
Full subtitle style controls (font weight/color/shadow/order UI incomplete),
model list/delete/translation import management, rich history search/segment
merge/delete controls, startup registry option, logging controls and model-path
UI, automatic CPU fallback dialog, robust task cancellation during inference,
translation backend selection and complete glossary editor are unfinished.
Microphone speech, games, sleep/resume, Bluetooth disconnect, real CUDA,
offline isolation and 10/30/60 minute soak remain unverified. No installer.

## Important fixes
Preserved resampler state; separated inference from capture/segmentation; bounded
final and translation queues with diagnostics; upserted translation updates to
avoid duplicate history cues; corrected millisecond rounding; replaced unsupported
Argos NONE sentencizer path with direct package tokenizer/model inference;
fixed Qt metric name collision and WebRTC wheel PyInstaller metadata hook.
Also diagnosed incompatible Poppler ICU DLL picked from PATH during bundling;
the spec excludes it so Qt uses the Windows ICU shim.

## Known limitations
5-second forced splits have no cross-split context. Partial display can still
revise initial words. Stop/quit waits for in-flight model inference or network
timeouts. Reconnect/default checks require physical tests. Capture overflow
counts blocks, ASR overflow counts segments, not missing word count. GUI rebuild
during an active session requires additional regression coverage. No promise of
1–3 s actual latency or transcription accuracy has been established.

## Next work
First obtain real bilingual CPU and CUDA inference with installed models, test
packaged inference on a clean host, then finish controls and glossary, improve
boundary stability, instrument soak/live latency and audit third-party licensing.
