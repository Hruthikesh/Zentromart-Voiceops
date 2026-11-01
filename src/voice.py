"""Gnani is the only speech provider. Split long WAV files into short clips."""
import os
import re
import tempfile
import wave
from pathlib import Path


class Voice:
    def __init__(self):
        if not os.getenv('GNANI_API_KEY'):
            raise ValueError('Add GNANI_API_KEY to your local .env file.')
        from gnani.stt import GnaniSTTClient
        from gnani.tts import GnaniTTSClient
        self.stt, self.tts = GnaniSTTClient(), GnaniTTSClient()
        self.language = os.getenv('LANGUAGE', 'en-IN')

    def transcribe(self, path):
        path = Path(path)
        # 25 seconds stays below the current documented 30-second REST limit.
        if path.suffix.lower() == '.wav':
            with wave.open(str(path), 'rb') as audio:
                params = audio.getparams()
                frames = audio.getnframes()
                if frames > params.framerate * 25:
                    texts = []
                    with tempfile.TemporaryDirectory() as folder:
                        while True:
                            data = audio.readframes(params.framerate * 25)
                            if not data:
                                break
                            clip = Path(folder) / 'clip.wav'
                            with wave.open(str(clip), 'wb') as out:
                                out.setparams(params)
                                out.writeframes(data)
                            texts.append(self._transcribe(clip))
                    return ' '.join(texts)
        return self._transcribe(path)

    def _transcribe(self, path):
        args = {'language_code': self.language}
        if self.language in ('en-IN', 'hi-IN'):
            args['format'] = 'transcribe'
        result = self.stt.transcribe(str(path), **args)
        if result.get('success') is False:
            raise RuntimeError('Gnani could not transcribe this file.')
        return result.get('transcript', '').strip()

    def speak(self, reply, path):
        spoken = re.sub(r'\b\d{8}\b', lambda m: ' '.join(m[0][i:i+2] for i in range(0, 8, 2)), reply)
        self.tts.synthesize(spoken, voice=os.getenv('VOICE', 'Kaveri'), model='timbre-v2.5',
                            language=self.language, output_file=str(path))
        if not Path(path).is_file() or Path(path).stat().st_size <= 44:
            raise RuntimeError('Gnani returned no usable speech file.')
