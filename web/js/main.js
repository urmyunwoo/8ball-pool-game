import {
    WIN_W, WIN_H, FPS, SIDEBAR_W,
    TABLE_X, TABLE_Y, TABLE_W, TABLE_H,
    BALL_RADIUS, BALL_COLORS, CUSHION_SIZE,
    MAX_POWER, C_BTN_GREEN, C_BTN_ORANGE, C_BTN_BLUE, C_BTN_DARK,
    C_GOLD_LIGHT, C_TEXT_DIM,
} from './config.js';
import { Ball, Physics, castRay } from './physics.js';
import { GameLogic, TURN, PHASE, CaromLogic, CAROM_RESULT } from './game-logic.js';
import {
    drawTable, drawBalls, drawBall, drawGuideLine, drawCue, drawPowerBar,
    drawSpinIndicator, drawSidebar, drawTurnHeader, drawBallStatusBar,
    drawDialog, drawReplayOverlay, drawMenuScene, PocketEffect,
    invalidateTableCache, roundRect
} from './renderer.js';
import {
    initSound, resumeAudio, playBallHit, playWallHit,
    playPocket, playCueShoot, playWin, playFoul, playClick
} from './sound.js';

// ── Canvas Setup ───────────────────────────────────────
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
canvas.width = WIN_W;
canvas.height = WIN_H;

// scale to fit window
function resizeCanvas() {
    const scaleX = window.innerWidth / WIN_W;
    const scaleY = window.innerHeight / WIN_H;
    const scale = Math.min(scaleX, scaleY);
    canvas.style.width = `${WIN_W * scale}px`;
    canvas.style.height = `${WIN_H * scale}px`;
    canvas.style.left = `${(window.innerWidth - WIN_W * scale) / 2}px`;
    canvas.style.top = `${(window.innerHeight - WIN_H * scale) / 2}px`;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// ── Mouse Coordinate Transform ─────────────────────────
function getMousePos(e) {
    const rect = canvas.getBoundingClientRect();
    return {
        x: (e.clientX - rect.left) * (WIN_W / rect.width),
        y: (e.clientY - rect.top) * (WIN_H / rect.height),
    };
}

// ── Scene System ───────────────────────────────────────
let currentScene = null;
const scenes = {};

function switchScene(name, opts = {}) {
    currentScene = scenes[name];
    if (currentScene.onEnter) currentScene.onEnter(opts);
}

// ══════════════════════════════════════════════════════
//  MENU SCENE
// ══════════════════════════════════════════════════════
scenes.menu = (() => {
    const gameCx = SIDEBAR_W + (WIN_W - SIDEBAR_W) / 2;
    const bwFull = 640, bwHalf = 308, bh = 56, bhBig = 64, gap = 14;
    let btnY = 310;

    const buttons = [];
    function addBtn(text, x, y, w, h, color, action, opts = {}) {
        buttons.push({ x, y, w, h, text, color, action, outline: opts.outline || false, subtitle: opts.subtitle || null });
    }

    // Row 1
    addBtn('🎱 원격 대결', gameCx - bwFull/2, btnY, bwHalf, bhBig, C_BTN_GREEN, 'online');
    addBtn('🤖 AI 대결', gameCx + bwFull/2 - bwHalf, btnY, bwHalf, bhBig, C_BTN_ORANGE, 'ai');
    btnY += bhBig + gap;

    // Row 2
    addBtn('로컬 2인 대결', gameCx - bwFull/2, btnY, bwFull, bh, C_BTN_GREEN, 'local');
    btnY += bh + gap;

    // Row 3
    addBtn('혼자 연습하기', gameCx - bwFull/2, btnY, bwFull, bh + 10, C_BTN_BLUE, 'practice',
        { subtitle: '자유롭게 연습할 수 있습니다' });
    btnY += bh + 10 + gap + 10;

    // Row 4
    addBtn('3구 쓰리쿠션', gameCx - bwFull/2, btnY, bwHalf, bh, C_BTN_DARK, '3cushion');
    addBtn('4구', gameCx + bwFull/2 - bwHalf, btnY, bwHalf, bh, C_BTN_DARK, '4ball');
    btnY += bh + gap;

    // Row 5
    addBtn('전적 보기', gameCx - bwFull/2, btnY, bwHalf, 46, null, 'records', { outline: true });
    addBtn('게임 방법', gameCx + bwFull/2 - bwHalf, btnY, bwHalf, 46, null, 'help', { outline: true });

    let hoverIdx = -1;
    let showDialog = null;
    let dialogBtns = [];

    return {
        onEnter() { hoverIdx = -1; showDialog = null; },
        handleEvent(type, e, pos) {
            if (showDialog) {
                if (type === 'click') {
                    for (const b of dialogBtns) {
                        if (pos.x >= b.x && pos.x <= b.x + b.w && pos.y >= b.y && pos.y <= b.y + b.h) {
                            playClick();
                            showDialog = null;
                        }
                    }
                }
                return;
            }
            if (type === 'mousemove') {
                hoverIdx = -1;
                for (let i = 0; i < buttons.length; i++) {
                    const b = buttons[i];
                    if (pos.x >= b.x && pos.x <= b.x + b.w && pos.y >= b.y && pos.y <= b.y + b.h) {
                        hoverIdx = i;
                        break;
                    }
                }
            }
            if (type === 'click' && hoverIdx >= 0) {
                playClick();
                resumeAudio();
                const action = buttons[hoverIdx].action;
                if (action === 'local') {
                    switchScene('nameInput', { mode: 'local' });
                } else if (action === 'practice') {
                    switchScene('game', { mode: 'practice' });
                } else if (action === '3cushion') {
                    switchScene('nameInput', { mode: '3cushion' });
                } else if (action === '4ball') {
                    switchScene('nameInput', { mode: '4ball' });
                } else if (action === 'ai') {
                    showDialog = { title: 'AI 모드 준비 중', msg: 'AI 대결 모드는 현재 개발 중입니다.\n조금만 기다려 주세요!' };
                } else if (action === 'online') {
                    showDialog = { title: '온라인 모드', msg: '온라인 대결은 서버가 필요합니다.\n로컬 2인 대결을 이용해 주세요!' };
                } else if (action === 'records') {
                    showDialog = { title: '전적 보기', msg: '로컬 게임의 전적은\n서버 연결 시 확인할 수 있습니다.' };
                } else if (action === 'help') {
                    showDialog = { title: '게임 방법', msg: '마우스로 조준, 드래그로 파워 조절\n화살표키로 스핀 조절\n자기 그룹 공을 모두 넣은 후 8번을 넣으면 승리!' };
                }
            }
        },
        update(dt) {},
        draw(ctx) {
            drawMenuScene(ctx, buttons, hoverIdx);
            if (showDialog) {
                dialogBtns = drawDialog(ctx, showDialog.title, showDialog.msg, ['확인']);
            }
        },
    };
})();

// ══════════════════════════════════════════════════════
//  NAME INPUT SCENE
// ══════════════════════════════════════════════════════
scenes.nameInput = (() => {
    let mode = 'local';
    let names = ['Player 1', 'Player 2'];
    let activeField = 0;
    let cursorBlink = 0;
    const hiddenInput = document.getElementById('hiddenInput');
    let composing = false;

    function syncFromInput() {
        const val = hiddenInput.value.slice(0, 12);
        names[activeField] = val;
    }

    function focusInput() {
        hiddenInput.value = names[activeField];
        hiddenInput.focus();
    }

    // IME 한국어 입력 지원
    hiddenInput.addEventListener('input', () => {
        if (!currentScene || currentScene !== scenes.nameInput) return;
        syncFromInput();
    });
    hiddenInput.addEventListener('compositionstart', () => { composing = true; });
    hiddenInput.addEventListener('compositionend', () => {
        composing = false;
        syncFromInput();
    });
    hiddenInput.addEventListener('keydown', (e) => {
        if (!currentScene || currentScene !== scenes.nameInput) return;
        if (e.key === 'Tab') {
            e.preventDefault();
            activeField = 1 - activeField;
            focusInput();
        } else if (e.key === 'Enter' && !composing) {
            e.preventDefault();
            playClick();
            hiddenInput.blur();
            if (mode === 'local') {
                switchScene('game', { mode: 'local', p1: names[0], p2: names[1] });
            } else {
                switchScene('game', { mode, p1: names[0], p2: names[1] });
            }
        }
    });

    function startGame() {
        playClick();
        hiddenInput.blur();
        if (mode === 'local') {
            switchScene('game', { mode: 'local', p1: names[0], p2: names[1] });
        } else {
            switchScene('game', { mode, p1: names[0], p2: names[1] });
        }
    }

    return {
        onEnter(opts = {}) {
            mode = opts.mode || 'local';
            names = ['Player 1', 'Player 2'];
            activeField = 0;
            cursorBlink = 0;
            setTimeout(() => focusInput(), 50);
        },
        handleEvent(type, e, pos) {
            if (type === 'click') {
                const cx = WIN_W / 2;
                if (pos.x > cx - 150 && pos.x < cx + 150 && pos.y > 360 && pos.y < 400) {
                    activeField = 0;
                    focusInput();
                } else if (pos.x > cx - 150 && pos.x < cx + 150 && pos.y > 440 && pos.y < 480) {
                    activeField = 1;
                    focusInput();
                } else if (pos.x > cx - 80 && pos.x < cx + 80 && pos.y > 520 && pos.y < 560) {
                    startGame();
                } else if (pos.x > cx - 80 && pos.x < cx + 80 && pos.y > 570 && pos.y < 610) {
                    playClick();
                    hiddenInput.blur();
                    switchScene('menu');
                }
            }
        },
        update(dt) { cursorBlink += dt; },
        draw(ctx) {
            ctx.fillStyle = '#0f0a08';
            ctx.fillRect(0, 0, WIN_W, WIN_H);

            const cx = WIN_W / 2;
            ctx.fillStyle = C_GOLD_LIGHT;
            ctx.font = 'bold 32px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('플레이어 이름 입력', cx, 310);

            for (let i = 0; i < 2; i++) {
                const y = 360 + i * 80;
                const isActive = i === activeField;
                ctx.fillStyle = isActive ? '#232323' : '#1a1a1a';
                ctx.strokeStyle = isActive ? C_GOLD_LIGHT : '#444';
                ctx.lineWidth = isActive ? 2 : 1;
                roundRect(ctx,cx - 150, y, 300, 40, 8);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = '#ccc';
                ctx.font = '18px Arial';
                ctx.textAlign = 'left';
                const txt = names[i] + (isActive && (cursorBlink % 1 < 0.5) ? '|' : '');
                ctx.fillText(txt, cx - 140, y + 26);

                ctx.fillStyle = C_TEXT_DIM;
                ctx.font = '14px Arial';
                ctx.textAlign = 'left';
                ctx.fillText(`P${i + 1}`, cx - 200, y + 26);
            }

            // Start button
            ctx.fillStyle = C_BTN_GREEN;
            roundRect(ctx,cx - 80, 520, 160, 40, 8);
            ctx.fill();
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 18px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('시작', cx, 546);

            // Cancel
            ctx.fillStyle = C_BTN_DARK;
            roundRect(ctx,cx - 80, 570, 160, 40, 8);
            ctx.fill();
            ctx.fillStyle = '#ccc';
            ctx.fillText('취소', cx, 596);
        },
    };
})();

// ══════════════════════════════════════════════════════
//  MAIN GAME SCENE (Local 2P / Practice / Carom)
// ══════════════════════════════════════════════════════
scenes.game = (() => {
    let mode = 'local'; // 'local' | 'practice' | '3cushion' | '4ball'
    let balls = [];
    let physics = null;
    let logic = null;       // GameLogic
    let caromLogic = null;  // CaromLogic
    let state = 'waiting';  // 'waiting' | 'moving' | 'hand' | 'over' | 'replay'
    let pocketFx = new PocketEffect();

    // Cue / aiming
    let cueAngle = 0;
    let targetAngle = 0;
    let spinX = 0, spinY = 0;
    let charging = false;
    let chargeStart = null;
    let power = 0;
    let mousePos = { x: 0, y: 0 };

    // Spin indicator position
    const SPIN_CX = 80;
    const SPIN_CY = WIN_H - 120;
    const SPIN_R = 28;
    const SPIN_STEP = 0.15;
    const SPIN_MAX = 0.85;
    let spinDragging = false;

    // Replay
    let replayFrames = [];
    let replayIdx = 0;
    let replayTimer = 0;
    let replayElapsed = 0;
    let recording = false;
    let recordFrames = [];
    let recordSkip = 0;
    const REPLAY_SPEED = 0.35;

    // Turn tracking
    let shotPocketed = [];
    let firstHitBall = null;
    let cuePocketed = false;
    let shotCount = 0;

    // Dialog
    let showDialog = null;
    let dialogBtns = [];

    // Leave button
    const LEAVE_BTN = { x: 15, y: WIN_H - 55, w: SIDEBAR_W - 30, h: 40 };

    function getCueBall() { return balls.find(b => b.number === 0); }
    function isCarom() { return mode === '3cushion' || mode === '4ball'; }

    function initBalls() {
        balls = [];
        if (isCarom()) {
            const setup = caromLogic.setupBalls();
            for (const [num, x, y, col] of setup) {
                const b = new Ball(num, x, y);
                b.color = col;
                balls.push(b);
            }
        } else {
            // cue ball
            balls.push(new Ball(0, GameLogic.CUE_START_X, GameLogic.CUE_START_Y));
            // rack
            const rack = logic.rackPositions();
            for (const [num, x, y] of rack) {
                balls.push(new Ball(num, x, y));
            }
        }
    }

    return {
        onEnter(opts = {}) {
            mode = opts.mode || 'local';
            const p1 = opts.p1 || 'Player 1';
            const p2 = opts.p2 || 'Player 2';

            if (isCarom()) {
                caromLogic = new CaromLogic(mode, p1, p2);
                logic = null;
                physics = new Physics(false);
            } else {
                logic = mode === 'practice' ? null : new GameLogic(p1, p2);
                caromLogic = null;
                physics = new Physics(true);
            }

            state = 'waiting';
            pocketFx = new PocketEffect();
            spinX = 0; spinY = 0;
            charging = false; power = 0;
            shotPocketed = [];
            firstHitBall = null;
            cuePocketed = false;
            shotCount = 0;
            showDialog = null;
            recording = false;
            replayFrames = [];

            initBalls();
            invalidateTableCache();
        },

        handleEvent(type, e, pos) {
            mousePos = pos;

            // Dialog handling
            if (showDialog) {
                if (type === 'click') {
                    for (const b of dialogBtns) {
                        if (pos.x >= b.x && pos.x <= b.x + b.w && pos.y >= b.y && pos.y <= b.y + b.h) {
                            playClick();
                            if (b.label === '새 게임') {
                                this.onEnter({ mode, p1: logic?.players[0]?.name || caromLogic?.names[0], p2: logic?.players[1]?.name || caromLogic?.names[1] });
                            } else if (b.label === '메뉴') {
                                switchScene('menu');
                            }
                            showDialog = null;
                        }
                    }
                }
                return;
            }

            // Leave button
            if (type === 'click') {
                const lb = LEAVE_BTN;
                if (pos.x >= lb.x && pos.x <= lb.x + lb.w && pos.y >= lb.y && pos.y <= lb.y + lb.h) {
                    playClick();
                    switchScene('menu');
                    return;
                }
            }

            // Replay skip
            if (state === 'replay') {
                if (type === 'keydown' && e.key === ' ') {
                    replayFrames = [];
                    state = 'moving'; // will transition to processEnd
                }
                return;
            }

            if (state === 'waiting') {
                const cue = getCueBall();
                if (!cue || cue.pocketed) return;

                // Spin indicator interaction
                if (type === 'mousedown' || type === 'mousemove' || type === 'mouseup') {
                    const sdx = pos.x - SPIN_CX;
                    const sdy = pos.y - SPIN_CY;
                    const sdist = Math.sqrt(sdx * sdx + sdy * sdy);

                    if (type === 'mousedown' && sdist <= SPIN_R + 6) {
                        if (e.button === 2) {
                            spinX = 0; spinY = 0;
                            return;
                        }
                        spinDragging = true;
                    }
                    if (spinDragging && (type === 'mousemove' || type === 'mousedown')) {
                        spinX = Math.max(-SPIN_MAX, Math.min(SPIN_MAX, sdx / (SPIN_R - 5)));
                        spinY = Math.max(-SPIN_MAX, Math.min(SPIN_MAX, sdy / (SPIN_R - 5)));
                        return;
                    }
                    if (type === 'mouseup') spinDragging = false;
                }

                // Keyboard spin
                if (type === 'keydown') {
                    if (e.key === 'ArrowLeft')  { spinX = Math.max(-SPIN_MAX, spinX - SPIN_STEP); return; }
                    if (e.key === 'ArrowRight') { spinX = Math.min(SPIN_MAX, spinX + SPIN_STEP); return; }
                    if (e.key === 'ArrowUp')    { spinY = Math.max(-SPIN_MAX, spinY - SPIN_STEP); return; }
                    if (e.key === 'ArrowDown')  { spinY = Math.min(SPIN_MAX, spinY + SPIN_STEP); return; }
                    if (e.key === 'Escape' && charging) { charging = false; power = 0; return; }
                }

                // Aiming & shooting
                if (type === 'mousemove' && !charging) {
                    targetAngle = Math.atan2(pos.y - cue.y, pos.x - cue.x);
                }

                if (type === 'mousedown' && e.button === 0 && !spinDragging) {
                    // check if clicking on table area
                    if (pos.x > SIDEBAR_W) {
                        charging = true;
                        chargeStart = { x: pos.x, y: pos.y };
                    }
                }

                if (type === 'mousemove' && charging) {
                    const dx = pos.x - chargeStart.x;
                    const dy = pos.y - chargeStart.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    power = Math.min(1.0, dist / 120);
                }

                if (type === 'mouseup' && charging) {
                    charging = false;
                    if (power > 0.02) {
                        shoot(cue);
                    }
                    power = 0;
                }

                // Practice: right-click to place cue ball
                if (mode === 'practice' && type === 'mousedown' && e.button === 2) {
                    if (pos.x > TABLE_X + CUSHION_SIZE && pos.x < TABLE_X + TABLE_W - CUSHION_SIZE &&
                        pos.y > TABLE_Y + CUSHION_SIZE && pos.y < TABLE_Y + TABLE_H - CUSHION_SIZE) {
                        cue.place(pos.x, pos.y);
                    }
                }
            }

            if (state === 'hand') {
                if (type === 'click') {
                    const bx = pos.x, by = pos.y;
                    if (bx > TABLE_X + CUSHION_SIZE + BALL_RADIUS &&
                        bx < TABLE_X + TABLE_W - CUSHION_SIZE - BALL_RADIUS &&
                        by > TABLE_Y + CUSHION_SIZE + BALL_RADIUS &&
                        by < TABLE_Y + TABLE_H - CUSHION_SIZE - BALL_RADIUS) {
                        // check no overlap with other balls
                        let ok = true;
                        for (const b of balls) {
                            if (b.pocketed || b.number === 0) continue;
                            const dx = b.x - bx, dy = b.y - by;
                            if (Math.sqrt(dx * dx + dy * dy) < BALL_RADIUS * 2 + 2) {
                                ok = false;
                                break;
                            }
                        }
                        if (ok) {
                            const cue = getCueBall();
                            cue.place(bx, by);
                            state = 'waiting';
                        }
                    }
                }
            }
        },

        update(dt) {
            // Smooth cue angle
            if (state === 'waiting') {
                let diff = targetAngle - cueAngle;
                while (diff > Math.PI) diff -= Math.PI * 2;
                while (diff < -Math.PI) diff += Math.PI * 2;
                const maxSpeed = 0.5;
                diff = Math.max(-maxSpeed, Math.min(maxSpeed, diff * 0.35));
                cueAngle += diff;
            }

            // Replay playback
            if (state === 'replay') {
                replayElapsed += dt;
                replayTimer += dt * REPLAY_SPEED * 60;
                if (replayTimer >= replayFrames.length - 1) {
                    // replay done
                    restoreBallsFromReplay(replayFrames[replayFrames.length - 1]);
                    replayFrames = [];
                    state = 'moving'; // will immediately process end since balls are stopped
                } else {
                    // interpolate frame
                    const fi = replayTimer | 0;
                    const frac = replayTimer - fi;
                    const frame = replayFrames[Math.min(fi, replayFrames.length - 1)];
                    restoreBallsFromReplay(frame);
                }
                pocketFx.update(dt);
                return;
            }

            // Physics
            if (state === 'moving') {
                physics.collisionEvents = [];
                const pocketed = physics.step(balls, dt);

                // Sound effects
                for (const ev of physics.collisionEvents) {
                    if (ev.kind === 'ball_hit') playBallHit(ev.speed);
                    else if (ev.kind === 'wall_hit') playWallHit(ev.speed);
                }

                // Track pocketed
                for (const num of pocketed) {
                    if (!shotPocketed.includes(num)) shotPocketed.push(num);
                    if (num === 0) cuePocketed = true;
                    const b = balls.find(b2 => b2.number === num);
                    if (b) {
                        playPocket();
                        pocketFx.spawn(b.pocketPos[0], b.pocketPos[1], BALL_COLORS[num] || [200,200,200]);
                    }
                }

                // Track first hit (for foul detection)
                if (firstHitBall === null && physics.ballContacts.size > 0) {
                    const cue = getCueBall();
                    for (const b of balls) {
                        if (b.number !== 0 && physics.ballContacts.has(b.number)) {
                            firstHitBall = b;
                            break;
                        }
                    }
                }

                // Record replay frames
                if (recording) {
                    recordSkip++;
                    if (recordSkip >= 2) {
                        recordSkip = 0;
                        recordFrames.push(balls.map(b => ({
                            n: b.number, x: b.x, y: b.y,
                            rx: b.rotX, ry: b.rotY, p: b.pocketed,
                        })));
                        if (recordFrames.length > 1200) recordFrames.shift();
                    }
                }

                // Check if all balls stopped
                const anyMoving = balls.some(b => b.isMoving);
                if (!anyMoving) {
                    recording = false;

                    // Check if should replay (2+ balls pocketed)
                    if (shotPocketed.length >= 2 && recordFrames.length > 5) {
                        replayFrames = recordFrames.slice();
                        replayTimer = 0;
                        replayElapsed = 0;
                        state = 'replay';
                    } else {
                        processEndOfShot();
                    }
                }
            }

            pocketFx.update(dt);
        },

        draw(ctx) {
            // Background
            ctx.fillStyle = '#0f0a08';
            ctx.fillRect(0, 0, WIN_W, WIN_H);

            // Table
            drawTable(ctx, isCarom());

            // Guide line (waiting only)
            if (state === 'waiting') {
                const cue = getCueBall();
                if (cue && !cue.pocketed) {
                    const ray = castRay(cue.x, cue.y, cueAngle + Math.PI, balls);
                    drawGuideLine(ctx, cue.x, cue.y, ray);
                }
            }

            // Balls
            drawBalls(ctx, balls);
            pocketFx.draw(ctx);

            // Cue stick
            if (state === 'waiting') {
                const cue = getCueBall();
                if (cue && !cue.pocketed) {
                    drawCue(ctx, cue.x, cue.y, cueAngle + Math.PI, power);
                    if (charging) {
                        drawPowerBar(ctx, power, SIDEBAR_W + (WIN_W - SIDEBAR_W) / 2, TABLE_Y + TABLE_H + 70);
                    }
                }
            }

            // Hand mode - ghost cue ball
            if (state === 'hand') {
                ctx.save();
                ctx.globalAlpha = 0.4;
                const ghost = new Ball(0, mousePos.x, mousePos.y);
                drawBall(ctx, ghost);
                ctx.restore();
            }

            // Spin indicator (waiting only)
            if (state === 'waiting') {
                drawSpinIndicator(ctx, spinX, spinY, SPIN_CX, SPIN_CY);
            }

            // Sidebar
            if (isCarom()) {
                drawCaromSidebar(ctx);
            } else if (mode === 'practice') {
                drawPracticeSidebar(ctx);
            } else {
                drawSidebar(ctx, logic.players, logic.current);
            }

            // Turn header
            drawTurnHeaderText(ctx);

            // Ball status (non-carom)
            if (!isCarom()) {
                drawBallStatusBar(ctx, balls,
                    logic?.players[0] || null,
                    logic?.players[1] || null);
            }

            // Replay overlay
            if (state === 'replay' && replayFrames.length > 0) {
                drawReplayOverlay(ctx, replayTimer / replayFrames.length, replayElapsed);
            }

            // Leave button
            drawLeaveButton(ctx);

            // Dialog
            if (showDialog) {
                dialogBtns = drawDialog(ctx, showDialog.title, showDialog.msg, showDialog.buttons || ['새 게임', '메뉴']);
            }
        },
    };

    function shoot(cue) {
        const finalPower = (power + 0.45 * power * power * power) * MAX_POWER;
        cue.shoot(cueAngle + Math.PI, finalPower, spinX, spinY);

        playCueShoot();
        state = 'moving';
        shotPocketed = [];
        firstHitBall = null;
        cuePocketed = false;
        shotCount++;

        if (isCarom()) {
            physics.resetTracking();
        }

        // Start recording
        recording = true;
        recordFrames = [];
        recordSkip = 0;
    }

    function processEndOfShot() {
        if (mode === 'practice') {
            // auto-reset cue ball if pocketed
            const cue = getCueBall();
            if (cue.pocketed) {
                cue.place(GameLogic.CUE_START_X, GameLogic.CUE_START_Y);
            }
            state = 'waiting';
            return;
        }

        if (isCarom()) {
            const cueBallNum = caromLogic.currentCue;
            const result = caromLogic.evaluate(physics.cushionHits, physics.ballContacts, cueBallNum);
            if (result === CAROM_RESULT.WIN) {
                playWin();
                showDialog = {
                    title: '게임 종료',
                    msg: `${caromLogic.names[caromLogic.current]} 승리!\n최종 스코어: ${caromLogic.scores[0]} - ${caromLogic.scores[1]}`,
                    buttons: ['새 게임', '메뉴'],
                };
                state = 'over';
            } else {
                state = 'waiting';
            }
            return;
        }

        // 8-ball logic
        const fhGroup = firstHitBall ? firstHitBall.group : null;
        const result = logic.onShotEnd(shotPocketed, fhGroup, cuePocketed);

        if (result === TURN.FOUL) {
            playFoul();
            const cue = getCueBall();
            if (cuePocketed) {
                cue.pocketed = false;
                state = 'hand';
            } else {
                state = 'hand';
            }
        } else if (result === TURN.WIN || result === TURN.LOSE) {
            playWin();
            showDialog = {
                title: '게임 종료',
                msg: logic.message,
                buttons: ['새 게임', '메뉴'],
            };
            state = 'over';
        } else {
            state = 'waiting';
        }
    }

    function restoreBallsFromReplay(frame) {
        if (!frame) return;
        for (const f of frame) {
            const b = balls.find(b2 => b2.number === f.n);
            if (b) {
                b.x = f.x; b.y = f.y;
                b.rotX = f.rx; b.rotY = f.ry;
                b.pocketed = f.p;
            }
        }
    }

    function drawTurnHeaderText(ctx) {
        let text = '';
        let highlight = true;

        if (state === 'hand') {
            text = '볼인핸드 — 테이블을 클릭해 큐볼을 배치하세요';
        } else if (state === 'moving' || state === 'replay') {
            text = '공이 이동 중...';
            highlight = false;
        } else if (mode === 'practice') {
            text = `연습 모드 — 샷: ${shotCount}`;
        } else if (isCarom()) {
            const name = caromLogic.names[caromLogic.current];
            text = `${name}의 차례`;
        } else if (logic) {
            text = logic.message;
        }

        drawTurnHeader(ctx, text, highlight);
    }

    function drawPracticeSidebar(ctx) {
        ctx.fillStyle = '#1c202d';
        ctx.fillRect(0, 0, SIDEBAR_W, WIN_H);
        ctx.fillStyle = '#303646';
        ctx.fillRect(SIDEBAR_W - 1, 0, 1, WIN_H);

        ctx.fillStyle = C_GOLD_LIGHT;
        ctx.font = 'bold 24px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('🎱 연습 모드', SIDEBAR_W / 2, 50);

        ctx.fillStyle = '#303646';
        ctx.fillRect(20, 70, SIDEBAR_W - 40, 1);

        ctx.fillStyle = C_TEXT_DIM;
        ctx.font = '18px Arial';
        ctx.fillText(`샷: ${shotCount}`, SIDEBAR_W / 2, 110);

        const pocketedCnt = balls.filter(b => b.pocketed && b.number !== 0).length;
        ctx.fillText(`넣은 공: ${pocketedCnt}개`, SIDEBAR_W / 2, 145);

        ctx.fillStyle = '#555';
        ctx.font = '14px Arial';
        ctx.fillText('우클릭: 큐볼 재배치', SIDEBAR_W / 2, 190);
    }

    function drawCaromSidebar(ctx) {
        ctx.fillStyle = '#1c202d';
        ctx.fillRect(0, 0, SIDEBAR_W, WIN_H);
        ctx.fillStyle = '#303646';
        ctx.fillRect(SIDEBAR_W - 1, 0, 1, WIN_H);

        const modeLabel = mode === '3cushion' ? '쓰리쿠션' : '4구';
        ctx.fillStyle = C_GOLD_LIGHT;
        ctx.font = 'bold 24px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(`🎱 ${modeLabel}`, SIDEBAR_W / 2, 50);

        ctx.fillStyle = '#303646';
        ctx.fillRect(20, 70, SIDEBAR_W - 40, 1);

        ctx.fillStyle = C_TEXT_DIM;
        ctx.font = '16px Arial';
        ctx.fillText(`목표: ${caromLogic.targetScore}점`, SIDEBAR_W / 2, 100);

        for (let i = 0; i < 2; i++) {
            const py = 130 + i * 140;
            const isActive = i === caromLogic.current;

            ctx.fillStyle = isActive ? '#262c3c' : 'rgba(255,255,255,0.03)';
            roundRect(ctx,15, py, SIDEBAR_W - 30, 120, 8);
            ctx.fill();
            if (isActive) {
                ctx.strokeStyle = C_GOLD_LIGHT;
                ctx.lineWidth = 2;
                ctx.stroke();
            }

            // ball color indicator
            const ballColor = i === 0 ? [248, 248, 248] : [240, 210, 50];
            ctx.fillStyle = `rgb(${ballColor[0]},${ballColor[1]},${ballColor[2]})`;
            ctx.beginPath();
            ctx.arc(45, py + 35, 14, 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = isActive ? '#e6e6e6' : '#8c8c8c';
            ctx.font = 'bold 20px Arial';
            ctx.textAlign = 'left';
            ctx.fillText(caromLogic.names[i], 70, py + 40);

            // score
            ctx.fillStyle = C_GOLD_LIGHT;
            ctx.font = 'bold 48px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(String(caromLogic.scores[i]), SIDEBAR_W / 2, py + 95);

            // progress bar
            const prog = caromLogic.scores[i] / caromLogic.targetScore;
            ctx.fillStyle = 'rgba(255,255,255,0.1)';
            ctx.fillRect(30, py + 105, SIDEBAR_W - 60, 4);
            ctx.fillStyle = C_GOLD_LIGHT;
            ctx.fillRect(30, py + 105, (SIDEBAR_W - 60) * prog, 4);
        }
    }

    function drawLeaveButton(ctx) {
        const lb = LEAVE_BTN;
        ctx.fillStyle = '#c82828';
        roundRect(ctx,lb.x, lb.y, lb.w, lb.h, 8);
        ctx.fill();
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('나가기', lb.x + lb.w / 2, lb.y + lb.h / 2 + 5);
    }
})();

// ── Input Handling ─────────────────────────────────────
canvas.addEventListener('contextmenu', e => e.preventDefault());

['mousedown', 'mouseup', 'mousemove', 'click'].forEach(type => {
    canvas.addEventListener(type, e => {
        const pos = getMousePos(e);
        if (currentScene?.handleEvent) currentScene.handleEvent(type, e, pos);
    });
});

document.addEventListener('keydown', e => {
    if (currentScene?.handleEvent) {
        currentScene.handleEvent('keydown', e, mouseGlobal);
    }
});

let mouseGlobal = { x: 0, y: 0 };
canvas.addEventListener('mousemove', e => { mouseGlobal = getMousePos(e); });

// ── Game Loop ──────────────────────────────────────────
let lastTime = performance.now();

function gameLoop(time) {
    let dt = (time - lastTime) / 1000;
    lastTime = time;

    // cap dt to avoid spiral of death
    if (dt > 0.05) dt = 0.05;

    if (currentScene) {
        currentScene.update(dt);
        currentScene.draw(ctx);
    }

    requestAnimationFrame(gameLoop);
}

// ── Init ───────────────────────────────────────────────
initSound();
switchScene('menu');
requestAnimationFrame(gameLoop);
