.pragma library

// Line-art drawings of the Hardware page, ported from
// reference/hardware-mock.html. Each one returns { w, h, shapes }: the size
// of its own coordinate space and the primitives drawn in it, which LineArt
// strokes. `thin` marks the faint detail lines.

function point(cx, cy, r, deg) {
    const a = deg * Math.PI / 180;
    return (cx + r * Math.cos(a)).toFixed(2) + "," + (cy + r * Math.sin(a)).toFixed(2);
}

function path(d, thin) {
    return { "kind": "path", "d": d, "thin": thin === true };
}

function rect(x, y, w, h, r, thin) {
    return { "kind": "rect", "x": x, "y": y, "w": w, "h": h, "r": r || 0, "thin": thin === true };
}

function circle(cx, cy, r, thin) {
    return { "kind": "circle", "cx": cx, "cy": cy, "r": r, "thin": thin === true };
}

// Centred on x; shrunk to fit `maxWidth` if longer.
function label(x, y, size, text, maxWidth) {
    return { "kind": "text", "x": x, "y": y, "size": size, "text": text, "maxWidth": maxWidth };
}

function mirrorX(d, w) {
    return d.replace(/(-?[\d.]+),(-?[\d.]+)/g, (_, x, y) => (w - x) + "," + y);
}

// The two text lines come from the CPU model, never a drawn logo.
function cpu(top, bottom) {
    const s = [rect(18, 18, 84, 84, 8), rect(26, 26, 68, 68, 4)];
    for (let i = 0; i < 10; i++) {
        const p = 25.5 + i * 7.6;
        s.push(rect(p, 8, 3, 10, 0.5), rect(p, 102, 3, 10, 0.5),
               rect(8, p, 10, 3, 0.5), rect(102, p, 10, 3, 0.5));
    }
    s.push(path("M31,89 L37,89 L31,83 Z"));
    if (top)
        s.push(label(60, 55, 9, top, 60));
    if (bottom)
        s.push(label(60, 71, 13, bottom, 60));
    return { "w": 120, "h": 120, "shapes": s };
}

// Rim, hub and eleven swept blades from hub to rim.
function fan(s, cx, cy) {
    s.push(circle(cx, cy, 46), circle(cx, cy, 12.5));
    for (let k = 0; k < 11; k++) {
        const a = k * 360 / 11;
        s.push(path("M" + point(cx, cy, 12.5, a)
                    + " Q" + point(cx, cy, 31, a + 4) + " " + point(cx, cy, 44.5, a + 56)
                    + " Q" + point(cx, cy, 31, a + 36) + " " + point(cx, cy, 12.5, a + 29)));
    }
}

function gpu() {
    const s = [];
    // Bracket: hooked top, port slits, tongue at the bottom.
    s.push(path("M13,25 H30 V128 M13,25 V28 H24 V140 L26,144 H30 V128"));
    for (const y of [42, 58, 74, 90, 106])
        s.push(rect(26, y, 2.5, 9, 0.5));
    // Shroud: square left corners, chamfered right corners.
    s.push(path("M33,16 H274 L288,32 V113 L274,128 H33 Z"));
    // Recess on the top edge with its slot.
    s.push(path("M118,16 L132,25 H190 L204,16"));
    s.push(rect(136, 19.5, 62, 2.5, 1.25));
    fan(s, 100, 72);
    fan(s, 221, 72);
    // Small tab, edge connector with its key, end tab.
    s.push(path("M60,128 V134 H66 V128"));
    s.push(path("M70,128 V139.5 H82 V134 H85 V139.5 H156 V134 H162 V132.5 H168 V135 H174 V128"));
    s.push(path("M88,137 H153", true));
    return { "w": 300, "h": 150, "shapes": s };
}

function ram() {
    const s = [];
    // PCB with side notches, key notch and gold fingers; only the parts the
    // heatsink leaves visible (its sides and the strip below).
    s.push(path("M14,30 H6 V36 H10 V44 H6 V82 H164 V76 H170 V82 H294 V44 H290 V36 H294 V30 H286"));
    for (let x = 12; x < 289; x += 2.4) {
        if (x < 162 || x > 172)
            s.push(path("M" + x.toFixed(1) + ",74 L" + x.toFixed(1) + ",80", true));
    }
    s.push(circle(10, 70, 2), circle(290, 70, 2));
    // Heatsink: raised ends, centre panel, diagonal fins.
    s.push(path("M14,26 L24,12 L62,12 L70,20 L112,20 L120,26 L180,26 L188,20 L230,20 L238,12 L276,12 L286,26 L286,66 L14,66 Z"));
    const edge = "M20,28 L28,17 L60,17 L66,24";
    s.push(path(edge, true), path(mirrorX(edge, 300), true));
    s.push(path("M84,36 L216,36 L222,42 L204,60 L96,60 L78,42 Z"));
    s.push(path("M88,40 L212,40", true));
    for (const d of ["M22,30 L30,30 L62,62 L54,62 Z", "M36,30 L44,30 L76,62 L68,62 Z"])
        s.push(path(d), path(mirrorX(d, 300)));
    return { "w": 300, "h": 90, "shapes": s };
}

function nvme() {
    const s = [];
    // M.2 2280 board, screw notch on the left, M-key connector on the right.
    s.push(path("M12,14 H282 V66 H12 V46 A6,6 0 0 0 12,34 Z"));
    s.push(path("M282,16 H292 V28 H287 V33 H292 V64 H282"));
    for (let y = 18; y < 63; y += 2.5) {
        if (y < 27 || y > 34)
            s.push(path("M284," + y + " L291," + y, true));
    }
    // NAND packages, controller, DRAM.
    s.push(rect(36, 20, 62, 40, 2), rect(40, 24, 54, 32, 1, true));
    s.push(rect(106, 20, 62, 40, 2), rect(110, 24, 54, 32, 1, true));
    s.push(rect(194, 22, 36, 36, 2), rect(201, 29, 22, 22, 1, true));
    s.push(rect(240, 26, 24, 28, 1.5));
    // Small parts.
    for (const [x, y] of [[24, 20], [24, 28], [24, 52], [178, 22], [178, 30], [178, 48], [184, 54], [270, 22], [270, 56]])
        s.push(rect(x, y, 5, 3, 0.5, true));
    return { "w": 300, "h": 80, "shapes": s };
}

// SATA data (short) and power (long) plugs on the left edge.
function sataPlugs(s) {
    for (const [y, h] of [[22, 20], [46, 32]]) {
        s.push(rect(4, y, 6, h, 0.5));
        for (let p = y + 2.5; p < y + h - 1; p += 2.5)
            s.push(path("M5," + p + " L9," + p, true));
    }
}

// 3.5" hard disk, cover off: platter, read arm, magnet and board blocks.
function hdd() {
    const s = [path("M15,4 H149 L154,9 V91 L149,96 H15 L10,91 V9 Z")];
    sataPlugs(s);
    for (const [x, y] of [[19, 13], [145, 13], [19, 87], [145, 87]])
        s.push(circle(x, y, 3));
    // Platter and spindle.
    s.push(circle(110, 50, 40), circle(110, 50, 37, true));
    s.push(circle(110, 50, 10), circle(110, 50, 3));
    // Magnet above the arm pivot, board cover below it.
    s.push(path("M22,12 H52 L56,18 V24 L48,28 H40 L34,34 V50 H22 Z"));
    s.push(path("M22,58 H34 L38,62 H46 L54,74 V88 H22 Z"));
    s.push(circle(28, 18, 1.5, true), circle(46, 17, 1.5, true), circle(48, 83, 1.5, true));
    // Arm: pivot, tapered beam, head over the platter.
    s.push(circle(60, 38, 7), circle(60, 38, 3, true));
    s.push(path("M63.6,45.8 L87.2,67.4 L89.4,65.2 L67.8,41.6 Z"));
    s.push(path("M86.5,68.1 L90.1,64.5 L93.6,68.0 L90.0,71.6 Z"));
    return { "w": 156, "h": 100, "shapes": s };
}

// 2.5" SATA SSD, cover off: controller, DRAM, two rows of NAND.
function ssd() {
    const s = [rect(10, 4, 132, 92, 4)];
    sataPlugs(s);
    for (const [x, y] of [[18, 12], [134, 12], [18, 88], [134, 88]])
        s.push(circle(x, y, 3));
    // Case rails along the long edges.
    s.push(path("M38,4 L42,8 H110 L114,4", true), path("M38,96 L42,92 H110 L114,96", true));
    s.push(rect(30, 38, 22, 22, 1.5), rect(34, 42, 14, 14, 1, true));
    s.push(rect(30, 66, 14, 18, 1), rect(40, 16, 12, 8, 1));
    for (const x of [62, 88, 114]) {
        for (const y of [20, 54]) {
            s.push(rect(x, y, 22, 26, 1));
            s.push(circle(x + 3, y + 3, 0.8, true));
        }
    }
    for (const [x, y] of [[22, 22], [22, 30], [22, 64], [22, 72], [54, 66], [54, 74], [50, 86]])
        s.push(rect(x, y, 4, 2.5, 0.5, true));
    return { "w": 146, "h": 100, "shapes": s };
}

function board() {
    const s = [rect(2, 2, 116, 116, 1.5)];
    for (const [x, y] of [[8, 8], [112, 8], [8, 112], [112, 112], [70, 112]])
        s.push(circle(x, y, 2, true));
    // Rear I/O.
    s.push(rect(4, 14, 13, 48, 1));
    for (let y = 18; y < 58; y += 8)
        s.push(rect(6.5, y, 8, 5, 0.5, true));
    // VRM heatsinks around the socket.
    s.push(path("M22,6 H72 V14 H30 V54 H22 Z"));
    for (let x = 34; x < 70; x += 4)
        s.push(path("M" + x + ",7 L" + x + ",13", true));
    for (let y = 18; y < 52; y += 4)
        s.push(path("M23," + y + " L29," + y, true));
    // CPU socket.
    s.push(rect(36, 20, 30, 30, 1), rect(40, 24, 22, 22, 0.5, true), path("M41,45 L45,45 L41,41 Z", true));
    // Four DIMM slots.
    for (const x of [78, 84, 90, 96])
        s.push(rect(x, 6, 4, 56, 0.5), path("M" + x + ",9 H" + (x + 4) + " M" + x + ",59 H" + (x + 4), true));
    // 24-pin power.
    s.push(rect(106, 20, 9, 30, 0.5));
    for (let y = 23; y < 49; y += 3)
        s.push(path("M107," + y + " H114", true));
    // PCIe slots and M.2.
    s.push(rect(10, 72, 62, 5, 0.5), rect(10, 86, 20, 4, 0.5), rect(10, 98, 62, 5, 0.5));
    s.push(rect(36, 84, 34, 7, 0.5, true));
    // Chipset heatsink with fins.
    s.push(rect(80, 78, 24, 24, 1));
    for (let i = 4; i < 44; i += 5) {
        const a = Math.max(0, i - 24);
        const b = Math.min(i, 24);
        s.push(path("M" + (80 + a) + "," + (78 + b) + " L" + (80 + b) + "," + (78 + a), true));
    }
    // SATA ports, CMOS battery, headers.
    for (const y of [70, 78, 86, 94])
        s.push(rect(108, y, 7, 5, 0.5, true));
    s.push(circle(54, 111, 4.5), circle(54, 111, 2.5, true));
    s.push(rect(80, 108, 20, 4, 0.5, true), rect(22, 108, 18, 4, 0.5, true));
    return { "w": 120, "h": 120, "shapes": s };
}

function monitor() {
    return {
        "w": 160,
        "h": 110,
        "shapes": [rect(4, 4, 152, 84, 3), rect(9, 9, 142, 72, 1, true),
                   path("M72,88 L69,100 H91 L88,88"), rect(50, 100, 60, 5, 2.5)]
    };
}

// A memory slot: a stick with its chips when populated, the bare slot
// otherwise.
function slot(populated) {
    const s = [rect(1, 4, 78, 14, 1)];
    if (populated) {
        s.push(rect(1, 0, 78, 18, 1));
        for (let i = 0; i < 8; i++)
            s.push(rect(5 + i * 9 + (i > 3 ? 3 : 0), 4, 6, 9, 0.5, true));
    } else {
        s.push(rect(5, 8, 70, 6, 0.5, true));
    }
    return { "w": 80, "h": 20, "shapes": s };
}
