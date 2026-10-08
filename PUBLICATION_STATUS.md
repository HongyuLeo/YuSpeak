# Publication Status

Target repository: https://github.com/HongyuLeo/YuSpeak

The user authorized Codex to upload project source and necessary documentation.
The public repository was successfully created under the authenticated HongyuLeo
account during this operation. Source push verification is recorded separately.
The upload result is recorded after the actual remote operation; the repository
URL by itself is not evidence of a successful push.

## Verified Source Upload
- Public repository creation succeeded through the authenticated HongyuLeo account.
- Initial source commit: beffa9b (Publish YuSpeak development preview source and GitHub AI handoff).
- `git push -u origin main` succeeded; the remote main branch was created.
- 67 tracked files uploaded: source, tests, build/CI files, necessary documents,
  license, real screenshots and earlier local test/build evidence.
- Local regression tests rerun for this upload: 17 passed, 0 failed.
- No EXE, DLL, ZIP, model weights, recordings, databases or build caches were committed.
- No Release or v0.1.0 tag was created. GitHub Actions results must be checked
  separately; local test success is not a claim that remote CI passed.

## Binary Release: Deferred
No v0.1.0 tag or binary Pre-release is being created in this upload operation.
The local portable ZIP exists and its extracted EXE passed GUI startup smoke.
However, redistribution compliance for Qt/LGPL, SoXR, FFmpeg/PyAV and transitive
runtime dependencies is still pending, as documented in THIRD_PARTY_LICENSES.md.
Collecting license notices is not equivalent to completing that review.

Core ASR, CUDA inference and the real bilingual caption pipeline have not been
fully accepted. No real inference/latency benchmark, microphone speech, offline
isolation or 10/30/60-minute soak acceptance has been established. This is a
development preview, not a complete stable product.

The repository excludes binaries, models, recordings, caches and build output.
CI runs tests on pushes/PRs; binary artifact building is disabled by default and
requires an explicit manual workflow opt-in after the compliance review.
release/RELEASE_MANIFEST.json describes the earlier local build delivery only;
its ZIP names and paths are not uploaded GitHub Release assets. Documentation
has changed since that local build; a future binary release must rebuild from a
specific commit and generate fresh corresponding manifests and SHA256 values.

ChatGPT should take over through this repository link and CHATGPT_HANDOFF.md,
especially sections J and K, without requiring full-file manual uploads.
