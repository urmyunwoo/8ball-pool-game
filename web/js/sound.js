// ── Web Audio 사운드 시스템 ──────────────────────────────
let ctx = null;
let initialized = false;

export function initSound() {
    if (initialized) return;
    try {
        ctx = new (window.AudioContext || window.webkitAudioContext)();
        initialized = true;
    } catch (e) {
        initialized = false;
    }
}

export function resumeAudio() {
    if (ctx && ctx.state === 'suspended') ctx.resume();
}

function playTone(freq, dur, vol = 0.3, type = 'sine', decay = 20) {
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(vol, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + dur);
}

function playNoise(dur, vol = 0.08) {
    if (!ctx) return;
    const bufSize = ctx.sampleRate * dur | 0;
    const buf = ctx.createBuffer(1, bufSize, ctx.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < bufSize; i++) data[i] = (Math.random() * 2 - 1) * vol;
    // apply decay
    for (let i = 0; i < bufSize; i++) data[i] *= Math.exp(-i / ctx.sampleRate * 30);
    const src = ctx.createBufferSource();
    src.buffer = buf;
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(1, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
    src.connect(gain);
    gain.connect(ctx.destination);
    src.start(ctx.currentTime);
}

export function playBallHit(speed) {
    if (!ctx) return;
    const vol = Math.min(1.0, Math.max(0.1, speed / 500));
    playTone(3200, 0.06, vol * 0.3);
    playTone(4800, 0.04, vol * 0.2);
    playTone(800, 0.05, vol * 0.15);
    playNoise(0.03, vol * 0.06);
}

export function playWallHit(speed) {
    if (!ctx) return;
    const vol = Math.min(1.0, Math.max(0.1, speed / 500));
    playTone(400, 0.07, vol * 0.25);
    playTone(900, 0.05, vol * 0.15);
    playNoise(0.04, vol * 0.08);
}

export function playPocket() {
    if (!ctx) return;
    playTone(200, 0.2, 0.3);
    playTone(350, 0.15, 0.2);
    playNoise(0.15, 0.05);
}

export function playCueShoot() {
    if (!ctx) return;
    playTone(2000, 0.08, 0.25);
    playTone(3500, 0.05, 0.15);
    playTone(1200, 0.06, 0.2);
    playNoise(0.03, 0.08);
}

export function playWin() {
    if (!ctx) return;
    const notes = [523.25, 659.25, 783.99, 1046.5];
    notes.forEach((f, i) => {
        setTimeout(() => playTone(f, 0.4, 0.2), i * 100);
    });
}

export function playFoul() {
    if (!ctx) return;
    playTone(180, 0.25, 0.3);
    playTone(220, 0.2, 0.2);
    playTone(260, 0.15, 0.12);
}

export function playClick() {
    if (!ctx) return;
    playTone(1800, 0.03, 0.2);
}
