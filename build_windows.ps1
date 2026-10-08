$ErrorActionPreference = 'Stop'
if (!(Test-Path .venv\Scripts\python.exe)) { py -3.12 -m venv .venv }
& .venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& .venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
& .venv\Scripts\python.exe -m PyInstaller --clean --noconfirm yuspeak.spec
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
New-Item -ItemType Directory -Force release\YuSpeak-Windows-x64-v0.1.0 | Out-Null
Copy-Item -Recurse dist\YuSpeak\* release\YuSpeak-Windows-x64-v0.1.0\
Compress-Archive -Force release\YuSpeak-Windows-x64-v0.1.0 release\YuSpeak-Windows-x64-v0.1.0.zip
