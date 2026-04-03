"""
효과음 관리 — ASMR 사운드 시스템.
사실적인 당구 사운드를 numpy 합성으로 생성.
속도 기반 볼륨으로 몰입감 극대화.
"""
import pygame
import math
import os

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


_sounds: dict[str, pygame.mixer.Sound | None] = {}
_vol_sounds: dict[str, list[pygame.mixer.Sound]] = {}
_initialized = False

SAMPLE_RATE = 44100


def init_sound():
    global _initialized
    if _initialized:
        return
    try:
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
        pygame.mixer.init()
        pygame.mixer.set_num_channels(24)
        _initialized = True
        _load_sounds()
    except Exception:
        _initialized = False


# ── 사운드 합성 헬퍼 ──────────────────────────────────────

def _envelope(n_samples: int, attack: int, decay: int) -> np.ndarray:
    """어택-디케이 엔벨로프 생성."""
    env = np.ones(n_samples, dtype=np.float64)
    if attack > 0:
        env[:attack] = np.linspace(0, 1, attack)
    if decay > 0 and decay < n_samples:
        env[-decay:] = np.linspace(1, 0, decay) ** 1.5
    return env


def _make_stereo(mono: np.ndarray) -> np.ndarray:
    """모노 → 스테레오 변환."""
    return np.column_stack([mono, mono])


def _synth_ball_hit() -> list[pygame.mixer.Sound]:
    """공끼리 부딪히는 맑은 'click' 사운드 — 볼륨별 3단계."""
    sounds = []
    for vol_level in [0.25, 0.5, 0.85]:
        dur = 0.065
        n = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, n, endpoint=False)

        # 고주파 어택 (맑은 클릭)
        wave = np.sin(2 * np.pi * 3200 * t) * 0.4
        wave += np.sin(2 * np.pi * 4800 * t) * 0.25
        wave += np.sin(2 * np.pi * 6400 * t) * 0.15

        # 저주파 바디 (묵직함)
        wave += np.sin(2 * np.pi * 800 * t) * 0.2

        # 노이즈 (자연스러움)
        noise = np.random.randn(n) * 0.08
        noise_env = _envelope(n, 2, int(n * 0.7))
        wave += noise * noise_env

        # 급격한 어택 + 빠른 디케이
        env = _envelope(n, int(SAMPLE_RATE * 0.001), int(n * 0.85))
        # 지수 감쇠
        exp_decay = np.exp(-t * 60)
        wave *= env * exp_decay * vol_level

        pcm = (wave * 32767).astype(np.int16)
        sounds.append(pygame.sndarray.make_sound(_make_stereo(pcm)))
    return sounds


def _synth_wall_hit() -> list[pygame.mixer.Sound]:
    """쿠션 충돌 — 부드러운 '퍽' 사운드, 볼륨별 3단계."""
    sounds = []
    for vol_level in [0.2, 0.4, 0.7]:
        dur = 0.08
        n = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, n, endpoint=False)

        # 중저주파 (쿠션의 묵직한 느낌)
        wave = np.sin(2 * np.pi * 400 * t) * 0.35
        wave += np.sin(2 * np.pi * 900 * t) * 0.2
        wave += np.sin(2 * np.pi * 1800 * t) * 0.1

        # 부드러운 노이즈
        noise = np.random.randn(n) * 0.12
        noise_env = _envelope(n, 5, int(n * 0.6))
        wave += noise * noise_env

        env = _envelope(n, int(SAMPLE_RATE * 0.002), int(n * 0.75))
        exp_decay = np.exp(-t * 40)
        wave *= env * exp_decay * vol_level

        pcm = (wave * 32767).astype(np.int16)
        sounds.append(pygame.sndarray.make_sound(_make_stereo(pcm)))
    return sounds


def _synth_pocket() -> pygame.mixer.Sound:
    """포켓에 공이 들어가는 '툭-르르' 사운드."""
    dur = 0.25
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    # 초기 '툭' (짧은 임팩트)
    thud = np.sin(2 * np.pi * 200 * t) * 0.4
    thud += np.sin(2 * np.pi * 350 * t) * 0.2
    thud_env = np.exp(-t * 30)
    thud *= thud_env

    # '르르' (공이 포켓 안에서 구르는 소리)
    roll_start = int(SAMPLE_RATE * 0.04)
    roll = np.zeros(n)
    roll_t = t[roll_start:]
    roll_freq = 150 + (roll_t - roll_t[0]) * 200  # 점점 높아지는 톤
    roll[roll_start:] = np.sin(2 * np.pi * np.cumsum(roll_freq) / SAMPLE_RATE) * 0.15
    # 구르는 소리 노이즈
    roll_noise = np.random.randn(n) * 0.06
    roll_noise[:roll_start] = 0
    roll_noise_env = _envelope(n - roll_start, int(SAMPLE_RATE * 0.02), int(n * 0.4))
    roll_noise[roll_start:] *= roll_noise_env
    roll += roll_noise

    wave = thud + roll

    env = _envelope(n, int(SAMPLE_RATE * 0.001), int(n * 0.5))
    wave *= env * 0.7

    pcm = (wave * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(_make_stereo(pcm))


def _synth_cue_shoot() -> pygame.mixer.Sound:
    """큐대로 공 치는 '탁' 사운드."""
    dur = 0.09
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    # 날카로운 어택
    wave = np.sin(2 * np.pi * 2000 * t) * 0.3
    wave += np.sin(2 * np.pi * 3500 * t) * 0.2
    wave += np.sin(2 * np.pi * 1200 * t) * 0.25

    # 약간의 노이즈 (타격감)
    noise = np.random.randn(n) * 0.1
    noise_env = _envelope(n, 1, int(n * 0.8))
    wave += noise * noise_env

    env = _envelope(n, int(SAMPLE_RATE * 0.0005), int(n * 0.7))
    exp_decay = np.exp(-t * 50)
    wave *= env * exp_decay * 0.8

    pcm = (wave * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(_make_stereo(pcm))


def _synth_win() -> pygame.mixer.Sound:
    """승리 팡파레."""
    dur = 0.8
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    # 올라가는 3화음 아르페지오
    notes = [523.25, 659.25, 783.99, 1046.5]  # C5, E5, G5, C6
    wave = np.zeros(n)
    for i, freq in enumerate(notes):
        start = int(n * i / len(notes) * 0.5)
        seg = t[start:]
        seg_t = seg - seg[0]
        note_wave = np.sin(2 * np.pi * freq * seg_t) * 0.25
        note_wave *= np.exp(-seg_t * 3)
        wave[start:] += note_wave

    env = _envelope(n, int(SAMPLE_RATE * 0.01), int(n * 0.4))
    wave *= env * 0.6

    pcm = (wave * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(_make_stereo(pcm))


def _synth_foul() -> pygame.mixer.Sound:
    """파울 — 저음 경고 사운드."""
    dur = 0.3
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    wave = np.sin(2 * np.pi * 180 * t) * 0.35
    wave += np.sin(2 * np.pi * 220 * t) * 0.25
    # 불협화음
    wave += np.sin(2 * np.pi * 260 * t) * 0.15

    env = _envelope(n, int(SAMPLE_RATE * 0.01), int(n * 0.6))
    wave *= env * 0.5

    pcm = (wave * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(_make_stereo(pcm))


def _synth_btn_click() -> pygame.mixer.Sound:
    """버튼 클릭 사운드."""
    dur = 0.04
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    wave = np.sin(2 * np.pi * 1800 * t) * 0.3
    env = _envelope(n, 2, int(n * 0.7))
    exp_decay = np.exp(-t * 80)
    wave *= env * exp_decay * 0.5

    pcm = (wave * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(_make_stereo(pcm))


def _synth_spin_click() -> pygame.mixer.Sound:
    """스핀 조절 클릭."""
    dur = 0.03
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)

    wave = np.sin(2 * np.pi * 2400 * t) * 0.15
    env = _envelope(n, 1, int(n * 0.8))
    wave *= env * np.exp(-t * 100)

    pcm = (wave * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(_make_stereo(pcm))


# ── 사운드 로딩 ──────────────────────────────────────────

def _load_sounds():
    """assets/sounds/ 폴더 파일 우선, 없으면 합성음 사용."""
    base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sounds")

    def _try_load(filename: str) -> pygame.mixer.Sound | None:
        path = os.path.join(base, filename)
        if os.path.exists(path):
            return pygame.mixer.Sound(path)
        return None

    if not _HAS_NUMPY:
        return

    # 볼륨별 사운드 (속도에 따라 다른 소리)
    loaded = _try_load("ball_hit.wav")
    _vol_sounds["ball_hit"] = [loaded] * 3 if loaded else _synth_ball_hit()

    loaded = _try_load("wall_hit.wav")
    _vol_sounds["wall_hit"] = [loaded] * 3 if loaded else _synth_wall_hit()

    # 단일 사운드
    _sounds["pocket"]     = _try_load("pocket.wav")    or _synth_pocket()
    _sounds["cue_shoot"]  = _try_load("cue_shoot.wav") or _synth_cue_shoot()
    _sounds["win"]        = _try_load("win.wav")       or _synth_win()
    _sounds["foul"]       = _try_load("foul.wav")      or _synth_foul()
    _sounds["btn_click"]  = _try_load("btn_click.wav") or _synth_btn_click()
    _sounds["spin_click"] = _synth_spin_click()


def play(name: str):
    """기본 사운드 재생."""
    if not _initialized:
        return
    s = _sounds.get(name)
    if s:
        s.play()


def play_impact(name: str, speed: float):
    """
    충돌 속도에 따라 볼륨이 달라지는 사운드 재생.
    speed: 충돌 상대 속도 (px/s)
    """
    if not _initialized:
        return
    variants = _vol_sounds.get(name)
    if not variants:
        play(name)
        return

    # 속도에 따라 3단계 선택 (약/중/강)
    if speed < 80:
        idx = 0
    elif speed < 250:
        idx = 1
    else:
        idx = 2

    # 볼륨도 속도에 비례 (최소 0.15, 최대 1.0)
    vol = min(1.0, max(0.15, speed / 500.0))
    snd = variants[idx]
    ch = snd.play()
    if ch:
        ch.set_volume(vol)
