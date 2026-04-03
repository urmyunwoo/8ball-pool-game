import {
    BALL_RADIUS, TABLE_X, TABLE_Y, TABLE_W, TABLE_H,
    CUSHION_SIZE, POCKET_RADIUS, POCKETS,
    FRICTION_DAMPING, CUSHION_RESTITUTION, BALL_RESTITUTION,
    MIN_SPEED, PHYSICS_SUBSTEPS
} from './config.js';

// ── Ball ───────────────────────────────────────────────
export class Ball {
    constructor(number, x, y) {
        this.number = number;
        this.x = x;
        this.y = y;
        this.vx = 0;
        this.vy = 0;
        this.radius = BALL_RADIUS;
        this.pocketed = false;
        this.rotX = 0;
        this.rotY = 0;
        this.spinX = 0;
        this.spinY = 0;
        this.spinPower = 0;
        this.shotDirX = 0;
        this.shotDirY = 0;
        this.pocketPos = null;
        this.color = null; // override for carom
    }

    get speed() { return Math.sqrt(this.vx * this.vx + this.vy * this.vy); }
    get isMoving() { return !this.pocketed && this.speed > MIN_SPEED; }

    get group() {
        if (this.number === 0) return 'cue';
        if (this.number === 8) return 'eight';
        if (this.number >= 1 && this.number <= 7) return 'solid';
        return 'stripe';
    }

    place(x, y) {
        this.x = x; this.y = y;
        this.vx = 0; this.vy = 0;
        this.pocketed = false;
        this.spinX = 0; this.spinY = 0;
        this.spinPower = 0;
    }

    shoot(angle, power, spinX = 0, spinY = 0) {
        this.vx = Math.cos(angle) * power;
        this.vy = Math.sin(angle) * power;
        this.shotDirX = Math.cos(angle);
        this.shotDirY = Math.sin(angle);
        this.spinX = spinX;
        this.spinY = spinY;
        this.spinPower = Math.sqrt(spinX * spinX + spinY * spinY);
    }

    clone() {
        const b = new Ball(this.number, this.x, this.y);
        b.vx = this.vx; b.vy = this.vy;
        b.pocketed = this.pocketed;
        b.rotX = this.rotX; b.rotY = this.rotY;
        b.color = this.color;
        return b;
    }
}

// ── Physics Engine ─────────────────────────────────────
export class Physics {
    constructor(hasPockets = true) {
        this.hasPockets = hasPockets;
        this._left   = TABLE_X + CUSHION_SIZE;
        this._right  = TABLE_X + TABLE_W - CUSHION_SIZE;
        this._top    = TABLE_Y + CUSHION_SIZE;
        this._bottom = TABLE_Y + TABLE_H - CUSHION_SIZE;
        this.cushionHits = 0;
        this.ballContacts = new Set();
        this.collisionEvents = [];
    }

    resetTracking() {
        this.cushionHits = 0;
        this.ballContacts.clear();
    }

    step(balls, dt) {
        const subDt = dt / PHYSICS_SUBSTEPS;
        const pocketed = [];

        for (let s = 0; s < PHYSICS_SUBSTEPS; s++) {
            for (const b of balls) {
                if (b.pocketed) continue;
                b.x += b.vx * subDt;
                b.y += b.vy * subDt;
                // update rotation for visual
                const spd = b.speed;
                if (spd > MIN_SPEED) {
                    const angular = subDt / b.radius;
                    b.rotX -= b.vy * angular;
                    b.rotY += b.vx * angular;
                }
            }
            this._wallCollisions(balls);
            this._ballCollisions(balls);

            if (this.hasPockets) {
                const p = this._checkPockets(balls);
                for (const num of p) {
                    if (!pocketed.includes(num)) pocketed.push(num);
                }
            }
        }

        this._applyFriction(balls, dt);
        return pocketed;
    }

    _wallCollisions(balls) {
        for (const b of balls) {
            if (b.pocketed) continue;
            // near pocket? skip wall collision
            if (this.hasPockets && this._nearPocket(b.x, b.y)) continue;

            let hit = false;
            if (b.x < this._left) {
                b.x = this._left;
                b.vx = Math.abs(b.vx) * CUSHION_RESTITUTION;
                hit = true;
            } else if (b.x > this._right) {
                b.x = this._right;
                b.vx = -Math.abs(b.vx) * CUSHION_RESTITUTION;
                hit = true;
            }
            if (b.y < this._top) {
                b.y = this._top;
                b.vy = Math.abs(b.vy) * CUSHION_RESTITUTION;
                hit = true;
            } else if (b.y > this._bottom) {
                b.y = this._bottom;
                b.vy = -Math.abs(b.vy) * CUSHION_RESTITUTION;
                hit = true;
            }
            if (hit) {
                // spin kick
                if (b.number === 0 && b.spinPower > 0) {
                    const kick = b.spinX * 40;
                    if (Math.abs(b.vx) > Math.abs(b.vy)) {
                        b.vy += kick;
                    } else {
                        b.vx += kick;
                    }
                }
                this.cushionHits++;
                this.collisionEvents.push({ kind: 'wall_hit', speed: b.speed * 60 });
            }
        }
    }

    _nearPocket(x, y) {
        const threshold = POCKET_RADIUS + BALL_RADIUS + 10;
        for (const [px, py] of POCKETS) {
            const dx = x - px, dy = y - py;
            if (dx * dx + dy * dy < threshold * threshold) return true;
        }
        return false;
    }

    _ballCollisions(balls) {
        for (let i = 0; i < balls.length; i++) {
            const a = balls[i];
            if (a.pocketed) continue;
            for (let j = i + 1; j < balls.length; j++) {
                const b = balls[j];
                if (b.pocketed) continue;

                const dx = b.x - a.x;
                const dy = b.y - a.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const minDist = a.radius + b.radius;

                if (dist < minDist && dist > 0) {
                    // separate
                    const nx = dx / dist;
                    const ny = dy / dist;
                    const overlap = minDist - dist;
                    a.x -= nx * overlap * 0.5;
                    a.y -= ny * overlap * 0.5;
                    b.x += nx * overlap * 0.5;
                    b.y += ny * overlap * 0.5;

                    // elastic collision
                    const relVx = a.vx - b.vx;
                    const relVy = a.vy - b.vy;
                    const relDot = relVx * nx + relVy * ny;
                    if (relDot > 0) {
                        const impulse = relDot * BALL_RESTITUTION;
                        a.vx -= impulse * nx;
                        a.vy -= impulse * ny;
                        b.vx += impulse * nx;
                        b.vy += impulse * ny;

                        const relSpeed = Math.sqrt(relVx * relVx + relVy * relVy) * 60;
                        this.collisionEvents.push({ kind: 'ball_hit', speed: relSpeed });
                        this.ballContacts.add(a.number);
                        this.ballContacts.add(b.number);
                    }
                }
            }
        }
    }

    _applyFriction(balls, dt) {
        const frames60 = dt * 60;
        const damp = Math.pow(FRICTION_DAMPING, frames60);
        for (const b of balls) {
            if (b.pocketed) continue;
            b.vx *= damp;
            b.vy *= damp;

            // spin-to-velocity for cue ball
            if (b.number === 0 && b.spinPower > 0) {
                const factor = 0.3 * dt;
                // follow / draw
                b.vx += b.shotDirX * (-b.spinY) * factor * 60;
                b.vy += b.shotDirY * (-b.spinY) * factor * 60;
                // side spin
                b.vx += (-b.shotDirY) * b.spinX * factor * 30;
                b.vy += b.shotDirX * b.spinX * factor * 30;
                b.spinPower *= Math.pow(0.97, frames60);
                if (b.spinPower < 0.01) {
                    b.spinPower = 0;
                    b.spinX = 0;
                    b.spinY = 0;
                }
            }

            if (b.speed < MIN_SPEED) {
                b.vx = 0;
                b.vy = 0;
            }
        }
    }

    _checkPockets(balls) {
        const pocketed = [];
        for (const b of balls) {
            if (b.pocketed) continue;
            for (const [px, py] of POCKETS) {
                const dx = b.x - px;
                const dy = b.y - py;
                if (Math.sqrt(dx * dx + dy * dy) < POCKET_RADIUS + b.radius * 0.75) {
                    b.pocketed = true;
                    b.pocketPos = [px, py];
                    b.vx = 0; b.vy = 0;
                    pocketed.push(b.number);
                    break;
                }
            }
        }
        return pocketed;
    }
}

// ── Guide Line Ray Casting ─────────────────────────────
export function castRay(cx, cy, angle, balls, maxLen = 800) {
    const dirX = Math.cos(angle);
    const dirY = Math.sin(angle);
    let minT = maxLen;
    let hitBall = null;

    // Check ball intersections
    for (const b of balls) {
        if (b.pocketed || b.number === 0) continue;
        const ox = cx - b.x;
        const oy = cy - b.y;
        const a = dirX * dirX + dirY * dirY;
        const bCoeff = 2 * (ox * dirX + oy * dirY);
        const c = ox * ox + oy * oy - (BALL_RADIUS * 2) * (BALL_RADIUS * 2);
        const disc = bCoeff * bCoeff - 4 * a * c;
        if (disc >= 0) {
            const t = (-bCoeff - Math.sqrt(disc)) / (2 * a);
            if (t > 0 && t < minT) {
                minT = t;
                hitBall = b;
            }
        }
    }

    // Check wall intersections
    const walls = [
        { x: TABLE_X + CUSHION_SIZE, nx: 1, ny: 0 },     // left
        { x: TABLE_X + TABLE_W - CUSHION_SIZE, nx: -1, ny: 0 }, // right
        { y: TABLE_Y + CUSHION_SIZE, nx: 0, ny: 1 },     // top
        { y: TABLE_Y + TABLE_H - CUSHION_SIZE, nx: 0, ny: -1 }, // bottom
    ];
    for (const w of walls) {
        let t;
        if (w.nx !== 0) {
            if (dirX === 0) continue;
            t = (w.x - cx) / dirX;
        } else {
            if (dirY === 0) continue;
            t = (w.y - cy) / dirY;
        }
        if (t > 0 && t < minT && !hitBall) {
            minT = t;
        }
    }

    const endX = cx + dirX * minT;
    const endY = cy + dirY * minT;

    let targetDir = null;
    if (hitBall) {
        const tdx = hitBall.x - endX;
        const tdy = hitBall.y - endY;
        const td = Math.sqrt(tdx * tdx + tdy * tdy);
        if (td > 0) targetDir = { x: tdx / td, y: tdy / td };
        // reflection
        const reflX = dirX - 2 * (dirX * (tdx/td) + dirY * (tdy/td)) * (tdx/td);
        const reflY = dirY - 2 * (dirX * (tdx/td) + dirY * (tdy/td)) * (tdy/td);
        return { endX, endY, hitBall, targetDir, reflX, reflY, dist: minT };
    }

    return { endX, endY, hitBall: null, targetDir: null, reflX: 0, reflY: 0, dist: minT };
}
