# YuSpeak — AI Project Handoff

Repository: https://github.com/HongyuLeo/YuSpeak
Version: **0.1.0 development preview, not a fully accepted production release**.
This is the repository-link handoff entry for ChatGPT or another coding agent.
The user should not need to upload source ZIPs or large local binaries manually.

## Read First
Read CHATGPT_HANDOFF.md for the complete development record and quick-start
section K; PROJECT_STATUS.md for unfinished features; TEST_REPORT.md and
BENCHMARK_REPORT.md for actual evidence; PUBLICATION_STATUS.md and
THIRD_PARTY_LICENSES.md for the binary release gate. Do not infer verified
functionality from code presence, model names, GPU enumeration or EXE startup.

## Product and Actual Status
YuSpeak is a Windows x64 local audio-to-bilingual-caption application. Source
implements system WASAPI loopback and microphone capture, offline Whisper
recognition, offline Argos English/Chinese translation, a transparent desktop
overlay, Chinese/English UI, tray/global shortcuts, local history and exports.
No cloud transcription/translation service or telemetry is part of the pipeline.
Models must be explicitly downloaded or imported; they are not bundled.

Verified: 17 module tests, real system loopback capture (148 blocks in the
earlier three-second smoke), ten actual language/page screenshots and packaged
EXE GUI startup. Core ASR, real CUDA inference and the real bilingual caption
chain are **not fully accepted**. Microphone speech, offline isolation, recovery,
games, long-running stability and real end-to-end latency remain unverified.

## Architecture and Key Files
- launcher.py / yuspeak/__main__.py: application entry points.
- yuspeak/ui.py: GUI, model actions, session controls, tray and history editing.
- yuspeak/audio.py: PyAudioWPatch devices/capture, SoXR resampling and VAD.
- yuspeak/pipeline.py: capture/segment/ASR/translation workers and backpressure.
- yuspeak/engines.py: faster-whisper and local Argos tokenizer/CT2 model calls.
- yuspeak/runtime.py: persistent Windows CUDA DLL directory registration.
- yuspeak/domain.py: timestamped data classes and interim text stabilization.
- yuspeak/overlay.py / hotkeys.py: Qt overlay and Win32 RegisterHotKey.
- yuspeak/config.py: persistent settings and LOCALAPPDATA/YuSpeak paths.
- yuspeak/models.py: explicit downloads, cancellation, checks and provenance.
- yuspeak/storage.py: SQLite session text and TXT/JSON/SRT/VTT exports.
- yuspeak.spec / hooks/: directory-style PyInstaller build and dependency fixes.
- tests/: regression suite; tools/: benchmarks, native verification, packaging.
- .github/workflows/windows.yml: Windows CI tests and optional manual build.

Qt signals transfer worker output to the GUI; SQLite writes remain in the GUI
thread. Caption translation updates upsert the same audio interval. Earlier
translations cannot replace newer displayed captions. Audio is not recorded by
default; enabling save_audio explicitly records local WAV audio.

## Algorithms and Timing
Capture callbacks use approximately 20 ms blocks and a bounded 100-block queue.
Stateful SoXR resamples mono audio to 16 kHz. WebRTC VAD evaluates 20 ms frames,
uses 200 ms pre-roll and closes after 400 ms silence. Continuous segments cap at
five seconds. Audio start/end use sample timeline positions, not inference return
wall-clock times. Discontinuities flush segmentation and reset the resampler.

Whisper is quasi-streaming at the application layer. An ASR mailbox holds up to
four final windows and one replaceable partial window. Partial hypotheses use
common-prefix stabilization. Slow inference may drop old final windows; dropped
time ranges are logged and counters are shown. No zero-loss promise exists.
Translation has its own bounded queue and worker; original captions appear
first. Argos package tokenizers and local CT2 weights are used directly to avoid
implicit sentence-boundary model downloads. Full text is not logged normally.

The overlay uses fixed geometry, QPainterPath outlines/shadows and transparent
input flags. Global hotkeys require modifiers and detect registration conflicts.
Exclusive-fullscreen games may hide ordinary desktop overlays; borderless mode
is the intended game scenario, without injection or memory modification.

## Run, Dependencies and Build
Use Windows x64 with Python 3.12. Main dependencies: PySide6 Essentials,
faster-whisper/CTranslate2, Argos Translate, PyAudioWPatch, SoXR and WebRTC VAD
wheels. requirements.txt pins principal versions; release/dependency-versions.json
records the earlier local environment, not a complete reproducible lockfile.
```powershell
git clone https://github.com/HongyuLeo/YuSpeak.git
cd YuSpeak
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m yuspeak
.venv\Scripts\python.exe -m pytest -q --junitxml=release/test-results.xml
.\build_windows.ps1
```
Build entry: dist/YuSpeak/YuSpeak.exe with its complete _internal directory.
CPU INT8 is default. GPU requires compatible CUDA 12 cuBLAS and cuDNN 9 DLLs
for the chosen CTranslate2 wheel; those NVIDIA runtimes are not bundled. Explicit
YUSPEAK_CUDA_DIRS can register runtime folders. CUDA detection alone is not proof
of successful model loading or inference. See BUILD_AND_RELEASE.md.

## Testing and Evidence
Local regression command above covers configuration, resampling, deterministic
VAD segmentation, timestamps, bounded queues, missing-model errors, injected GPU
failure, cancellation/checksums, shortcut parsing and exports. Some tests use
fakes deliberately; they do not establish speech accuracy or GPU operation.
release/test-results.xml, native-results.json, exe-smoke.json and build.log
describe earlier local checks. Remote CI status must be checked independently.

Native Windows capture/screenshot tool (not microphone speech acceptance):
```powershell
$env:PYTHONPATH=(Get-Location).Path
.venv\Scripts\python.exe tools/verify_native.py --screenshots work/screenshots --report work/native-results.json
```
After installing local models, file benchmark:
```powershell
.venv\Scripts\python.exe tools/benchmark.py sample.wav --model base --device cpu --language en
```
This is file inference, not a real WASAPI end-to-end latency benchmark. Follow
docs/MANUAL_ACCEPTANCE.md for actual device, CPU/GPU, offline, game and soak tests.
No measured WER/CER, live 1–3 second latency or inference RSS/VRAM is available.

## Known Issues and Recommended Order
1. Establish actual CPU ASR plus both translation directions; retain real evidence.
2. Establish genuine CUDA model loading/inference with compatible runtimes.
3. Test full WASAPI/mic bilingual flow and offline inference in packaged EXE.
4. Test stop/shutdown, disconnect/sleep recovery, stale caption behavior and soak.
5. Complete dependency redistribution review before binary Pre-release publication.
6. Finish style controls, model deletion/import management, richer history,
   glossary/backend selection and remaining settings listed in PROJECT_STATUS.md.

Five-second splits lack cross-split context; partial output can revise initial
words. Quit can wait for ongoing inference/network timeouts. UI rebuild during
an active session needs more coverage. Requirements do not guarantee 1–3 seconds.

## Publication and Privacy
Source repository is public under HongyuLeo only. Do not overwrite history or
modify unrelated repositories. No binaries/models/private recordings are tracked.
The existing local manifest describes a previous build delivery, not uploaded
GitHub Release assets. Its code/binary correspondence must not be assumed after
documentation revisions. A future binary release must rebuild from an identified
commit, rerun acceptance, collect license evidence and generate fresh hashes.

Binary Release is deferred: Qt/LGPL, SoXR, FFmpeg/PyAV and transitive runtime
redistribution review is pending. Existing EXE startup success does not complete
that review or product acceptance. Never publish unverified claims, include
credentials or commit private recordings/transcripts, models, caches or venv.
