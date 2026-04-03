import {
    WIN_W, WIN_H, SIDEBAR_W, TABLE_X, TABLE_Y, TABLE_W, TABLE_H,
    CUSHION_SIZE, POCKET_RADIUS, POCKETS, BALL_RADIUS, BALL_COLORS,
    C_BG, C_WOOD, C_WOOD_LIGHT, C_FELT, C_FELT_DARK, C_POCKET,
    C_GOLD, C_GOLD_LIGHT, C_TEXT, C_TEXT_DIM, C_WHITE, C_BLACK,
    C_SIDEBAR_BG, C_SIDEBAR_LIGHT, C_SIDEBAR_BORDER,
    C_BTN_GREEN, C_BTN_ORANGE, C_BTN_BLUE, C_BTN_DARK, C_ACCENT_BLUE,
    rgb, rgba
} from './config.js';

// ── Table Cache ────────────────────────────────────────
let _tableCache = null;

export function invalidateTableCache() { _tableCache = null; }

function drawTableToCache() {
    const c = document.createElement('canvas');
    c.width = WIN_W; c.height = WIN_H;
    const ctx = c.getContext('2d');

    // Wood frame
    const fx = TABLE_X - 20;
    const fy = TABLE_Y - 20;
    const fw = TABLE_W + 40;
    const fh = TABLE_H + 40;
    ctx.fillStyle = C_WOOD;
    roundRect(ctx, fx, fy, fw, fh, 12);
    ctx.fill();
    // lighter inner
    ctx.fillStyle = C_WOOD_LIGHT;
    roundRect(ctx, fx + 4, fy + 4, fw - 8, fh - 8, 10);
    ctx.fill();

    // Felt
    ctx.fillStyle = C_FELT;
    ctx.fillRect(TABLE_X, TABLE_Y, TABLE_W, TABLE_H);
    // subtle texture lines
    ctx.strokeStyle = C_FELT_DARK;
    ctx.lineWidth = 0.5;
    ctx.globalAlpha = 0.3;
    for (let y = TABLE_Y + 8; y < TABLE_Y + TABLE_H; y += 12) {
        ctx.beginPath();
        ctx.moveTo(TABLE_X, y);
        ctx.lineTo(TABLE_X + TABLE_W, y);
        ctx.stroke();
    }
    ctx.globalAlpha = 1.0;

    // Cushions (darker border)
    ctx.fillStyle = '#0f5a16';
    // top
    ctx.fillRect(TABLE_X + POCKET_RADIUS + 10, TABLE_Y, TABLE_W / 2 - POCKET_RADIUS * 2 - 10, CUSHION_SIZE);
    ctx.fillRect(TABLE_X + TABLE_W / 2 + POCKET_RADIUS + 10, TABLE_Y, TABLE_W / 2 - POCKET_RADIUS * 2 - 10, CUSHION_SIZE);
    // bottom
    ctx.fillRect(TABLE_X + POCKET_RADIUS + 10, TABLE_Y + TABLE_H - CUSHION_SIZE, TABLE_W / 2 - POCKET_RADIUS * 2 - 10, CUSHION_SIZE);
    ctx.fillRect(TABLE_X + TABLE_W / 2 + POCKET_RADIUS + 10, TABLE_Y + TABLE_H - CUSHION_SIZE, TABLE_W / 2 - POCKET_RADIUS * 2 - 10, CUSHION_SIZE);
    // left
    ctx.fillRect(TABLE_X, TABLE_Y + POCKET_RADIUS + 10, CUSHION_SIZE, TABLE_H - POCKET_RADIUS * 2 - 20);
    // right
    ctx.fillRect(TABLE_X + TABLE_W - CUSHION_SIZE, TABLE_Y + POCKET_RADIUS + 10, CUSHION_SIZE, TABLE_H - POCKET_RADIUS * 2 - 20);

    // Diamond markers on rails
    const diamonds = [];
    for (let i = 1; i < 4; i++) {
        const x = TABLE_X + (TABLE_W / 4) * i;
        diamonds.push([x, TABLE_Y - 8]);
        diamonds.push([x, TABLE_Y + TABLE_H + 8]);
    }
    for (let i = 1; i < 3; i++) {
        const y = TABLE_Y + (TABLE_H / 3) * i;
        diamonds.push([TABLE_X - 8, y]);
        diamonds.push([TABLE_X + TABLE_W + 8, y]);
    }
    ctx.fillStyle = C_GOLD;
    for (const [dx, dy] of diamonds) {
        ctx.beginPath();
        ctx.save();
        ctx.translate(dx, dy);
        ctx.rotate(Math.PI / 4);
        ctx.fillRect(-3, -3, 6, 6);
        ctx.restore();
    }

    // Center & head spots
    ctx.fillStyle = C_GOLD;
    ctx.globalAlpha = 0.4;
    ctx.beginPath();
    ctx.arc(TABLE_X + TABLE_W * 0.25, TABLE_Y + TABLE_H * 0.5, 3, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1.0;

    // Pockets
    for (const [px, py] of POCKETS) {
        // gold rim
        ctx.beginPath();
        ctx.arc(px, py, POCKET_RADIUS + 6, 0, Math.PI * 2);
        ctx.fillStyle = '#8b6914';
        ctx.fill();
        ctx.beginPath();
        ctx.arc(px, py, POCKET_RADIUS + 3, 0, Math.PI * 2);
        ctx.fillStyle = C_GOLD;
        ctx.fill();
        // black hole
        ctx.beginPath();
        ctx.arc(px, py, POCKET_RADIUS, 0, Math.PI * 2);
        ctx.fillStyle = C_POCKET;
        ctx.fill();
        // inner shadow gradient
        const grad = ctx.createRadialGradient(px, py, POCKET_RADIUS * 0.3, px, py, POCKET_RADIUS);
        grad.addColorStop(0, 'rgba(0,0,0,0.9)');
        grad.addColorStop(1, 'rgba(20,20,20,0.5)');
        ctx.fillStyle = grad;
        ctx.fill();
    }

    _tableCache = c;
}

export function drawTable(ctx, pocketless = false) {
    if (!_tableCache || pocketless) {
        if (pocketless) {
            drawPocketlessTable(ctx);
            return;
        }
        drawTableToCache();
    }
    ctx.drawImage(_tableCache, 0, 0);
}

function drawPocketlessTable(ctx) {
    // Wood frame
    const fx = TABLE_X - 20;
    const fy = TABLE_Y - 20;
    ctx.fillStyle = C_WOOD;
    roundRect(ctx, fx, fy, TABLE_W + 40, TABLE_H + 40, 12);
    ctx.fill();
    ctx.fillStyle = C_WOOD_LIGHT;
    roundRect(ctx, fx + 4, fy + 4, TABLE_W + 32, TABLE_H + 32, 10);
    ctx.fill();
    // Felt
    ctx.fillStyle = C_FELT;
    ctx.fillRect(TABLE_X, TABLE_Y, TABLE_W, TABLE_H);
    // Cushion borders all around
    ctx.fillStyle = '#0f5a16';
    ctx.fillRect(TABLE_X, TABLE_Y, TABLE_W, CUSHION_SIZE);
    ctx.fillRect(TABLE_X, TABLE_Y + TABLE_H - CUSHION_SIZE, TABLE_W, CUSHION_SIZE);
    ctx.fillRect(TABLE_X, TABLE_Y, CUSHION_SIZE, TABLE_H);
    ctx.fillRect(TABLE_X + TABLE_W - CUSHION_SIZE, TABLE_Y, CUSHION_SIZE, TABLE_H);
    // Diamonds
    ctx.fillStyle = C_GOLD;
    for (let i = 1; i < 4; i++) {
        const x = TABLE_X + (TABLE_W / 4) * i;
        drawDiamond(ctx, x, TABLE_Y - 8);
        drawDiamond(ctx, x, TABLE_Y + TABLE_H + 8);
    }
    for (let i = 1; i < 3; i++) {
        const y = TABLE_Y + (TABLE_H / 3) * i;
        drawDiamond(ctx, TABLE_X - 8, y);
        drawDiamond(ctx, TABLE_X + TABLE_W + 8, y);
    }
}

function drawDiamond(ctx, x, y) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(Math.PI / 4);
    ctx.fillRect(-3, -3, 6, 6);
    ctx.restore();
}

// ── Pixel-level 3D Ball Renderer ───────────────────────
// Offscreen canvas for per-pixel ball rendering
const _ballCanvas = document.createElement('canvas');
const _ballCtx = _ballCanvas.getContext('2d');
const _RS = 2; // supersample factor
const _ballSize = (BALL_RADIUS * 2 + 2) * _RS;
_ballCanvas.width = _ballSize;
_ballCanvas.height = _ballSize;

// Light direction (normalized) — upper-left-front
const LX = -0.4, LY = -0.55, LZ = 0.75;
const LL = Math.sqrt(LX*LX + LY*LY + LZ*LZ);
const LIGHT = [LX/LL, LY/LL, LZ/LL];

export function drawBall(ctx, ball) {
    if (ball.pocketed) return;
    const { x, y, number, radius } = ball;
    const color = ball.color || BALL_COLORS[number] || [200, 200, 200];
    const isStripe = number >= 9 && number <= 15;
    const isCue = number === 0;
    const isEight = number === 8;
    const rx = ball.rotX || 0;
    const ry = ball.rotY || 0;

    // shadow
    ctx.save();
    ctx.globalAlpha = 0.3;
    ctx.fillStyle = '#000';
    ctx.beginPath();
    ctx.ellipse(x + 3, y + 5, radius * 0.9, radius * 0.45, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Precompute inverse rotation matrix (transpose of forward rotation)
    // Forward: Ry * Rx * point.  Inverse: Rx^T * Ry^T * point
    const cx1 = Math.cos(-rx), sx1 = Math.sin(-rx);
    const cy1 = Math.cos(-ry), sy1 = Math.sin(-ry);

    const R = radius * _RS;
    const size = R * 2 + 2;
    const imgData = _ballCtx.createImageData(size | 0, size | 0);
    const data = imgData.data;
    const w = imgData.width;

    const [cr, cg, cb] = color;

    for (let py = 0; py < w; py++) {
        for (let px = 0; px < w; px++) {
            const sx = (px - w / 2) / R;  // -1..1 in sphere space
            const sy = (py - w / 2) / R;
            const r2 = sx * sx + sy * sy;
            if (r2 > 1.0) continue;

            const sz = Math.sqrt(1.0 - r2);  // surface normal z

            // Normal in world space = (sx, sy, sz)
            // Apply inverse rotation to find texture coordinate
            // First inverse Ry
            let tx = sx * cy1 + sz * sy1;
            let tz = -sx * sy1 + sz * cy1;
            // Then inverse Rx
            let ty = sy * cx1 - tz * sx1;
            let tz2 = sy * sx1 + tz * cx1;

            // Texture coordinate: (tx, ty, tz2) is the original sphere point
            // Latitude = asin(ty)  (-pi/2 to pi/2)
            const lat = Math.asin(Math.max(-1, Math.min(1, ty)));

            // Determine base color at this texel
            let baseR, baseG, baseB;

            if (isCue) {
                baseR = 245; baseG = 245; baseB = 245;
            } else if (isStripe) {
                // Stripe: white ball with colored band at equator (|lat| < 35°)
                const bandAngle = 0.61; // ~35 degrees in radians
                if (Math.abs(lat) < bandAngle) {
                    baseR = cr; baseG = cg; baseB = cb;
                } else {
                    baseR = 240; baseG = 240; baseB = 240;
                }
            } else {
                // Solid ball: entire surface is ball color
                baseR = cr; baseG = cg; baseB = cb;
            }

            // Number circle check: distance from "north pole" (0, 1, 0) in texture space
            if (!isCue && !ball.color) {
                const numDist = Math.sqrt(tx * tx + (ty - 1) * (ty - 1) + tz2 * tz2);
                if (numDist < 0.55) {
                    // White circle background
                    baseR = 250; baseG = 250; baseB = 250;
                    if (numDist < 0.35) {
                        // Dark number area (simplified — just a dark dot for the digit center)
                        baseR = 30; baseG = 30; baseB = 30;
                    }
                }
            }

            // Phong lighting
            const ndotl = sx * LIGHT[0] + sy * LIGHT[1] + sz * LIGHT[2];
            const diffuse = Math.max(0, ndotl);

            // Specular: reflect light off surface
            const refX = 2 * ndotl * sx - LIGHT[0];
            const refY = 2 * ndotl * sy - LIGHT[1];
            const refZ = 2 * ndotl * sz - LIGHT[2];
            const spec = Math.pow(Math.max(0, refZ), 30); // view = (0,0,1)

            // Fresnel-like rim darkening
            const fresnel = 1.0 - Math.pow(1.0 - sz, 2.5) * 0.5;

            const ambient = 0.25;
            const light = Math.min(1.3, ambient + diffuse * 0.75);
            const finalR = Math.min(255, (baseR * light * fresnel + spec * 200) | 0);
            const finalG = Math.min(255, (baseG * light * fresnel + spec * 200) | 0);
            const finalB = Math.min(255, (baseB * light * fresnel + spec * 200) | 0);

            // Edge anti-aliasing
            const edgeDist = Math.sqrt(r2);
            let alpha = 255;
            if (edgeDist > 0.92) {
                alpha = Math.max(0, ((1.0 - edgeDist) / 0.08) * 255) | 0;
            }

            const idx = (py * w + px) * 4;
            data[idx]     = finalR;
            data[idx + 1] = finalG;
            data[idx + 2] = finalB;
            data[idx + 3] = alpha;
        }
    }

    _ballCtx.putImageData(imgData, 0, 0);

    // Draw number text onto the ball canvas (projected)
    if (!isCue && !ball.color) {
        // Find where north pole projects to screen
        const npSy = 0 * cx1 - 1 * sx1;  // after inv Rx, the z component
        const npY = 0 * Math.cos(rx) - (-1) * Math.sin(rx);  // not needed, recalc properly

        // Forward rotate (0,1,0) to find screen position
        // Rx: y'=cos(rx)*1, z'=sin(rx)*1
        const npYr = Math.cos(rx);
        const npZr = Math.sin(rx);
        // Ry: x'=sin(ry)*npZr, z''=cos(ry)*npZr
        const npXf = Math.sin(ry) * npZr;
        const npYf = npYr;
        const npZf = Math.cos(ry) * npZr;

        if (npZf > 0.15) {
            const scale = 0.4 + npZf * 0.6;
            const numPx = (w / 2 + npXf * R * 0.65) | 0;
            const numPy = (w / 2 - npYf * R * 0.65) | 0;
            const fontSize = Math.max(7, ((radius - 3) * _RS * scale)) | 0;

            // Lighting at number position
            const nsx = npXf, nsy = -npYf, nsz = npZf;
            const nLight = Math.min(1.2, 0.3 + Math.max(0, nsx*LIGHT[0]+nsy*LIGHT[1]+nsz*LIGHT[2]) * 0.7);

            _ballCtx.fillStyle = `rgba(255,255,255,${Math.min(1, scale * 1.2)})`;
            _ballCtx.beginPath();
            _ballCtx.arc(numPx, numPy, radius * 0.42 * _RS * scale, 0, Math.PI * 2);
            _ballCtx.fill();

            const brightness = Math.min(60, (nLight * 40) | 0);
            _ballCtx.fillStyle = `rgb(${brightness},${brightness},${brightness})`;
            _ballCtx.font = `bold ${fontSize}px Arial`;
            _ballCtx.textAlign = 'center';
            _ballCtx.textBaseline = 'middle';
            _ballCtx.fillText(String(number), numPx, numPy + 1);
        }
    }

    // Blit the ball to main canvas (downscale from supersample)
    ctx.drawImage(
        _ballCanvas,
        0, 0, w, w,
        x - radius - 0.5, y - radius - 0.5,
        radius * 2 + 1, radius * 2 + 1
    );
}

export function drawBalls(ctx, balls) {
    for (const b of balls) drawBall(ctx, b);
}

// ── Guide Line ─────────────────────────────────────────
export function drawGuideLine(ctx, startX, startY, ray) {
    if (!ray) return;
    const { endX, endY, hitBall, targetDir, reflX, reflY } = ray;

    // main aim line (white, fading)
    const grad = ctx.createLinearGradient(startX, startY, endX, endY);
    grad.addColorStop(0, 'rgba(255,255,255,0.6)');
    grad.addColorStop(1, 'rgba(255,255,255,0.1)');
    ctx.strokeStyle = grad;
    ctx.lineWidth = 1.5;
    ctx.setLineDash([8, 6]);
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.stroke();
    ctx.setLineDash([]);

    if (hitBall && targetDir) {
        // ghost cue ball
        ctx.strokeStyle = 'rgba(255,255,255,0.25)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(endX, endY, BALL_RADIUS, 0, Math.PI * 2);
        ctx.stroke();

        // target ball direction (yellow)
        ctx.strokeStyle = 'rgba(255, 220, 50, 0.5)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([6, 4]);
        ctx.beginPath();
        ctx.moveTo(hitBall.x, hitBall.y);
        ctx.lineTo(hitBall.x + targetDir.x * 120, hitBall.y + targetDir.y * 120);
        ctx.stroke();
        ctx.setLineDash([]);

        // cue reflection (sky blue)
        ctx.strokeStyle = 'rgba(100, 200, 255, 0.3)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(endX, endY);
        ctx.lineTo(endX + reflX * 80, endY + reflY * 80);
        ctx.stroke();
        ctx.setLineDash([]);
    } else {
        // end circle (no hit)
        ctx.strokeStyle = 'rgba(255,255,255,0.2)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(endX, endY, BALL_RADIUS, 0, Math.PI * 2);
        ctx.stroke();
    }
}

// ── Cue Stick ──────────────────────────────────────────
export function drawCue(ctx, ballX, ballY, angle, power) {
    const CUE_LENGTH = 280;
    const gap = BALL_RADIUS + 5 + power * 45;

    ctx.save();
    ctx.translate(ballX, ballY);
    ctx.rotate(angle);

    // cue stick body (3 sections)
    const startX = -gap - CUE_LENGTH;
    const tipW = 3;
    const buttW = 9;

    // butt (dark)
    ctx.fillStyle = '#783c1e';
    ctx.beginPath();
    ctx.moveTo(startX, -buttW / 2);
    ctx.lineTo(startX + CUE_LENGTH * 0.35, -6 / 2);
    ctx.lineTo(startX + CUE_LENGTH * 0.35, 6 / 2);
    ctx.lineTo(startX, buttW / 2);
    ctx.closePath();
    ctx.fill();

    // body (wood)
    ctx.fillStyle = '#be8c37';
    ctx.beginPath();
    ctx.moveTo(startX + CUE_LENGTH * 0.35, -6 / 2);
    ctx.lineTo(startX + CUE_LENGTH * 0.85, -4 / 2);
    ctx.lineTo(startX + CUE_LENGTH * 0.85, 4 / 2);
    ctx.lineTo(startX + CUE_LENGTH * 0.35, 6 / 2);
    ctx.closePath();
    ctx.fill();

    // tip (light)
    ctx.fillStyle = '#dcd2be';
    ctx.beginPath();
    ctx.moveTo(startX + CUE_LENGTH * 0.85, -4 / 2);
    ctx.lineTo(startX + CUE_LENGTH, -tipW / 2);
    ctx.lineTo(startX + CUE_LENGTH, tipW / 2);
    ctx.lineTo(startX + CUE_LENGTH * 0.85, 4 / 2);
    ctx.closePath();
    ctx.fill();

    // white wrap accent
    ctx.fillStyle = 'rgba(255,255,255,0.5)';
    ctx.fillRect(startX + CUE_LENGTH * 0.32, -3, CUE_LENGTH * 0.06, 6);

    ctx.restore();
}

// ── Power Bar ──────────────────────────────────────────
export function drawPowerBar(ctx, power, x, y) {
    const w = 220;
    const h = 16;
    const bx = x - w / 2;
    const by = y;

    // bg
    ctx.fillStyle = 'rgba(0,0,0,0.5)';
    roundRect(ctx, bx - 2, by - 2, w + 4, h + 4, 4);
    ctx.fill();

    // fill
    const fillW = w * power;
    if (fillW > 0) {
        const grad = ctx.createLinearGradient(bx, 0, bx + w, 0);
        grad.addColorStop(0, '#28a746');
        grad.addColorStop(0.5, '#eb9119');
        grad.addColorStop(1, '#dc3545');
        ctx.fillStyle = grad;
        roundRect(ctx, bx, by, fillW, h, 3);
        ctx.fill();
    }

    // stripes
    ctx.strokeStyle = 'rgba(255,255,255,0.15)';
    ctx.lineWidth = 1;
    for (let sx = bx + 10; sx < bx + fillW; sx += 12) {
        ctx.beginPath();
        ctx.moveTo(sx, by);
        ctx.lineTo(sx, by + h);
        ctx.stroke();
    }

    // border
    ctx.strokeStyle = C_GOLD;
    ctx.lineWidth = 1;
    roundRect(ctx, bx, by, w, h, 3);
    ctx.stroke();

    // label
    ctx.fillStyle = C_TEXT;
    ctx.font = 'bold 13px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(`${(power * 100) | 0}%`, x, by + h + 16);
}

// ── Spin Indicator ─────────────────────────────────────
export function drawSpinIndicator(ctx, spinX, spinY, cx, cy) {
    const R = 28;

    // background
    ctx.fillStyle = 'rgba(20,20,20,0.85)';
    ctx.beginPath();
    ctx.arc(cx, cy, R + 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#f8f8f8';
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.fill();

    // crosshair
    ctx.strokeStyle = 'rgba(0,0,0,0.15)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(cx - R, cy); ctx.lineTo(cx + R, cy);
    ctx.moveTo(cx, cy - R); ctx.lineTo(cx, cy + R);
    ctx.stroke();

    // red dot
    const dotX = cx + spinX * (R - 5);
    const dotY = cy + spinY * (R - 5);
    ctx.fillStyle = '#dc3545';
    ctx.beginPath();
    ctx.arc(dotX, dotY, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 1;
    ctx.stroke();

    // label
    ctx.font = '13px Arial';
    ctx.textAlign = 'center';
    ctx.fillStyle = C_TEXT_DIM;
    let label = '스핀 조절';
    if (spinY < -0.15) label = '밀어치기';
    else if (spinY > 0.15) label = '끌어치기';
    else if (spinX < -0.15) label = '좌회전';
    else if (spinX > 0.15) label = '우회전';
    ctx.fillText(label, cx, cy + R + 20);
}

// ── Pocket Effect Particles ────────────────────────────
export class PocketEffect {
    constructor() { this.particles = []; this.flashes = []; }

    spawn(x, y, color) {
        for (let i = 0; i < 35; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = 80 + Math.random() * 200;
            let c;
            if (Math.random() < 0.7) {
                c = `rgb(${color[0]},${color[1]},${color[2]})`;
            } else {
                c = Math.random() < 0.5 ? C_GOLD_LIGHT : '#fff';
            }
            this.particles.push({
                x, y, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed,
                life: 0.4 + Math.random() * 0.6, age: 0, color: c,
                size: 2 + Math.random() * 4,
            });
        }
        this.flashes.push({ x, y, life: 0.2, age: 0 });
    }

    update(dt) {
        for (const p of this.particles) {
            p.age += dt;
            p.vy += 300 * dt; // gravity
            p.vx *= 0.97;
            p.vy *= 0.97;
            p.x += p.vx * dt;
            p.y += p.vy * dt;
        }
        this.particles = this.particles.filter(p => p.age < p.life);
        for (const f of this.flashes) f.age += dt;
        this.flashes = this.flashes.filter(f => f.age < f.life);
    }

    draw(ctx) {
        for (const f of this.flashes) {
            const alpha = 1 - f.age / f.life;
            const r = 30 + f.age / f.life * 40;
            ctx.save();
            ctx.globalAlpha = alpha * 0.6;
            ctx.fillStyle = 'rgba(255,255,220,1)';
            ctx.beginPath();
            ctx.arc(f.x, f.y, r, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
        for (const p of this.particles) {
            const alpha = 1 - p.age / p.life;
            ctx.save();
            ctx.globalAlpha = alpha;
            ctx.fillStyle = p.color;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size * (1 - p.age / p.life * 0.5), 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
    }
}

// ── Sidebar & HUD ──────────────────────────────────────
export function drawSidebar(ctx, players, currentTurn, isCarom = false) {
    // sidebar bg
    ctx.fillStyle = C_SIDEBAR_BG;
    ctx.fillRect(0, 0, SIDEBAR_W, WIN_H);
    ctx.fillStyle = C_SIDEBAR_BORDER;
    ctx.fillRect(SIDEBAR_W - 1, 0, 1, WIN_H);

    // title
    ctx.fillStyle = C_GOLD_LIGHT;
    ctx.font = 'bold 26px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('🎱 8 Ball Pool', SIDEBAR_W / 2, 50);

    // divider
    ctx.fillStyle = C_SIDEBAR_BORDER;
    ctx.fillRect(20, 70, SIDEBAR_W - 40, 1);

    // players
    ctx.font = '14px Arial';
    ctx.fillStyle = C_TEXT_DIM;
    ctx.fillText('플레이어', SIDEBAR_W / 2, 100);

    if (players) {
        for (let i = 0; i < players.length; i++) {
            const p = players[i];
            const py = 120 + i * 110;
            const isActive = i === currentTurn;

            // card background
            ctx.fillStyle = isActive ? C_SIDEBAR_LIGHT : 'rgba(255,255,255,0.03)';
            roundRect(ctx, 15, py, SIDEBAR_W - 30, 95, 8);
            ctx.fill();
            if (isActive) {
                ctx.strokeStyle = C_GOLD;
                ctx.lineWidth = 2;
                roundRect(ctx, 15, py, SIDEBAR_W - 30, 95, 8);
                ctx.stroke();
            }

            // avatar
            const avColor = i === 0 ? '#3287d2' : '#eb9119';
            ctx.fillStyle = avColor;
            ctx.beginPath();
            ctx.arc(45, py + 35, 18, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 16px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(`P${i + 1}`, 45, py + 40);

            // name
            ctx.fillStyle = isActive ? C_TEXT : C_TEXT_DIM;
            ctx.font = `bold 20px Arial`;
            ctx.textAlign = 'left';
            ctx.fillText(p.name, 75, py + 32);

            // group
            if (p.group) {
                ctx.font = '14px Arial';
                ctx.fillStyle = C_ACCENT_BLUE;
                ctx.fillText(p.group === 'solid' ? '솔리드 (1-7)' : '스트라이프 (9-15)', 75, py + 52);
            }

            // pocketed count
            if (!isCarom) {
                ctx.font = '13px Arial';
                ctx.fillStyle = C_TEXT_DIM;
                const cnt = p.pocketedBalls ? p.pocketedBalls.length : (p.scores !== undefined ? p.scores : 0);
                ctx.fillText(`넣은 공: ${cnt}개`, 75, py + 72);
            } else if (p.scores !== undefined) {
                ctx.font = 'bold 28px Arial';
                ctx.fillStyle = C_GOLD_LIGHT;
                ctx.textAlign = 'right';
                ctx.fillText(String(p.scores), SIDEBAR_W - 35, py + 50);
            }

            // active indicator
            if (isActive) {
                ctx.fillStyle = '#28a746';
                ctx.beginPath();
                ctx.arc(SIDEBAR_W - 30, py + 15, 5, 0, Math.PI * 2);
                ctx.fill();
            }
        }
    }
}

export function drawTurnHeader(ctx, text, highlight = true) {
    const cx = SIDEBAR_W + (WIN_W - SIDEBAR_W) / 2;
    ctx.font = 'bold 22px Arial';
    ctx.textAlign = 'center';
    ctx.fillStyle = highlight ? C_GOLD_LIGHT : C_TEXT_DIM;
    ctx.fillText(text, cx, TABLE_Y - 30);
}

export function drawBallStatusBar(ctx, balls, player1, player2) {
    const barY = TABLE_Y + TABLE_H + 35;
    const cx = SIDEBAR_W + (WIN_W - SIDEBAR_W) / 2;
    const spacing = 38;

    // cue ball center
    const cueBall = balls.find(b => b.number === 0);
    if (cueBall && !cueBall.pocketed) {
        drawMiniball(ctx, cx, barY, 0, false);
    }

    // solids left
    for (let i = 1; i <= 7; i++) {
        const b = balls.find(b2 => b2.number === i);
        const pocketed = !b || b.pocketed;
        drawMiniball(ctx, cx - (8 - i) * spacing, barY, i, pocketed);
    }

    // stripes right
    for (let i = 9; i <= 15; i++) {
        const b = balls.find(b2 => b2.number === i);
        const pocketed = !b || b.pocketed;
        drawMiniball(ctx, cx + (i - 8) * spacing, barY, i, pocketed);
    }

    // 8 ball
    const b8 = balls.find(b => b.number === 8);
    drawMiniball(ctx, cx, barY + 30, 8, !b8 || b8.pocketed);
}

function drawMiniball(ctx, x, y, num, pocketed) {
    const r = 13;
    const color = BALL_COLORS[num] || [200, 200, 200];
    const isStripe = num >= 9;

    ctx.save();
    if (pocketed) ctx.globalAlpha = 0.2;

    if (num === 0) {
        ctx.fillStyle = '#e8e8e8';
    } else if (isStripe) {
        ctx.fillStyle = '#e8e8e8';
    } else {
        ctx.fillStyle = rgb(color[0], color[1], color[2]);
    }
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();

    if (isStripe) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.clip();
        ctx.fillStyle = rgb(color[0], color[1], color[2]);
        ctx.fillRect(x - r, y - r * 0.45, r * 2, r * 0.9);
        ctx.restore();
    }

    if (num > 0) {
        ctx.fillStyle = '#fff';
        ctx.beginPath();
        ctx.arc(x, y, r * 0.4, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#111';
        ctx.font = `bold ${r - 3}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(num), x, y + 1);
    }

    ctx.strokeStyle = 'rgba(0,0,0,0.2)';
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.stroke();

    ctx.restore();
}

// ── Dialog ─────────────────────────────────────────────
export function drawDialog(ctx, title, message, buttons) {
    // overlay
    ctx.fillStyle = 'rgba(0,0,0,0.6)';
    ctx.fillRect(0, 0, WIN_W, WIN_H);

    const w = 480;
    const lines = message.split('\n');
    const h = 160 + lines.length * 28;
    const x = (WIN_W - w) / 2;
    const y = (WIN_H - h) / 2;

    // box
    ctx.fillStyle = '#1a1a2e';
    ctx.strokeStyle = C_GOLD;
    ctx.lineWidth = 2;
    roundRect(ctx, x, y, w, h, 16);
    ctx.fill();
    ctx.stroke();

    // title
    ctx.fillStyle = C_GOLD_LIGHT;
    ctx.font = 'bold 26px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(title, x + w / 2, y + 45);

    // separator
    ctx.fillStyle = C_GOLD;
    ctx.globalAlpha = 0.3;
    ctx.fillRect(x + 30, y + 62, w - 60, 1);
    ctx.globalAlpha = 1;

    // message lines
    ctx.fillStyle = C_TEXT;
    ctx.font = '20px Arial';
    for (let i = 0; i < lines.length; i++) {
        ctx.fillText(lines[i], x + w / 2, y + 95 + i * 28);
    }

    // buttons
    const btnW = 130;
    const btnH = 40;
    const btnY = y + h - 60;
    const totalBtnW = buttons.length * btnW + (buttons.length - 1) * 20;
    const btnStartX = x + (w - totalBtnW) / 2;
    const rects = [];

    for (let i = 0; i < buttons.length; i++) {
        const bx = btnStartX + i * (btnW + 20);
        ctx.fillStyle = i === 0 ? C_BTN_GREEN : C_BTN_DARK;
        roundRect(ctx, bx, btnY, btnW, btnH, 8);
        ctx.fill();
        ctx.fillStyle = C_TEXT;
        ctx.font = 'bold 17px Arial';
        ctx.fillText(buttons[i], bx + btnW / 2, btnY + btnH / 2 + 6);
        rects.push({ x: bx, y: btnY, w: btnW, h: btnH, label: buttons[i] });
    }

    return rects;
}

// ── Replay Overlay ─────────────────────────────────────
export function drawReplayOverlay(ctx, progress, elapsed) {
    // vignette
    ctx.save();
    ctx.globalAlpha = 0.3;
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, WIN_W, WIN_H);
    ctx.restore();

    // REPLAY banner
    const pulse = Math.sin(elapsed * 4) * 0.3 + 0.7;
    ctx.save();
    ctx.globalAlpha = pulse;
    ctx.fillStyle = '#dc3545';
    ctx.font = 'bold 36px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('REPLAY', WIN_W / 2, 60);
    ctx.restore();

    // slow-mo label
    ctx.fillStyle = C_TEXT_DIM;
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('x0.35 슬로모션', WIN_W / 2, 85);

    // progress bar
    const bw = 400;
    const bx = (WIN_W - bw) / 2;
    const by = WIN_H - 40;
    ctx.fillStyle = 'rgba(255,255,255,0.1)';
    ctx.fillRect(bx, by, bw, 4);
    ctx.fillStyle = C_GOLD_LIGHT;
    ctx.fillRect(bx, by, bw * progress, 4);

    // skip hint
    ctx.fillStyle = C_TEXT_DIM;
    ctx.font = '14px Arial';
    ctx.fillText('SPACE: 건너뛰기', WIN_W / 2, WIN_H - 15);
}

// ── Menu Scene Renderer ────────────────────────────────
export function drawMenuScene(ctx, buttons, hoverIdx) {
    // background
    ctx.fillStyle = C_BG;
    ctx.fillRect(0, 0, WIN_W, WIN_H);

    // sidebar
    ctx.fillStyle = C_SIDEBAR_BG;
    ctx.fillRect(0, 0, SIDEBAR_W, WIN_H);
    ctx.fillStyle = C_SIDEBAR_BORDER;
    ctx.fillRect(SIDEBAR_W - 1, 0, 1, WIN_H);

    // sidebar content
    ctx.fillStyle = C_TEXT_DIM;
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Guest', SIDEBAR_W / 2, 80);
    ctx.fillStyle = '#3287d2';
    ctx.beginPath();
    ctx.arc(SIDEBAR_W / 2, 40, 22, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 18px Arial';
    ctx.fillText('G', SIDEBAR_W / 2, 46);

    // title area
    const gameCx = SIDEBAR_W + (WIN_W - SIDEBAR_W) / 2;

    // title banner
    const bannerW = 700;
    const bannerH = 130;
    const bannerX = gameCx - bannerW / 2;
    const bannerY = 100;
    const grad = ctx.createLinearGradient(bannerX, bannerY, bannerX, bannerY + bannerH);
    grad.addColorStop(0, 'rgba(22,90,30,0.9)');
    grad.addColorStop(1, 'rgba(15,60,20,0.9)');
    ctx.fillStyle = grad;
    roundRect(ctx, bannerX, bannerY, bannerW, bannerH, 16);
    ctx.fill();
    ctx.strokeStyle = C_GOLD;
    ctx.lineWidth = 2;
    roundRect(ctx, bannerX, bannerY, bannerW, bannerH, 16);
    ctx.stroke();

    // 8-ball icon
    ctx.fillStyle = '#111';
    ctx.beginPath();
    ctx.arc(gameCx - 160, bannerY + bannerH / 2, 35, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.beginPath();
    ctx.arc(gameCx - 160, bannerY + bannerH / 2, 14, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#111';
    ctx.font = 'bold 18px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('8', gameCx - 160, bannerY + bannerH / 2 + 6);

    // title text
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 72px Impact, Arial';
    ctx.fillText('BALL POOL', gameCx + 30, bannerY + bannerH / 2 + 25);
    ctx.strokeStyle = '#0f5a16';
    ctx.lineWidth = 2;
    ctx.strokeText('BALL POOL', gameCx + 30, bannerY + bannerH / 2 + 25);

    // buttons
    for (let i = 0; i < buttons.length; i++) {
        const btn = buttons[i];
        const isHover = i === hoverIdx;
        drawMenuButton(ctx, btn, isHover);
    }

    // footer
    ctx.fillStyle = 'rgba(0,0,0,0.3)';
    roundRect(ctx, gameCx - 350, WIN_H - 60, 700, 36, 8);
    ctx.fill();
    ctx.fillStyle = C_TEXT_DIM;
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('포켓볼 게임에 오신 것을 환영합니다!', gameCx, WIN_H - 37);
}

function drawMenuButton(ctx, btn, hover) {
    const { x, y, w, h, text, color, outline, subtitle } = btn;

    if (outline) {
        ctx.strokeStyle = hover ? C_GOLD_LIGHT : C_GOLD;
        ctx.lineWidth = hover ? 2 : 1.5;
        roundRect(ctx, x, y, w, h, 10);
        ctx.stroke();
        if (hover) {
            ctx.fillStyle = 'rgba(184,134,11,0.1)';
            roundRect(ctx, x, y, w, h, 10);
            ctx.fill();
        }
        ctx.fillStyle = hover ? C_GOLD_LIGHT : C_GOLD;
    } else {
        const [r, g, b] = hexToRgb(color);
        const offset = hover ? 20 : 0;
        ctx.fillStyle = rgb(
            Math.min(255, r + offset),
            Math.min(255, g + offset),
            Math.min(255, b + offset)
        );
        roundRect(ctx, x, y, w, h, 10);
        ctx.fill();
        ctx.fillStyle = '#fff';
    }

    ctx.font = `bold 22px Arial`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, x + w / 2, y + h / 2 + (subtitle ? -8 : 0));

    if (subtitle) {
        ctx.font = '15px Arial';
        ctx.fillStyle = 'rgba(255,255,255,0.6)';
        ctx.fillText(subtitle, x + w / 2, y + h / 2 + 16);
    }
}

// ── Helpers ────────────────────────────────────────────
export function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
}

function hexToRgb(hex) {
    if (typeof hex !== 'string') return [100, 100, 100];
    hex = hex.replace('#', '');
    return [
        parseInt(hex.substr(0, 2), 16),
        parseInt(hex.substr(2, 2), 16),
        parseInt(hex.substr(4, 2), 16),
    ];
}
