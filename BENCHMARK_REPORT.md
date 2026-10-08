# Benchmark Report
No completed ASR/translation benchmark is available in this delivery.

| Metric | Actual state |
|---|---|
| Hardware | NVIDIA GeForce RTX 4090 24 GB detected by nvidia-smi |
| Driver | 616.92 |
| CTranslate2 device count | 1; does not establish successful CUDA inference |
| ASR model | tiny download attempted; no completed benchmark |
| Translation models | official EN/ZH v1.9 endpoints resolved; inference untested |
| CPU inference speed / RTF | 未测试 / Not tested |
| CUDA inference speed / RTF | 未测试 / Not tested |
| Model initialization | 未测试 / Not tested |
| Translation latency | 未测试 / Not tested |
| Live end-to-end latency | 未测试 / Not tested |
| RSS / GPU VRAM during inference | 未测试 / Not tested |
| WER / CER | 未测试; no reference dataset used |
| 10 / 30 / 60 min soak | 未测试 / Not tested |

`tools/benchmark.py` is a local PCM16 WAV inference benchmark after models are
installed. It resamples correctly and labels itself file inference, not live
capture. It reports end-to-end live delay as null. Use manual acceptance with
annotated audio events for real subtitle delay. 1–3 s is an engineering goal,
not a result. No benchmark sample contains user private audio.
