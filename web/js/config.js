// ── Window ─────────────────────────────────────────────
export const WIN_W = 1920;
export const WIN_H = 1080;
export const FPS = 120;
export const TITLE = "8 Ball Pool";

// ── Sidebar ────────────────────────────────────────────
export const SIDEBAR_W = 300;

// ── Table geometry ─────────────────────────────────────
export const TABLE_W = 1200;
export const TABLE_H = 600;
export const TABLE_X = SIDEBAR_W + (WIN_W - SIDEBAR_W - TABLE_W) / 2 | 0;
export const TABLE_Y = 220;
export const CUSHION_SIZE = 34;
export const POCKET_RADIUS = 25;

export const POCKETS = [
    [TABLE_X, TABLE_Y],
    [TABLE_X + TABLE_W / 2, TABLE_Y - 6],
    [TABLE_X + TABLE_W, TABLE_Y],
    [TABLE_X, TABLE_Y + TABLE_H],
    [TABLE_X + TABLE_W / 2, TABLE_Y + TABLE_H + 6],
    [TABLE_X + TABLE_W, TABLE_Y + TABLE_H],
];

// ── Ball ───────────────────────────────────────────────
export const BALL_RADIUS = 16;

// ── Physics ────────────────────────────────────────────
export const FRICTION_DAMPING = 0.987;
export const CUSHION_RESTITUTION = 0.88;
export const BALL_RESTITUTION = 0.96;
export const MIN_SPEED = 0.3;
export const PHYSICS_SUBSTEPS = 16;

// ── Shot ───────────────────────────────────────────────
export const MAX_POWER = 1350.0;
export const POWER_SCALE = 0.35;

// ── Colors ─────────────────────────────────────────────
export const C_BG         = '#0f0a08';
export const C_WOOD       = '#3c2010';
export const C_WOOD_LIGHT = '#503018';
export const C_FELT       = '#165a1e';
export const C_FELT_DARK  = '#124818';
export const C_POCKET     = '#060606';
export const C_GOLD       = '#b8860b';
export const C_GOLD_LIGHT = '#dca828';
export const C_TEXT       = '#e6e6e6';
export const C_TEXT_DIM   = '#8c8c8c';
export const C_WHITE      = '#ffffff';
export const C_BLACK      = '#0a0a0a';
export const C_RED        = '#c82828';
export const C_GREEN_BTN  = '#1e8c32';
export const C_OVERLAY    = 'rgba(0,0,0,0.63)';

export const C_SIDEBAR_BG     = '#1c202d';
export const C_SIDEBAR_LIGHT  = '#262c3c';
export const C_SIDEBAR_BORDER = '#303646';
export const C_BTN_GREEN      = '#28a746';
export const C_BTN_ORANGE     = '#eb9119';
export const C_BTN_BLUE       = '#3287d2';
export const C_BTN_DARK       = '#2d323e';
export const C_ACCENT_BLUE    = '#3c8cc8';

export const BALL_COLORS = {
    0:  [248, 248, 248],
    1:  [240, 190, 0],
    2:  [20,  50,  210],
    3:  [210, 30,  30],
    4:  [130, 0,   145],
    5:  [240, 110, 0],
    6:  [0,   155, 35],
    7:  [145, 20,  20],
    8:  [18,  18,  18],
    9:  [240, 190, 0],
    10: [20,  50,  210],
    11: [210, 30,  30],
    12: [130, 0,   145],
    13: [240, 110, 0],
    14: [0,   155, 35],
    15: [145, 20,  20],
};

export function rgb(r, g, b) { return `rgb(${r},${g},${b})`; }
export function rgba(r, g, b, a) { return `rgba(${r},${g},${b},${a})`; }
