# Manual Acceptance
Record date, device names, model revision, language, backend and actual result.
Do not substitute mocked adapter tests for these cases.

1. Download/install both translation packages and a multilingual Whisper model.
2. Play English YouTube speech; system loopback must work with mic unused.
3. Select microphone, speak Mandarin and verify English translation.
4. Verify background-music, fast dialogue, long speech and silence cases.
5. Explicit CPU mode; then CUDA mode with actual model inference and backend log.
6. Unplug headphones/mic, change default output and sleep/resume; verify recovery.
7. Check click-through and unlocked dragging across multiple displays and DPI.
8. Borderless game overlay, and document exclusive-fullscreen limitations.
9. Disable network after all models exist; repeat ASR and both translations.
10. Run 10, 30 and 60 minutes; record RSS/VRAM/CPU/RTF/queue/drops/latency samples.
11. Export/edit/delete sessions; inspect SRT/VTT times against the audio timeline.
12. On a clean Windows machine without Python, run the extracted EXE and repeat.
13. Cancel downloads, verify no completed false model appears, retry and import.
14. Run English/Chinese UI and light/dark themes, hotkey conflicts and tray quit.

Performance goals are not measured results. For quantitative delay use annotated
audio-end times and actual caption emission times, not just inference duration.
