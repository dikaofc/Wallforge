"""WASAPI loopback audio capture for audio-reactive wallpapers.

Captures whatever is playing on the default output device (system loopback)
and exposes an FFT spectrum via get_spectrum(). Runs in a background thread
feeding a ring buffer; the renderer reads it on the Qt thread.
"""
from __future__ import annotations

import numpy as np

from ..core.logger import setup_logger

log = setup_logger("wallforge.audio_capture")


class AudioCapture:
    def __init__(self, bins: int = 32) -> None:
        self.bins = bins
        self.spectrum = np.zeros(bins)
        self._thread = None
        self._running = False
        self._stream = None
        self._np = np

    def start(self) -> None:
        try:
            import soundcard as sc
        except Exception as exc:
            log.warning("soundcard lib unavailable: %s", exc)
            return
        try:
            # Loopback capture: a "microphone" that records the speaker output.
            self._loopback = sc.get_microphone(
                id=sc.default_speaker().id, include_loopback=True)
            self._running = True
            self._thread = __import__("threading").Thread(
                target=self._run, daemon=True)
            self._thread.start()
        except Exception as exc:
            log.warning("loopback start failed: %s", exc)

    def _run(self) -> None:
        blocksize = 1024
        try:
            with self._loopback.recorder(samplerate=44100,
                                         channels=1,
                                         blocksize=blocksize) as rec:
                while self._running:
                    data = rec.record(numframes=blocksize)
                    self._analyse(data.flatten())
        except Exception as exc:
            log.debug("loopback run ended: %s", exc)

    def _analyse(self, samples: np.ndarray) -> None:
        try:
            win = samples * np.hanning(len(samples))
            fft = np.abs(np.fft.rfft(win))
            # Log-spaced binning into self.bins buckets.
            n = len(fft)
            edges = np.logspace(0, np.log10(max(n, 2)), self.bins + 1).astype(int)
            out = np.zeros(self.bins)
            for i in range(self.bins):
                a, b = edges[i], max(edges[i + 1], edges[i] + 1)
                out[i] = fft[a:b].mean() if b > a else 0.0
            # Normalise.pps to 0..1 (sqrt for nicer visual response).
            peak = out.max() if out.max() > 0 else 1.0
            self.spectrum = np.sqrt(out / peak)
        except Exception:
            pass

    def get_spectrum(self) -> np.ndarray:
        return self.spectrum

    def stop(self) -> None:
        self._running = False
