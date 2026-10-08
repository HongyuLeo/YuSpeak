from __future__ import annotations
import os
import re
import time
from .runtime import setup_dlls
from .config import data_dir


class ASR:
    def __init__(self, path, device='cpu'):
        if not (path / 'model.bin').is_file():
            raise FileNotFoundError(f'ASR model missing: {path}')
        setup_dlls()
        from faster_whisper import WhisperModel
        self.device = device
        self.precision = 'float16' if device == 'cuda' else 'int8'
        self.model = WhisperModel(str(path), device=device, compute_type=self.precision,
                                  cpu_threads=max(1, min(8, (os.cpu_count() or 4) // 2)),
                                  num_workers=1, local_files_only=True)
        self.locked_language = None
        self.language_confidence = 0.0
        self.candidate = None
        self.candidate_count = 0

    def transcribe(self, audio, language='en', final=True):
        t = time.perf_counter()
        segments, info = self.model.transcribe(audio, language=None if language == 'auto' else language,
                                               beam_size=3 if final else 1, vad_filter=False,
                                               condition_on_previous_text=False, temperature=0,
                                               word_timestamps=False, no_speech_threshold=.6)
        result = [s for s in segments if s.no_speech_prob < .6 and s.avg_logprob > -1.2]
        text = ''.join(s.text for s in result).strip()
        lang = language
        if language == 'auto':
            detected = info.language
            self.language_confidence = info.language_probability
            if detected in ('en', 'zh') and info.language_probability >= .7:
                if detected == self.candidate:
                    self.candidate_count += 1
                else:
                    self.candidate, self.candidate_count = detected, 1
                if self.locked_language is None or self.candidate_count >= 2:
                    self.locked_language = detected
            lang = self.locked_language or detected
        return text, lang, time.perf_counter() - t


class Translator:
    def __init__(self):
        # Set before importing Argos. spaCy downloads and package updates are never automatic.
        os.environ['ARGOS_PACKAGES_DIR'] = str(data_dir() / 'argos')
        os.environ['ARGOS_DEVICE_TYPE'] = 'cpu'
        os.environ.setdefault('XDG_DATA_HOME', str(data_dir() / 'vendor' / 'data'))
        os.environ.setdefault('XDG_CONFIG_HOME', str(data_dir() / 'vendor' / 'config'))
        os.environ.setdefault('XDG_CACHE_HOME', str(data_dir() / 'vendor' / 'cache'))
        from argostranslate import package
        self.packages = package
        self.engines = {}
        self.cache = {}
        self.glossary = []

    def installed(self):
        return [(p.from_code, p.to_code, p.package_version) for p in self.packages.get_installed_packages() if p.type == 'translate']

    def translate(self, text, source):
        target = {'en': 'zh', 'zh': 'en'}.get(source)
        if target is None:
            raise ValueError(f'Unsupported detected language: {source}')
        key = (text, source, tuple(tuple(x) for x in self.glossary))
        if key in self.cache:
            return self.cache[key]
        direction = (source, target)
        if direction not in self.engines:
            pkg = next((p for p in self.packages.get_installed_packages() if p.type == 'translate' and p.from_code == source and p.to_code == target), None)
            if pkg is None: raise FileNotFoundError(f'Translation model missing: {source} → {target}')
            import ctranslate2
            self.engines[direction] = (pkg, ctranslate2.Translator(str(pkg.package_path / 'model'), device='cpu', compute_type='int8', intra_threads=4))
        pkg, engine = self.engines[direction]
        # VAD captions are already short segments. Use Argos tokenizers and model
        # directly, avoiding an additional sentencizer model or implicit downloads.
        tokens = pkg.tokenizer.encode(text)
        prefix = [[pkg.target_prefix]] if pkg.target_prefix else None
        output = engine.translate_batch([tokens], target_prefix=prefix, replace_unknowns=True, beam_size=4, num_hypotheses=1, length_penalty=.2)
        result = pkg.tokenizer.decode(output[0].hypotheses[0])
        if pkg.target_prefix and result.startswith(pkg.target_prefix): result = result[len(pkg.target_prefix):]
        result = result.strip()
        # Phrase glossary replacements are applied only when the complete source phrase occurred.
        for original, translated in self.glossary:
            if not original or not translated:
                continue
            boundary = r'(?<!\w)' + re.escape(original) + r'(?!\w)'
            if re.search(boundary, text, re.I):
                result = re.sub(boundary, lambda _: translated, result, flags=re.I)
        if len(self.cache) >= 128:
            self.cache.clear()
        self.cache[key] = result
        return result
