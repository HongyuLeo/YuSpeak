# Build and Release
Windows 10/11 x64, Python 3.12. Use `.\build_windows.ps1` or install
requirements then `python -m PyInstaller --clean --noconfirm yuspeak.spec`.
Directory output is `dist/YuSpeak/YuSpeak.exe`; keep `_internal` alongside it.
The project WebRTC hook copies metadata for `webrtcvad-wheels`, not `webrtcvad`.
The spec excludes Poppler's incompatible ICU DLL accidentally found on PATH;
Qt uses the Windows system ICU shim instead. Windows 10 must be new enough to
provide the required ICU exports; older Windows builds remain unverified.
The portable ZIP excludes all model weights and personal data.

## GPU
CUDA detection is not GPU inference verification. CTranslate2 CUDA backend needs
compatible CUDA 12 cuBLAS and cuDNN 9 DLLs for the selected wheel; verify against
that wheel's upstream release documentation before distributing GPU runtimes.
Do not package installed CUDA 13 as if it satisfies these requirements.
Set `YUSPEAK_CUDA_DIRS` to semicolon-separated runtime directories if needed.
The loader also searches bundled/site-packages `nvidia/*/bin` and `cuda_runtime`.
DLL directory handles remain alive. This release does not bundle NVIDIA DLLs.
On load/inference failure, stop, select CPU and restart recognition; it does not
silently claim GPU operation. The entire GUI can run without GPU libraries.

## Models
Download via explicit UI actions from Systran Hugging Face repositories or the
official Argos index. ASR revisions are resolved and LFS SHA256 is checked when
available. Argos uses CRC and local SHA256; official index may lack an upstream
trusted checksum, which is recorded, not invented. No models are redistributed.
Model/tokenizer licensing must be reviewed independently before bundling.

## Verification
Run `python -m pytest -q --junitxml=release/test-results.xml`, inspect build.log,
start EXE on a clean Windows host and execute docs/MANUAL_ACCEPTANCE.md.
Check `_internal` dependencies and retained third-party license notices.
```powershell
Get-FileHash release\YuSpeak-Windows-x64-v0.1.0.zip -Algorithm SHA256
```
The Windows Actions workflow tests on windows-latest. Binary building/upload is
off by default and requires an explicit workflow_dispatch build_portable opt-in
after redistribution compliance review. It does not create a GitHub Release;
CI cannot prove physical mic, GPU, game or offline device compatibility.

## Publish
The user has authorized source/document upload to https://github.com/HongyuLeo/YuSpeak.
Binary Release is deferred while redistribution compliance review is pending.
A future authorized publisher should
review handoff, resolve missing acceptance and license verification, create the
YuSpeak repository, add source only, run CI, then create a **prerelease** tag
v0.1.0 with honest notes and attach the portable ZIP and manifest. Exclude build,
dist, models, venv, private transcripts and recordings. No installer is promised.
