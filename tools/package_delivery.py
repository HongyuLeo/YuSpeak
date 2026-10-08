"""Create archives and truthful manifests from actual artifact/test files."""
from __future__ import annotations
import hashlib, importlib.metadata, json, platform, shutil, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]; DELIVERY=ROOT.parent
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while b:=f.read(1024*1024):h.update(b)
    return h.hexdigest()
def archive(source,target,exclude=()):
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in source.rglob('*'):
            rel=p.relative_to(source)
            if p.is_file() and not any(part in exclude for part in rel.parts):z.write(p,str(Path(source.name)/rel))
def main():
    excluded=('build','dist','__pycache__','.pytest_cache','.venv','.git')
    (ROOT/'FILE_TREE.txt').write_text('\n'.join(str(p.relative_to(ROOT)) for p in sorted(ROOT.rglob('*')) if p.is_file() and not any(part in excluded for part in p.relative_to(ROOT).parts))+'\n','utf-8')
    versions={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    (ROOT/'release'/'dependency-versions.json').write_text(json.dumps(versions,indent=2),'utf-8')
    runtime=ROOT/'dist'/'YuSpeak'
    portable=DELIVERY/'YuSpeak-Windows-x64-v0.1.0.zip'; source=DELIVERY/'YuSpeak-Source-v0.1.0.zip'
    if (runtime/'YuSpeak.exe').exists():
        licenses=runtime/'licenses'; licenses.mkdir(exist_ok=True)
        for dist in importlib.metadata.distributions():
            for f in dist.files or []:
                if any(x.lower().startswith(('license','copying','notice')) for x in f.parts) and dist.locate_file(f).is_file():
                    dest=licenses/dist.metadata['Name']/Path(*f.parts); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(dist.locate_file(f),dest)
        for name in ('LICENSE','THIRD_PARTY_LICENSES.md','README.zh-CN.md','BUILD_AND_RELEASE.md'):shutil.copy2(ROOT/name,runtime/name)
        archive(runtime,portable)
    tests=ET.parse(ROOT/'release'/'test-results.xml').getroot(); suites=list(tests) if tests.tag=='testsuites' else [tests]
    total=sum(int(x.get('tests',0)) for x in suites); failed=sum(int(x.get('failures',0))+int(x.get('errors',0)) for x in suites); skipped=sum(int(x.get('skipped',0)) for x in suites)
    native=json.loads((ROOT/'release'/'native-results.json').read_text('utf-8'))
    smoke_path=ROOT/'release'/'exe-smoke.json'
    smoke=json.loads(smoke_path.read_text('utf-8')) if smoke_path.exists() else None
    source_rel='YuSpeak-Source-v0.1.0.zip'
    manifest=dict(project_name='YuSpeak',version='0.1.0',build_date='2026-10-08',git_commit=None,repository_suggestion='YuSpeak',platform='Windows 10/11',architecture='x64',source_archive=source_rel,portable_archive=portable.name if portable.exists() else None,installer_archive=None,artifact_paths={},artifact_sizes={},artifact_sha256={},executable_entry='YuSpeak/YuSpeak.exe' if portable.exists() else None,build_status='built_development_preview' if portable.exists() else 'source_only',build_environment=dict(os=platform.platform(),python=platform.python_version()),tests_executed=total,tests_passed=total-failed-skipped,tests_failed=failed,tests_skipped=skipped,gpu_verified=False,cpu_verified=False,audio_loopback_verified=native['loopback_verified'],microphone_verified=False,translation_verified=False,offline_verified=False,known_issues=['Full bilingual inference acceptance not yet completed','CUDA runtime not bundled or verified','Mic speech and game coverage unverified','10/30/60 minute soak unperformed','Advanced requested UI controls incomplete','Third-party/model redistribution audit pending'],model_dependencies=['Systran/faster-whisper-tiny/base/small/medium/large-v3','Argos translate-en_zh-1_9','Argos translate-zh_en-1_9'],required_runtime_dependencies=['Bundled Python/Qt/CTranslate2/PortAudio runtime','Optional NVIDIA CUDA 12 cuBLAS and cuDNN 9; not bundled'],release_assets=[],publication_status='not_published_not_ready_for_stable_release')
    for p in [portable] if portable.exists() else []:
        manifest['artifact_paths'][p.name]=p.name;manifest['artifact_sizes'][p.name]=p.stat().st_size;manifest['artifact_sha256'][p.name]=sha(p);manifest['release_assets'].append(p.name)
    manifest['artifact_paths'][source_rel]=source_rel
    manifest['artifact_sizes'][source_rel]=None; manifest['artifact_sha256'][source_rel]=None
    manifest['source_archive_hash_note']='Source hash is in outer manifest only; embedding its own hash is self-referential.'
    manifest['executable_startup_verified']=bool(smoke and smoke.get('frozen') and smoke.get('window_visible'))
    manifest['packaged_model_inference_verified']=False
    (ROOT/'release'/'RELEASE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
    archive(ROOT,source,exclude=excluded)
    manifest['artifact_sizes'][source.name]=source.stat().st_size;manifest['artifact_sha256'][source.name]=sha(source);manifest['release_assets'].append(source.name)
    (DELIVERY/'RELEASE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
    for p in ROOT.glob('*.md'):shutil.copy2(p,DELIVERY/p.name)
    print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
