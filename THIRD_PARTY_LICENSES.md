# Third-Party Licenses
Review upstream LICENSE files before public redistribution. Project MIT does
not replace third-party terms. Version values below reflect this development env.

| Component | Version | Source | License | Redistribution status |
|---|---|---|---|---|
| PySide6 Essentials / Qt | 6.11.2 | pypi.org/project/PySide6-Essentials | LGPL-3.0 / GPL / commercial, module dependent | Dynamic LGPL components require notices, source/relinking rights; final audit pending |
| faster-whisper | 1.2.1 | github.com/SYSTRAN/faster-whisper | MIT | Allowed with notice |
| CTranslate2 | 4.8.2 | github.com/OpenNMT/CTranslate2 | MIT | Allowed with notice |
| Argos Translate | 1.11.0 | github.com/argosopentech/argos-translate | MIT / CC0 dual upstream | Verify shipped license |
| PyAudioWPatch / PortAudio | 0.2.12.9 | github.com/s0d3s/PyAudioWPatch | MIT and PortAudio license | Include both notices |
| WebRTC VAD wheels | 2.0.14.post1 | pypi.org/project/webrtcvad-wheels | MIT wrapper / BSD WebRTC | Include embedded notices |
| SoXR | 1.1.0 | pypi.org/project/soxr | LGPL-2.1 library / wrapper license | Final distribution compliance audit pending |
| NumPy | 2.5.3 | numpy.org | BSD and bundled math library notices | Include wheel notices |
| PyInstaller | 6.22.3 | pyinstaller.org | GPL-2.0+ with bootloader exception | Compiled app permitted by exception |
| Requests | 2.34.2 | requests.readthedocs.io | Apache-2.0 | Include notice |
| Whisper model weights | Not bundled | huggingface.co/Systran/faster-whisper-* | Model card/upstream license | Must verify pinned card and redistribution before bundling |
| Argos EN/ZH weights | index version 1.9, not bundled | github.com/argosopentech/argospm-index | Each package license, not automatically code license | Model license verification pending |
| NVIDIA CUDA/cuDNN/cuBLAS | Not bundled | developer.nvidia.com | NVIDIA proprietary redistribution terms | Do not bundle without checking permitted redistributables |

The portable package's licenses directory should contain collected installed
distribution notices. Collecting notices does not itself complete legal review.
Transitive wheel contents (FFmpeg/PyAV, ONNX Runtime, tokenizers, SentencePiece,
Sacremoses and others) also need final release audit. Public release is gated on
that audit; unverified model licenses are never treated as approved.
