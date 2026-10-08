# Test Report
Date: 2026-10-08, native Windows x64, Python 3.12.14.

Automated run: **17 passed, 0 failed, 0 skipped**. Machine-readable evidence:
`release/test-results.xml`. These are module/regression tests, not complete
product certification. The VAD deterministic segmentation tests use a fake
speech detector; native WebRTC classification accuracy is not established.
CUDA failure tests inject a backend exception; they are not GPU inference tests.
Translation missing-model tests verify failure, not translation quality.

Native smoke: `release/native-results.json`: 7 loopback and 14 input device
entries enumerated; 148 real loopback blocks received during a 3-second capture.
This verifies callback capture, **not an English video recognition chain**.
Microphone capture deliberately not claimed. Qt startup renders 5 pages in each
language; 10 PNGs under screenshots are real application captures, without
fabricated captions. No gameplay or bilingual video screenshot is supplied.

PyInstaller directory build completed after fixing the WebRTC wheel hook.
Build diagnostics are in `release/build.log`; packaged startup evidence is in
`release/exe-smoke.json` when present. Startup checks do not verify packaged ASR,
translation, device recovery or clean-machine compatibility.

Final packaged GUI smoke **passed**: frozen=true, window_visible=true, pages=5.
An initial QtCore failure was traced to a conflicting Poppler ICU DLL on PATH;
the build spec exclusion fixed it and the actual EXE was rerun successfully.

Unperformed: 30-second EN/ZH/reference accuracy benchmarks, music/fast/mixed
speech, live mic recognition, CPU and CUDA model inference, offline isolation,
Bluetooth/sleep recovery, games and 10/30/60 minute soak. Model downloads were
attempted from verified official endpoints but throughput was insufficient to
complete weights within this delivery run. No measurements are invented.
