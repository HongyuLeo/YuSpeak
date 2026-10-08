# YuSpeak — ChatGPT Handoff

## A. 项目基本信息
- 名称：YuSpeak，版本 0.1.0，日期 2026-10-08。
- 英文：YuSpeak — Local AI Live Bilingual Subtitles。
- 中文：YuSpeak — 本地 AI 实时双语字幕助手。
- 定位：Windows 10/11 x64 本地语音识别与中英双语字幕。
- 用户：视频观看者、会议参与者、游戏用户及语言学习者。
- 源码许可证：MIT；依赖和模型授权单独核查。
- 状态：**开发预览，需求未全部完成，不适合直接宣传为完整正式版**。

## B. 功能真实状态
已实现且验证：17 项模块测试；Qt 主窗口实际启动；中英文 5 页各一次
实际渲染截图；WASAPI 默认输出实际采集 148 音频块；设备枚举；格式导出
模块验证。构建以 release/build.log 为准；成品启动以 exe-smoke.json 为准。

已实现但未完成真实闭环验收：Whisper CPU/CUDA 模型加载与识别适配器、
Argos EN/ZH 包的 tokenizer + CTranslate2 本地翻译、麦克风采集代码、
并发流水线、字幕点击穿透/拖动/淡入淡出、原文先显示与译文更新、托盘和
全局快捷键、暂停/停止、SQLite 会话编辑、显式音频录制、下载/取消/导入。

部分完成：字幕设置、模型管理、设备恢复、语言防抖、性能仪表盘、历史管理。
未完成：术语表编辑、翻译引擎切换、启动项设置、完整模型删除与翻译导入
界面、历史搜索/合并/删除片段界面、全部样式控件、自动 CPU 回退对话框。
真实麦克风、双向模型推理、CUDA 实际调用、离线隔离、游戏、蓝牙恢复、
睡眠恢复及 10/30/60 分钟稳定性未验证。完整产品不能据此认定验收完成。

## C. 技术架构
PySide6 Essentials GUI；PyAudioWPatch WASAPI 20ms 回调；有界音频队列；
SoXR 状态保持重采样到 mono 16k；WebRTC VAD 20ms、200ms 预留、400ms
静音结束、5 秒上限；有限 ASR mailbox；faster-whisper/CTranslate2；
独立翻译队列；Argos 包 tokenizer 与本地权重；Qt Signals 发回 GUI。
原文先到 GUI，翻译随后 upsert 同一时间区间。SQLite 只在 GUI 线程写入。
字幕用 QPainterPath 实现描边/阴影，Windows 透明输入窗口标志支持穿透。
RegisterHotKey 检查冲突。配置与数据默认在 LOCALAPPDATA/YuSpeak。
模型下载才显式联网，识别只使用 local_files_only，不上传音频和逐字稿。
PyInstaller 目录式 EXE；NVIDIA 专有运行时未附带，CPU 为默认模式。

## D. 文件结构
```text
source/
  launcher.py                EXE 入口
  pyproject.toml / requirements.txt
  yuspeak.spec / build_windows.ps1
  .github/workflows/windows.yml
  hooks/hook-webrtcvad.py    wheels 元数据修复
  assets/icon.svg            品牌图标
  yuspeak/
    __main__.py / __init__.py
    ui.py                   GUI、托盘、历史和模型下载操作
    overlay.py              真实独立悬浮字幕
    hotkeys.py              Win32 全局快捷键
    audio.py                设备、采集、重采样、VAD
    pipeline.py             并发调度、有限队列、暂停停止
    engines.py              ASR、Argos 本地推理
    runtime.py              CUDA DLL 搜索目录
    domain.py               数据类、增量稳定化
    config.py               配置、数据路径
    models.py               下载、完整性、来源记录
    storage.py              SQLite、字幕导出
  tests/                    8 个测试模块
  tools/
    benchmark.py            文件推理 benchmark
    verify_native.py        原生采集与截图冒烟
    package_delivery.py     归档、许可证收集和真实 manifest
  docs/ARCHITECTURE.md / MANUAL_ACCEPTANCE.md
  release/                  测试 XML、构建/原生证据、manifest
  dist/YuSpeak/             真实运行目录（不进入源码 ZIP）
```
完整实际文件清单见 FILE_TREE.txt。交接、状态、报告与 README 保存在源码根。

## E. 如何运行
开发环境 Windows x64 + Python 3.12，安装 requirements.txt，然后
`python -m yuspeak`。运行便携版本需解压完整 ZIP，执行 YuSpeak/YuSpeak.exe，
保留 _internal。首次必须下载/导入 Whisper CT2 模型及两种 Argos 翻译包。
没有附带模型；不能在没有模型时宣称开箱即用。CPU 不需要 CUDA Toolkit。
GPU 路径与 DLL 诊断见 BUILD_AND_RELEASE.md。若 CUDA 报错应手动改 CPU。

## F. 实际测试记录
`release/test-results.xml`：17 passed / 0 failed / 0 skipped。
`release/native-results.json`：真实 Windows 系统采集 148 blocks；7 个
loopback、14 个 input 枚举项。并非 14 个唯一物理麦克风。
10 张截图来自 PySide6 实际窗口，没有用固定文本冒充语音识别。
`release/exe-smoke.json` 如存在，记录 packaged frozen GUI 启动，不证明推理。
最终 EXE 冒烟已通过：frozen=true / window_visible=true / pages=5。
修复包括 Qt metric 重名、WebRTC hook 发行包元数据、Argos NONE 未实现、
持续重采样状态、线程隔离、translation upsert 与毫秒时间戳。
未做人工视频、语音、游戏、断网和 soak 验收；见 TEST_REPORT.md。

## G. 性能
RTX 4090 24 GB，驱动 616.92；CTranslate2 CUDA count=1。
系统装有 CUDA Toolkit 13.0，但不能当成 CT2 CUDA12/cuDNN9 满足条件。
模型完整下载未完成；ASR 耗时、翻译耗时、RTF、真实字幕延迟、RSS/VRAM
推理占用与识别准确率全部 **未测试**。不能引用 1–3 秒目标作实际成绩。
Benchmark 工具是 WAV 文件推理，不能冒充真实 WASAPI 端到端测量。

## H. 打包
成品入口：source/dist/YuSpeak/YuSpeak.exe；便携 ZIP：
YuSpeak-Windows-x64-v0.1.0.zip。源码 ZIP：YuSpeak-Source-v0.1.0.zip。
这些路径相对于 YuSpeak-Delivery。安装器未生成。
最终大小/SHA256 由外层 RELEASE_MANIFEST.json 自动读取真实文件，勿从本
文猜测。源码内 manifest 的源码自身 hash 为 null，避免自引用；外层包含
实际源码 ZIP 哈希。GPU/模型推理未测试。依赖动态库随目录打包，NVIDIA
CUDA/cuDNN/cuBLAS 不随包提供。许可证目录收集实际 wheel notices，但公开
发布前仍需 LGPL 和全部传递依赖审计。

## I. GitHub 发布准备
- 推荐仓库：YuSpeak。
- Description：Local AI live bilingual subtitles for Windows with offline ASR and translation.
- Topics：windows, subtitles, speech-recognition, offline, whisper, pyside6, translation。
- 推荐 Tag：v0.1.0；Title：YuSpeak v0.1.0 — Development Preview。
- 双语 Release Notes：RELEASE_NOTES_EN.md / RELEASE_NOTES_ZH.md。
- Release 附件：真实 portable ZIP、source ZIP、外层 manifest、测试/性能报告。
- 源码仓库：yuspeak、tests、tools、assets、hooks、docs、workflow、构建文件和文档。
- 排除：dist/build/venv/cache/模型权重/录音/真实会议数据库/密钥。
- README 尚没有双语视频 demo，因为没有完成相应实际运行验收。
- 目标源码仓库：https://github.com/HongyuLeo/YuSpeak。
- 用户已授权 Codex 上传源码与必要文档；实际上传结果见 PUBLICATION_STATUS.md。
- 二进制 Release 暂缓：再分发合规审计未完成。EXE 启动通过不等于合规或模型验收通过。

## J. For ChatGPT Taking Over This Project
This project was developed by Codex. Future handoff is through the GitHub
repository https://github.com/HongyuLeo/YuSpeak and this document, not by asking
the user to upload the complete source tree or large binary files to ChatGPT.

先通过仓库链接读取本交接文档、PROJECT_STATUS.md、PUBLICATION_STATUS.md、
测试证据与实际源码。需要二进制时，仅在真正发布后从 Release 下载，不要求
用户上传全部文件。现有 manifest 中本地 ZIP 路径不是 GitHub 附件地址；
本地源码包也可能早于仓库文档修订，以 Git commit 和发布记录确认对应版本。
需要核验成品时核对哈希、版本和构建对应提交，不要依据文件名认定功能通过，
尤其不能以 GPU 枚举替代推理。
读取 PROJECT_STATUS.md 并完成真实双语闭环和 clean-host 验收再判断发布。
公开发布前检查所有 Qt/SoXR/FFmpeg 等运行时条款以及模型许可证。
获得用户 GitHub 授权后创建/更新 YuSpeak 和 prerelease，不能自动修改或删除
用户其他仓库。不要把权重、缓存、编译产物或私人音频提交源码库。
所有无法验证的状态要如实说明，不得将“实现代码”改写为“通过验收”。

## K. AI 快速接手 / AI Quick Start
**仓库入口：https://github.com/HongyuLeo/YuSpeak**。先阅读本文件，再读
PROJECT_STATUS.md、PUBLICATION_STATUS.md、TEST_REPORT.md、BENCHMARK_REPORT.md
与 THIRD_PARTY_LICENSES.md。当前是开发预览；核心 ASR、CUDA 推理和真实
双语字幕链路尚未全部验收，没有可引用的端到端性能成绩。

### 核心文件
入口 launcher.py / yuspeak/__main__.py；GUI yuspeak/ui.py；调度与背压
yuspeak/pipeline.py；采集/重采样/VAD yuspeak/audio.py；ASR/翻译
yuspeak/engines.py；CUDA DLL yuspeak/runtime.py；字幕 yuspeak/overlay.py；
模型下载 yuspeak/models.py；配置 yuspeak/config.py；历史与导出
yuspeak/storage.py。架构详见 docs/ARCHITECTURE.md。

### 开发、测试与构建
Windows x64，Python 3.12，主依赖为 PySide6 Essentials、faster-whisper、
CTranslate2、Argos Translate、PyAudioWPatch、SoXR 和 WebRTC VAD wheels；
实际版本见 requirements.txt 与 release/dependency-versions.json。
```powershell
git clone https://github.com/HongyuLeo/YuSpeak.git
cd YuSpeak
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m yuspeak
.venv\Scripts\python.exe -m pytest -q --junitxml=release/test-results.xml
.\build_windows.ps1
```
构建输出 dist/YuSpeak/YuSpeak.exe；保留整个 _internal。原生截图/采集测试：
```powershell
$env:PYTHONPATH=(Get-Location).Path
.venv\Scripts\python.exe tools/verify_native.py --screenshots work/screenshots --report work/native-results.json
```
仅在安装本地模型后运行文件推理 benchmark：
```powershell
.venv\Scripts\python.exe tools/benchmark.py sample.wav --model base --device cpu --language en
```
该工具不是实时 WASAPI 延迟测量。硬件/人工验收按 docs/MANUAL_ACCEPTANCE.md
执行。现有 17 项通过测试、148 个 loopback 音频块和 EXE GUI 启动证据不能
证明语音模型推理、真实翻译质量、CUDA 或长时间稳定性。

### 最重要问题与推荐顺序
1. 完成 CPU ASR + 英中/中英本地翻译的真实闭环，保存实际测试证据。
2. 验证兼容 CUDA 12/cuDNN 9 DLL、真实 GPU 初始化与推理；失败时明确 CPU 路径。
3. 从打包 EXE 验证真实 WASAPI/麦克风双语字幕与断网运行，核查线程退出和恢复。
4. 测量真实延迟、RTF、队列丢失及 10/30/60 分钟内存/显存稳定性。
5. 完成 Qt/SoXR/FFmpeg 等传递依赖再分发审计，再决定二进制 Pre-release。
6. 补齐 PROJECT_STATUS.md 列出的样式、模型管理、历史和术语表控件。

仅凭源码上传成功，不得改写验收状态。未来发布请记录对应 Git commit、
构建日志、测试证据、最终 SHA256 与许可审计结果。
