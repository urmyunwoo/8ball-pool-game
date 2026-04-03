import { TABLE_X, TABLE_Y, TABLE_W, TABLE_H, BALL_RADIUS } from './config.js';

// ── Turn Results ───────────────────────────────────────
export const TURN = {
    CONTINUE: 'continue',
    SWITCH: 'switch',
    FOUL: 'foul',
    WIN: 'win',
    LOSE: 'lose',
};

// ── Game Phases ────────────────────────────────────────
export const PHASE = {
    BREAK: 'break',
    PLAYING: 'playing',
    FINISH: 'finish',
};

// ── Player State ───────────────────────────────────────
export class PlayerState {
    constructor(name) {
        this.name = name;
        this.group = null; // 'solid' | 'stripe'
        this.pocketedBalls = [];
        this.isDone = false;
    }
}

// ── 8-Ball Game Logic ──────────────────────────────────
export class GameLogic {
    constructor(p1Name = 'Player 1', p2Name = 'Player 2') {
        this.players = [new PlayerState(p1Name), new PlayerState(p2Name)];
        this.current = 0;
        this.phase = PHASE.BREAK;
        this.winner = null;
        this.message = `${p1Name}의 브레이크 샷`;
        this.firstHitGroup = null;
    }

    get currentPlayer() { return this.players[this.current]; }
    get otherPlayer() { return this.players[1 - this.current]; }

    static get CUE_START_X() { return TABLE_X + TABLE_W * 0.25; }
    static get CUE_START_Y() { return TABLE_Y + TABLE_H * 0.5; }

    rackPositions() {
        const apexX = TABLE_X + TABLE_W * 0.72;
        const apexY = TABLE_Y + TABLE_H * 0.5;
        const gap = BALL_RADIUS * 2 + 1;
        const rowDx = gap * Math.sqrt(3) / 2;

        const rows = [
            [1],
            [2, 9],
            [3, 8, 10],
            [4, 11, 7, 12],
            [5, 13, 6, 14, 15],
        ];

        const positions = [];
        for (let r = 0; r < rows.length; r++) {
            const row = rows[r];
            const count = row.length;
            for (let c = 0; c < count; c++) {
                const colOff = c - (count - 1) / 2;
                const x = apexX + r * rowDx;
                const y = apexY + colOff * gap;
                positions.push([row[c], x, y]);
            }
        }
        return positions;
    }

    ballInHandPos() {
        return [GameLogic.CUE_START_X, GameLogic.CUE_START_Y];
    }

    onShotEnd(pocketed, firstHitGroup, cuePocketed) {
        // === BREAK ===
        if (this.phase === PHASE.BREAK) {
            if (cuePocketed) {
                this.message = `파울! 큐볼 포켓 — ${this.otherPlayer.name} 차례`;
                this.current = 1 - this.current;
                this.phase = PHASE.PLAYING;
                return TURN.FOUL;
            }
            if (pocketed.length === 0) {
                this.message = `${this.otherPlayer.name}의 차례`;
                this.current = 1 - this.current;
                return TURN.SWITCH;
            }
            // assign groups
            const solids = pocketed.filter(n => n >= 1 && n <= 7).length;
            const stripes = pocketed.filter(n => n >= 9 && n <= 15).length;
            if (solids >= stripes) {
                this.currentPlayer.group = 'solid';
                this.otherPlayer.group = 'stripe';
            } else {
                this.currentPlayer.group = 'stripe';
                this.otherPlayer.group = 'solid';
            }
            this._recordPocketed(pocketed);
            this.phase = PHASE.PLAYING;
            this.message = `그룹 배정! ${this.currentPlayer.name} 계속`;
            return TURN.CONTINUE;
        }

        // === PLAYING ===
        // 8-ball pocketed?
        const eightPocketed = pocketed.includes(8);
        if (eightPocketed) {
            if (this.currentPlayer.isDone) {
                this.phase = PHASE.FINISH;
                this.winner = this.current;
                this.message = `${this.currentPlayer.name} 승리!`;
                return TURN.WIN;
            } else {
                this.phase = PHASE.FINISH;
                this.winner = 1 - this.current;
                this.message = `${this.currentPlayer.name} 패배 (8번 일찍 포켓)`;
                return TURN.LOSE;
            }
        }

        // Foul checks
        if (cuePocketed) {
            this._recordPocketed(pocketed);
            this.message = `파울! 큐볼 포켓 — ${this.otherPlayer.name} 차례`;
            this.current = 1 - this.current;
            return TURN.FOUL;
        }

        // Wrong first hit
        if (firstHitGroup && this.currentPlayer.group) {
            if (firstHitGroup !== this.currentPlayer.group && firstHitGroup !== 'eight') {
                this._recordPocketed(pocketed);
                this.message = `파울! 상대 공 먼저 맞힘 — ${this.otherPlayer.name} 차례`;
                this.current = 1 - this.current;
                return TURN.FOUL;
            }
        }

        this._recordPocketed(pocketed);

        // Check if pocketed own balls
        const ownPocketed = pocketed.filter(n => {
            if (n === 0 || n === 8) return false;
            const g = n <= 7 ? 'solid' : 'stripe';
            return g === this.currentPlayer.group;
        });

        if (ownPocketed.length > 0) {
            this.message = `${this.currentPlayer.name} 계속!`;
            return TURN.CONTINUE;
        }

        this.message = `${this.otherPlayer.name}의 차례`;
        this.current = 1 - this.current;
        return TURN.SWITCH;
    }

    _recordPocketed(nums) {
        for (const n of nums) {
            if (n === 0 || n === 8) continue;
            const g = n <= 7 ? 'solid' : 'stripe';
            for (const p of this.players) {
                if (p.group === g) {
                    if (!p.pocketedBalls.includes(n)) p.pocketedBalls.push(n);
                    p.isDone = p.pocketedBalls.length >= 7;
                }
            }
        }
    }
}

// ── Carom Logic ────────────────────────────────────────
export const CAROM_RESULT = {
    SCORE: 'score',
    MISS: 'miss',
    WIN: 'win',
};

export class CaromLogic {
    constructor(mode = '3cushion', p1 = 'Player 1', p2 = 'Player 2') {
        this.mode = mode;
        this.names = [p1, p2];
        this.scores = [0, 0];
        this.current = 0;
        this.targetScore = mode === '3cushion' ? 10 : 15;
        this.cueBalls = [0, 1]; // P1 uses white(0), P2 uses yellow(1)
    }

    get currentCue() { return this.cueBalls[this.current]; }

    setupBalls() {
        // Returns [number, x, y, colorOverride] for carom balls
        const cx = TABLE_X + TABLE_W / 2;
        const cy = TABLE_Y + TABLE_H / 2;
        const balls = [
            [0, TABLE_X + TABLE_W * 0.25, cy, [248, 248, 248]],      // white
            [1, TABLE_X + TABLE_W * 0.75, cy, [240, 210, 50]],        // yellow
            [2, cx, cy - 50, [210, 30, 30]],                           // red 1
        ];
        if (this.mode === '4ball') {
            balls.push([3, cx, cy + 50, [210, 30, 30]]);              // red 2
        }
        return balls;
    }

    evaluate(cushionHits, ballContacts, cueBallNum) {
        if (this.mode === '3cushion') {
            // must hit 2+ other balls AND 3+ cushions
            const otherContacts = ballContacts.size - (ballContacts.has(cueBallNum) ? 1 : 0);
            if (otherContacts >= 2 && cushionHits >= 3) {
                this.scores[this.current]++;
                if (this.scores[this.current] >= this.targetScore) {
                    return CAROM_RESULT.WIN;
                }
                return CAROM_RESULT.SCORE;
            }
        } else {
            // 4ball: must hit both red balls (2 and 3)
            if (ballContacts.has(2) && ballContacts.has(3)) {
                this.scores[this.current]++;
                if (this.scores[this.current] >= this.targetScore) {
                    return CAROM_RESULT.WIN;
                }
                return CAROM_RESULT.SCORE;
            }
        }
        this.current = 1 - this.current;
        return CAROM_RESULT.MISS;
    }
}
