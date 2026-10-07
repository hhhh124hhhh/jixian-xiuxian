/* 极简修仙 Web 版 · Canvas 渲染（游戏感还原版）
 * 逻辑层：js/game-logic.js（GameLogic.createGame，不动）
 * 渲染层：本文件，原生 Canvas 2D，960×640 逻辑分辨率
 */
"use strict";

/* ================= 布局常量（960×640） ================= */
const W = 960, H = 640;
const L = {
  hudH: 76,                       // 顶部状态条高
  banner: { w: 420, h: 140, y: 86 },          // 标题横幅
  btnR: 56, btnY: 336, btnGap: 172,            // 四圆形按钮
  statusY: 432,                   // 潮汐/渡劫/指引行
  log: { x: 160, y: 476, w: 640, h: 152 },    // 日志面板
  restart: { x: 848, y: 10, w: 100, h: 30 },  // 右上重开
};
const BTN_DEFS = [
  { action: "meditate",    img: "btn_meditate" },
  { action: "consume_pill", img: "btn_pill" },
  { action: "cultivate",   img: "btn_cultivate" },
  { action: "wait",        img: "btn_wait" },
];
BTN_DEFS.forEach((b, i) => {
  b.cx = W / 2 + (i - 1.5) * L.btnGap;
  b.cy = L.btnY;
});

/* ================= 颜色/字体 ================= */
const C = {
  gold: "#e8c56b", cream: "#f5ecd7", dim: "#9db8b0",
  jade: "#7fd1a8", red: "#e05252", hp: "#e06c7a", mp: "#6ca8e0",
  exp: "#e8c56b", dark: "rgba(8,16,16,0.82)",
};
const F = (s, w) => (w ? w + " " : "") + s + 'px "Noto Sans SC","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif';

/* ================= 资源加载 ================= */
const ASSETS = {};
const ASSET_FILES = {
  bg: "assets/bg_main.jpg",
  banner: "assets/banner_title.png",
  panel_log: "assets/panel_log.png",
  btn_meditate: "assets/btn_meditate.png",
  btn_pill: "assets/btn_pill.png",
  btn_cultivate: "assets/btn_cultivate.png",
  btn_wait: "assets/btn_wait.png",
  tide_buff: "assets/icon_tide_buff.png",
  tide_debuff: "assets/icon_tide_debuff.png",
};
function setLoad(pct, text) {
  const fill = document.getElementById("load-fill");
  const status = document.getElementById("load-status");
  if (fill) fill.style.width = pct + "%";
  if (status && text) status.textContent = text;
}
function loadAssets() {
  const keys = Object.keys(ASSET_FILES);
  let done = 0;
  return Promise.all(keys.map(k => new Promise((res, rej) => {
    const img = new Image();
    img.onload = () => { ASSETS[k] = img; done++; setLoad(Math.round(done / keys.length * 90), "加载素材 " + done + "/" + keys.length); res(); };
    img.onerror = rej;
    img.src = ASSET_FILES[k];
  })));
}

/* ================= 游戏逻辑 ================= */
const game = GameLogic.createGame();
let S = game.getState();          // 缓存的最新状态（开始页时角色为空）
let lastLogLen = 0;

// 死亡结算：死因文案 + 墓志铭（墓志铭来自逻辑层 DEATH_EPITAPHS）
const DEATH_EPITAPHS = GameLogic.DEATH_EPITAPHS || {};
const DEATH_CAUSE_LABELS = {
  deviation: "走火而亡", tribulation: "渡劫身陨",
  lifespan: "寿终坐化", demon: "心魔反噬",
};

/* ================= 界面状态机：start | play | gameover ================= */
let screen = "start";
const stats = { expTotal: 0, breakthroughs: 0, tribSuccess: 0, tribFail: 0 };
function resetStats() { stats.expTotal = 0; stats.breakthroughs = 0; stats.tribSuccess = 0; stats.tribFail = 0; }
let over = { win: true, realm: "--", rounds: 0, deathCause: null, maxCombo: 0, epitaph: "" };

/* ================= 隐藏测试钩子：URL 参数 =================
 * ?debug_hp=N        开局设置气血（如 ?debug_hp=5，0 则开局即触发死亡结算）
 * ?debug_lifespan=N  开局设置剩余寿元（如 ?debug_lifespan=3）
 * ?debug_deviation=100 修炼走火率强制 100% 且走火伤害固定 999（必走火暴毙）
 * 仅测试用；无参数时行为完全不变 */
function readDebugParams() {
  const out = {};
  try {
    const q = new URLSearchParams(window.location.search);
    const hp = parseInt(q.get("debug_hp"), 10);
    if (!isNaN(hp) && hp >= 0) out.hp = hp;
    const life = parseInt(q.get("debug_lifespan"), 10);
    if (!isNaN(life) && life >= 0) out.lifespan = life;
    const dev = parseInt(q.get("debug_deviation"), 10);
    if (!isNaN(dev) && dev >= 100) out.deviation = true;
  } catch (e) { /* URL 解析失败就当无参数 */ }
  return out;
}
const DEBUG = readDebugParams();

function newRun() {
  game.init("无名修士", "normal");
  // 隐藏测试钩子：直接覆盖游戏逻辑层的真实状态 game.ch，
  // 不能改 getState() 返回的快照拷贝（它是每次现算的，第一个动作刷新 S 时会丢）
  if (game.ch) {
    if (DEBUG.hp !== undefined) game.ch.hp = Math.min(game.ch.maxHp, DEBUG.hp);
    if (DEBUG.lifespan !== undefined) game.ch.lifespan = DEBUG.lifespan;
    // 隐藏测试钩子：强制走火（game-logic.js 的 doCultivate 会读这个标记）
    if (DEBUG.deviation) game.ch._debugForceDeviation = true;
  }
  S = game.getState();
  lastLogLen = S.log.length;
  resetStats();
  fx.toasts = []; fx.bigText = null; fx.deviation = 0; fx.rings = []; fx.expFloats = [];
  screen = "play";
}

/* ================= 特效 ================= */
const now = () => performance.now();
const easeOut = t => 1 - Math.pow(1 - t, 3);
const fx = {
  rings: [],        // {cx,cy,start}
  expFloats: [],    // {amount,x,y,start}
  deviation: 0,     // start timestamp, 0=inactive
  toasts: [],       // {text,type,start}
  bigText: null,    // {text,color,start,dur}
  press: null,      // {action,start} 按钮按下缩放
};
function toast(text, type) { fx.toasts.push({ text, type: type || "", start: now() }); }
function bigText(text, color, dur) { fx.bigText = { text, color, start: now(), dur: dur || 2000 }; }


/* ================= 音效（Web Audio 程序合成，无外部音频文件） =================
 * AudioContext 必须在用户手势中创建：onTap 里调 initAudio() */
let AC = null;
function initAudio() {
  if (AC) { if (AC.state === "suspended") AC.resume(); return; }
  try { AC = new (window.AudioContext || window.webkitAudioContext)(); }
  catch (e) { console.warn("[sfx] AudioContext 不可用", e); }
}
/* 五声音阶频率（宫商角徵羽），国风味道 */
const PENTA = { C4:261.63, D4:293.66, E4:329.63, G4:392.00, A4:440.00,
                C5:523.25, D5:587.33, E5:659.25, G5:783.99, A5:880.00 };
function tone(freq, t0, dur, type, vol, slideTo) {
  if (!AC) return;
  try {
    const t = AC.currentTime + t0;
    const o = AC.createOscillator(), g = AC.createGain();
    o.type = type || "sine";
    o.frequency.setValueAtTime(freq, t);
    if (slideTo) o.frequency.exponentialRampToValueAtTime(slideTo, t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol || 0.16, t + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(AC.destination);
    o.start(t); o.stop(t + dur + 0.05);
  } catch (e) { /* 忽略单次合成失败 */ }
}
const SFX = {
  click()       { tone(760, 0, 0.07, "square", 0.07); },
  meditate()    { tone(PENTA.E4, 0, 0.5, "sine", 0.13, PENTA.C4);
                  tone(PENTA.G4, 0.08, 0.5, "sine", 0.09, PENTA.E4); },
  pill()        { tone(PENTA.G4, 0, 0.12, "triangle", 0.15);
                  tone(PENTA.C5, 0.1, 0.22, "triangle", 0.15); },
  cultivate()   { tone(PENTA.C4, 0, 0.35, "sine", 0.13, PENTA.G4); },
  wait()        { tone(330, 0, 0.1, "sine", 0.07); },
  breakthrough(){ [PENTA.C4,PENTA.D4,PENTA.E4,PENTA.G4,PENTA.A4,PENTA.C5]
                    .forEach((f,i) => tone(f, i*0.09, 0.3, "triangle", 0.15)); },
  tribWin()     { [PENTA.G4,PENTA.C5,PENTA.D5,PENTA.E5,PENTA.G5]
                    .forEach((f,i) => tone(f, i*0.11, 0.34, "triangle", 0.15)); },
  tribFail()    { tone(220, 0, 0.5, "sawtooth", 0.09, 110); },
  deviation()   { tone(196, 0, 0.4, "sawtooth", 0.11, 185);
                  tone(208, 0.05, 0.4, "sawtooth", 0.09, 220); },
  warn()        { tone(440, 0, 0.12, "square", 0.05); },
  good()        { tone(PENTA.C5, 0, 0.15, "triangle", 0.12);
                  tone(PENTA.E5, 0.09, 0.2, "triangle", 0.12); },
};
const ACTION_SFX = { meditate:"meditate", consume_pill:"pill", cultivate:"cultivate",
                     wait:"wait", restart:"click" };

/* ================= canvas ================= */
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
(function setupDPR() {
  const dpr = Math.min(2, window.devicePixelRatio || 1);
  canvas.width = W * dpr; canvas.height = H * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
})();

function roundRect(x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

/* 文字过长时截断加省略号，保证不超出框 */
function fitText(text, maxW, font) {
  text = String(text);
  ctx.font = font;
  if (ctx.measureText(text).width <= maxW) return text;
  let t = text;
  while (t.length > 1 && ctx.measureText(t + "…").width > maxW) t = t.slice(0, -1);
  return t + "…";
}
function inRect(p, r, pad) {
  pad = pad || 0;   // pad>0 时扩大热区（移动端手指点按更友好），不影响绘制
  return p.x >= r.x - pad && p.x <= r.x + r.w + pad && p.y >= r.y - pad && p.y <= r.y + r.h + pad;
}

/* ================= 绘制 ================= */
function drawBackground() {
  if (ASSETS.bg) ctx.drawImage(ASSETS.bg, 0, 0, W, H);
  else { ctx.fillStyle = "#0a1414"; ctx.fillRect(0, 0, W, H); }
  // 夜色罩：压暗融合（之前验证过的融合方案，canvas 内重做）
  const g = ctx.createRadialGradient(W/2, H*0.42, 80, W/2, H*0.42, 560);
  g.addColorStop(0, "rgba(6,12,12,0.42)");
  g.addColorStop(1, "rgba(6,12,12,0.72)");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);
}

function drawHUD() {
  const c = S.character || {};
  // 顶栏深色底已去掉：文字直接落在水墨背景上，靠阴影保证可读
  const shc = "rgba(0,0,0,0.55)", shb = 6;
  ctx.shadowColor = shc; ctx.shadowBlur = shb;

  // 头像圆（图形不加阴影）
  ctx.shadowBlur = 0;
  ctx.beginPath(); ctx.arc(40, 38, 22, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(127,209,168,0.15)"; ctx.fill();
  ctx.lineWidth = 2; ctx.strokeStyle = C.jade; ctx.stroke();
  ctx.shadowBlur = shb;
  ctx.fillStyle = C.jade; ctx.font = F(22, "bold"); ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText("修", 40, 39);

  // 名字·境界（名字过长截断，不超出框）
  ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
  ctx.fillStyle = C.cream; ctx.font = F(20, "bold");
  const nameTxt = fitText(c.name || "无名修士", 150, F(20, "bold"));
  ctx.fillText(nameTxt, 72, 26);
  const nm = ctx.measureText(nameTxt).width;
  ctx.fillStyle = C.jade; ctx.font = F(16);
  ctx.fillText("· " + fitText(c.realm || "炼气期", 90, F(16)), 72 + nm + 6, 26);

  // 三条状态条
  const bars = [
    ["气血", c.hp, c.max_hp, C.hp],
    ["仙力", c.mp, c.max_mp, C.mp],
    ["经验", c.exp, isFinite(c.exp_threshold) ? c.exp_threshold : 100, C.exp, (c.exp_progress || 0)],
  ];
  bars.forEach((b, i) => {
    const y = 42 + i * 12, bx = 108, bw = 150;
    ctx.fillStyle = C.dim; ctx.font = F(12); ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
    ctx.fillText(b[0], 72, y + 9);
    ctx.shadowBlur = 0;
    ctx.fillStyle = "rgba(255,255,255,0.12)";
    roundRect(bx, y, bw, 9, 4); ctx.fill();
    const pct = b[4] !== undefined ? b[4] / 100 : (b[1] / Math.max(1, b[2]));
    ctx.fillStyle = b[3];
    if (pct > 0) { roundRect(bx, y, Math.max(9, bw * Math.min(1, pct)), 9, 4); ctx.fill(); }
    ctx.shadowBlur = shb;
    ctx.fillStyle = C.dim; ctx.font = F(11); ctx.textAlign = "left";
    ctx.fillText((b[1] || 0) + "/" + b[2], bx + bw + 6, y + 9);
  });

  // 中部：丹药 / 连击 / 配额（全部限宽，不压边框）
  ctx.fillStyle = C.gold; ctx.font = F(15, "bold"); ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
  ctx.fillText(fitText("丹药 " + (c.pills || 0), 130, F(15, "bold")), 300, 30);
  ctx.fillStyle = (S.fire_deviation_turn > 0) ? C.red : C.cream;
  ctx.font = F(14);
  ctx.fillText(fitText(S.breath_combo_status || S.demon_cleared_status || "--", 150, F(14)), 300, 54);
  ctx.fillStyle = C.dim; ctx.font = F(13);
  ctx.fillText(fitText((S.quota && S.quota.text) || "", 170, F(13)), 470, 30);
  ctx.fillText("资质 " + (c.talent || "--"), 470, 54);
  // 寿元（normal/aging/dying 三档配色，大限将至追加警示语）
  const warn = c.lifespan_warn || "normal";
  ctx.fillStyle = warn === "dying" ? C.red : (warn === "aging" ? C.gold : C.dim);
  const lifeTxt = "寿元 " + (c.lifespan || 0) + "/" + (c.lifespan_max || "--") +
    (warn === "dying" ? " · 大限将至" : "");
  ctx.fillText(fitText(lifeTxt, 180, F(13)), 560, 54);

  // 右上：回合 + 重开
  ctx.fillStyle = C.dim; ctx.font = F(14); ctx.textAlign = "right";
  ctx.fillText("第 " + (c.total_actions || 0) + " 回合", 836, 30);
  const r = L.restart;
  const hov = hoverRestart;
  ctx.shadowBlur = 0;
  ctx.fillStyle = hov ? "rgba(232,197,107,0.25)" : "rgba(255,255,255,0.08)";
  roundRect(r.x, r.y, r.w, r.h, 14); ctx.fill();
  ctx.strokeStyle = "rgba(232,197,107,0.4)"; ctx.lineWidth = 1;
  roundRect(r.x, r.y, r.w, r.h, 14); ctx.stroke();
  ctx.shadowBlur = shb;
  ctx.fillStyle = C.gold; ctx.font = F(13); ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText("↻ 重开", r.x + r.w / 2, r.y + r.h / 2 + 1);
  ctx.shadowBlur = 0; ctx.textBaseline = "alphabetic";
}

function drawBanner() {
  const b = L.banner, cx = W / 2;
  if (ASSETS.banner) ctx.drawImage(ASSETS.banner, cx - b.w / 2, b.y, b.w, b.h);
  ctx.fillStyle = C.gold; ctx.font = F(46, "bold");
  ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.shadowColor = "rgba(0,0,0,0.6)"; ctx.shadowBlur = 10;
  ctx.fillText("极 简 修 仙", cx + 4, b.y + b.h / 2 + 2);
  ctx.shadowBlur = 0; ctx.textBaseline = "alphabetic";
}

function drawButtons(t) {
  const btns = S.buttons || [];
  BTN_DEFS.forEach(def => {
    const b = btns.find(x => x.action === def.action);
    const enabled = b && b.enabled && !S.is_game_over;
    const label = (b && b.label) || def.action;
    let scale = 1;
    if (fx.press && fx.press.action === def.action) {
      const pt = (t - fx.press.start) / 140;
      if (pt < 1) scale = 1 - 0.1 * Math.sin(pt * Math.PI);
      else fx.press = null;
    }
    const R = L.btnR * scale;
    const hov = hoverBtn === def.action && enabled;
    ctx.save();
    ctx.globalAlpha = enabled ? 1 : 0.38;
    if (ASSETS[def.img]) {
      const s = R * 2;
      ctx.drawImage(ASSETS[def.img], def.cx - s / 2, def.cy - s / 2, s, s);
    } else {
      ctx.beginPath(); ctx.arc(def.cx, def.cy, R, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(20,35,35,0.9)"; ctx.fill();
    }
    if (hov) {
      ctx.beginPath(); ctx.arc(def.cx, def.cy, R + 3, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(127,209,168,0.7)"; ctx.lineWidth = 2; ctx.stroke();
    }
    // 潮汐共同命运脉冲
    if (tideActive) {
      const p = (Math.sin(t / 250) + 1) / 2;
      ctx.beginPath(); ctx.arc(def.cx, def.cy, R + 4, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(127,209,168," + (0.25 + 0.35 * p).toFixed(2) + ")";
      ctx.lineWidth = 3; ctx.stroke();
    }
    ctx.restore();
    // 标签
    const labelY = def.cy + R + 24;
    ctx.fillStyle = enabled ? C.cream : "rgba(157,184,176,0.6)";
    ctx.font = F(16, "bold"); ctx.textAlign = "center";
    ctx.fillText(label, def.cx, labelY);
    const labelW = ctx.measureText(label).width;
    // 修炼按钮标出走火风险（走火率 >20% 标红）
    // 放在标签右侧而非下方：按钮下方 392~422 只有一行空间，
    // 再加一行会压到「灵气潮汐」那行（同基线，潮汐文案跨 386~575）。
    if (def.action === "cultivate") {
      const rate = (S.fire_rate || 0) * 100;
      const risk = "走火 " + Math.round(rate) + "% · -" + (S.deviation_damage || 0);
      const next = BTN_DEFS[BTN_DEFS.indexOf(def) + 1];
      const limit = next ? next.cx - 34 : W - 20;   // 不越过下一个按钮的标签
      const startX = Math.min(def.cx + labelW / 2 + 10, limit - 64);
      ctx.font = F(12);
      ctx.fillStyle = rate > 20 ? C.red : C.dim;
      ctx.textAlign = "left";
      ctx.fillText(fitText(risk, limit - startX, F(12)), startX, labelY);
    }
  });
}

function drawStatus() {
  const y = L.statusY;
  ctx.textAlign = "center"; ctx.font = F(14);
  ctx.shadowColor = "rgba(0,0,0,0.55)"; ctx.shadowBlur = 6;
  // 潮汐
  const tide = S.tide_effect;
  let tx = W / 2;
  if (tide) {
    const icon = tide.tone === "buff" ? ASSETS.tide_buff : ASSETS.tide_debuff;
    const label = "灵气潮汐：" + (tide.label || tide.preview || "有感应");
    const wdt = ctx.measureText(label).width;
    if (icon) ctx.drawImage(icon, tx - wdt / 2 - 30, y - 16, 24, 24);
    ctx.fillStyle = tide.tone === "buff" ? C.jade : (tide.tone === "debuff" ? C.red : C.gold);
    ctx.fillText(label, tx, y + 4);
  } else {
    ctx.fillStyle = C.dim;
    ctx.fillText("灵气潮汐：平静", tx, y + 4);
  }
  // 渡劫 + 指引
  const trib = S.tribulation || {};
  ctx.font = F(13);
  ctx.fillStyle = trib.ready ? C.gold : C.dim;
  ctx.fillText(trib.ready ? ("渡劫：可渡（成功率 " + trib.rate + "%）") : "渡劫：时机未到", W / 2 - 220, y + 28);
  ctx.fillStyle = C.dim;
  const reco = "指引：" + (S.recommendation || "--");
  ctx.fillText(reco.length > 26 ? reco.slice(0, 26) + "…" : reco, W / 2 + 200, y + 28);
  ctx.shadowBlur = 0;
}

function logColor(t) {
  if (/\[错误\]/.test(t)) return C.red;
  if (/潮汐|灵气/.test(t)) return C.jade;
  if (/走火|失败|心魔|终结|身死|坐化|耗尽/.test(t)) return "#e08a8a";
  if (/突破|成功|获得|飞升/.test(t)) return C.gold;
  return "#cfe3da";
}
function drawLog() {
  const lg = L.log;
  if (ASSETS.panel_log) ctx.drawImage(ASSETS.panel_log, lg.x, lg.y, lg.w, lg.h);
  else { ctx.fillStyle = C.dark; roundRect(lg.x, lg.y, lg.w, lg.h, 8); ctx.fill(); }
  ctx.fillStyle = C.gold; ctx.font = F(15, "bold"); ctx.textAlign = "left";
  ctx.fillText("— 修仙日志 —", lg.x + 28, lg.y - 8);
  const logs = S.log || [];
  const lineH = 21, maxLines = 5, padX = 30, topY = lg.y + 34;
  // 文字安全区底：半透明深色垫在文字行下面，防底图山水图案压住日志字
  ctx.fillStyle = "rgba(4,10,10,0.62)";
  roundRect(lg.x + 14, topY - 20, lg.w - 28, maxLines * lineH + 10, 8); ctx.fill();
  const start = Math.max(0, logs.length - maxLines);
  ctx.font = F(14);
  ctx.shadowColor = "rgba(0,0,0,0.6)"; ctx.shadowBlur = 4;
  for (let i = 0; i < Math.min(maxLines, logs.length); i++) {
    const t = logs[start + i];
    ctx.fillStyle = logColor(t);
    let txt = t;
    while (ctx.measureText(txt).width > lg.w - padX * 2 && txt.length > 4) txt = txt.slice(0, -2);
    if (txt !== t) txt += "…";
    ctx.fillText(txt, lg.x + padX, topY + i * lineH);
  }
  ctx.shadowBlur = 0;
}

/* ---- 特效绘制 ---- */
function drawEffects(t) {
  // 突破圆环
  fx.rings = fx.rings.filter(r => t - r.start < 900);
  fx.rings.forEach(r => {
    const p = (t - r.start) / 900, rad = 200 * easeOut(p), a = 0.85 * (1 - p);
    if (rad <= 2 || a <= 0) return;
    ctx.beginPath(); ctx.arc(r.cx, r.cy, rad, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(127,209,168," + a.toFixed(2) + ")"; ctx.lineWidth = 5; ctx.stroke();
    ctx.beginPath(); ctx.arc(r.cx, r.cy, rad * 0.7, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(127,209,168," + (a / 3).toFixed(2) + ")"; ctx.lineWidth = 2; ctx.stroke();
  });
  // 经验上浮
  fx.expFloats = fx.expFloats.filter(e => t - e.start < 900);
  fx.expFloats.forEach(e => {
    const p = (t - e.start) / 900, dy = 44 * easeOut(p), a = 1 - p;
    ctx.globalAlpha = Math.max(0, a);
    ctx.fillStyle = "#fff0b4"; ctx.font = F(20, "bold"); ctx.textAlign = "center";
    ctx.fillText("+" + e.amount, e.x, e.y - dy);
    ctx.globalAlpha = 1;
  });
  // 走火红脉冲
  if (fx.deviation) {
    const el = t - fx.deviation;
    if (el > 2400) fx.deviation = 0;
    else {
      const pulse = Math.abs(Math.sin(el / 2400 * Math.PI * 2 * 2));
      const a = 0.35 * pulse * (1 - el / 2400 * 0.5);
      ctx.fillStyle = "rgba(220,40,40," + a.toFixed(2) + ")";
      const e2 = 16;
      ctx.fillRect(0, 0, W, e2); ctx.fillRect(0, H - e2, W, e2);
      ctx.fillRect(0, 0, e2, H); ctx.fillRect(W - e2, 0, e2, H);
    }
  }
  // 中央大字
  if (fx.bigText) {
    const el = t - fx.bigText.start;
    if (el > fx.bigText.dur) fx.bigText = null;
    else {
      const a = el < 200 ? el / 200 : (el > fx.bigText.dur - 400 ? (fx.bigText.dur - el) / 400 : 1);
      ctx.globalAlpha = Math.max(0, Math.min(1, a));
      ctx.fillStyle = fx.bigText.color; ctx.font = F(54, "bold"); ctx.textAlign = "center";
      ctx.shadowColor = "rgba(0,0,0,0.8)"; ctx.shadowBlur = 18;
      ctx.fillText(fx.bigText.text, W / 2, H / 2 - 40);
      ctx.shadowBlur = 0; ctx.globalAlpha = 1;
    }
  }
  // Toast
  fx.toasts = fx.toasts.filter(x => t - x.start < 3000);
  fx.toasts.forEach((x, i) => {
    const el = t - x.start;
    const a = el < 200 ? el / 200 : (el > 2600 ? (3000 - el) / 400 : 1);
    if (a <= 0) return;
    ctx.globalAlpha = Math.max(0, Math.min(1, a));
    ctx.font = F(16, "bold");
    const wdt = Math.min(560, ctx.measureText(x.text).width + 56);
    const bx = W / 2 - wdt / 2, by = 84 + i * 44;
    ctx.fillStyle = "rgba(10,20,20,0.88)";
    roundRect(bx, by, wdt, 36, 8); ctx.fill();
    ctx.strokeStyle = x.type === "warn" ? "rgba(224,82,82,0.8)" : "rgba(127,209,168,0.8)";
    ctx.lineWidth = 1.5; roundRect(bx, by, wdt, 36, 8); ctx.stroke();
    ctx.fillStyle = x.type === "warn" ? "#f0a0a0" : C.cream;
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(x.text, W / 2, by + 19);
    ctx.textBaseline = "alphabetic"; ctx.globalAlpha = 1;
  });
}

/* ================= 开始页 ================= */
const START_BTN = { x: W / 2 - 110, y: 408, w: 220, h: 58 };
function drawStart(t) {
  const bw = 460, bh = 154, bx = W / 2 - bw / 2, by = 118;
  if (ASSETS.banner) ctx.drawImage(ASSETS.banner, bx, by, bw, bh);
  ctx.fillStyle = C.gold; ctx.font = F(64, "bold");
  ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.shadowColor = "rgba(0,0,0,0.7)"; ctx.shadowBlur = 14;
  ctx.fillText("极 简 修 仙", W / 2 + 4, by + bh / 2 + 4);
  ctx.shadowBlur = 0; ctx.textBaseline = "alphabetic";
  ctx.shadowColor = "rgba(0,0,0,0.55)"; ctx.shadowBlur = 6;
  ctx.fillStyle = C.cream; ctx.font = F(22);
  ctx.textAlign = "center";
  ctx.fillText("吐纳炼气 · 渡劫飞升", W / 2, 332);
  ctx.fillStyle = C.dim; ctx.font = F(16);
  ctx.fillText("点击开始，随机资质，入道修行", W / 2, 364);
  ctx.shadowBlur = 0;
  const b = START_BTN, hov = hoverStart;
  const pulse = 0.5 + 0.5 * Math.sin(t / 600);
  ctx.fillStyle = hov ? "rgba(127,209,168,0.28)" : "rgba(20,35,35,0.85)";
  roundRect(b.x, b.y, b.w, b.h, 12); ctx.fill();
  ctx.strokeStyle = "rgba(127,209,168," + (hov ? 1 : (0.6 + 0.3 * pulse)).toFixed(2) + ")";
  ctx.lineWidth = 2; roundRect(b.x, b.y, b.w, b.h, 12); ctx.stroke();
  ctx.fillStyle = C.gold; ctx.font = F(26, "bold"); ctx.textBaseline = "middle";
  ctx.fillText("开 始 游 戏", W / 2, b.y + b.h / 2 + 1);
  ctx.textBaseline = "alphabetic";
}

/* ================= 结算页 ================= */
const AGAIN_BTN = { x: W / 2 - 240, y: 436, w: 210, h: 54 };
const TITLE_BTN = { x: W / 2 + 30, y: 436, w: 210, h: 54 };
function drawBtn(r, label, hov) {
  ctx.fillStyle = hov ? "rgba(127,209,168,0.25)" : "rgba(20,35,35,0.9)";
  roundRect(r.x, r.y, r.w, r.h, 10); ctx.fill();
  ctx.strokeStyle = hov ? C.jade : "rgba(127,209,168,0.55)";
  ctx.lineWidth = 2; roundRect(r.x, r.y, r.w, r.h, 10); ctx.stroke();
  ctx.fillStyle = C.cream; ctx.font = F(20, "bold");
  ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText(label, r.x + r.w / 2, r.y + r.h / 2 + 1);
  ctx.textBaseline = "alphabetic";
}
function drawSettlement() {
  ctx.fillStyle = "rgba(4,8,8,0.66)";
  ctx.fillRect(0, 0, W, H);
  const px = W / 2 - 270, py = 118, pw = 540, ph = 404;
  ctx.fillStyle = "rgba(10,20,20,0.95)";
  roundRect(px, py, pw, ph, 14); ctx.fill();
  ctx.strokeStyle = over.win ? "rgba(127,209,168,0.6)" : "rgba(224,138,138,0.55)";
  ctx.lineWidth = 2;
  roundRect(px, py, pw, ph, 14); ctx.stroke();
  ctx.textAlign = "center";
  ctx.fillStyle = over.win ? C.gold : "#e08a8a";
  ctx.font = F(44, "bold");
  ctx.shadowColor = "rgba(0,0,0,0.8)"; ctx.shadowBlur = 14;
  ctx.fillText(over.win ? "羽 化 飞 升" : "身 死 道 消", W / 2, py + 72);
  ctx.shadowBlur = 0;
  const rows = over.win ? [
    ["最终境界", over.realm],
    ["修炼回合", over.rounds + ""],
    ["累计经验", stats.expTotal + ""],
    ["突破次数", stats.breakthroughs + ""],
    ["渡劫", "成功 " + stats.tribSuccess + " · 失败 " + stats.tribFail],
  ] : [
    ["最终境界", over.realm],
    ["修行回合", over.rounds + ""],
    ["最高连击", "×" + (over.maxCombo || 0)],
    ["死因", DEATH_CAUSE_LABELS[over.deathCause] || DEATH_CAUSE_LABELS.deviation],
  ];
  // 死亡时行数少、留一行空间给墓志铭
  const rowStart = py + (over.win ? 140 : 124);
  ctx.font = F(20);
  rows.forEach((r2, i) => {
    const y = rowStart + i * 38;
    ctx.fillStyle = C.dim; ctx.textAlign = "right"; ctx.textBaseline = "alphabetic";
    ctx.fillText(r2[0], W / 2 - 20, y);
    ctx.fillStyle = over.win ? C.cream : "#e8c4c4"; ctx.textAlign = "left";
    ctx.fillText(fitText(r2[1], 220, F(20)), W / 2 + 20, y);
  });
  if (!over.win && over.epitaph) {
    ctx.fillStyle = C.gold;
    ctx.font = "italic " + F(16);
    ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
    ctx.fillText(over.epitaph, W / 2, py + 286);
  }
  drawBtn(AGAIN_BTN, over.win ? "再来一局" : "重新入道", hoverAgain);
  drawBtn(TITLE_BTN, "返回标题", hoverTitle);
}

/* ================= 主循环 ================= */
let tideActive = false, hoverBtn = null, hoverRestart = false;
let hoverStart = false, hoverAgain = false, hoverTitle = false;

function render(t) {
  ctx.clearRect(0, 0, W, H);
  if (screen === "start") {
    drawBackground();
    drawStart(t || 0);
    return;
  }
  tideActive = !!(S.tide_effect && S.tide_effect.tone);
  drawBackground();
  drawHUD();
  drawBanner();
  drawButtons(t);
  drawStatus();
  drawLog();
  drawEffects(t);
  if (screen === "gameover") drawSettlement();
}
function loop(t) { render(t || 0); requestAnimationFrame(loop); }

/* ================= 输入 ================= */
function toGame(e) {
  const r = canvas.getBoundingClientRect();
  return {
    x: (e.clientX - r.left) * (W / r.width),
    y: (e.clientY - r.top) * (H / r.height),
  };
}
function hitButton(p) {
  const R = L.btnR + 12;   // 命中半径比绘制半径大一圈，手指好点
  for (const def of BTN_DEFS) {
    const dx = p.x - def.cx, dy = p.y - def.cy;
    if (dx * dx + dy * dy <= R * R) return def.action;
  }
  return null;
}
function doGameAction(action) {
  try {
    const r = game.doAction(action);
    if (!r.success) {
      toast(r.message, "warn");
      SFX.warn();
    } else {
      fx.press = { action, start: now() };
      const sfx = ACTION_SFX[action];
      if (sfx && SFX[sfx]) SFX[sfx]();
    }
    const ef = r.effects || {};
    if (ef.level_up) {
      SFX.breakthrough();
      fx.rings.push({ cx: W / 2, cy: L.btnY, start: now() });
      bigText("突破 · " + (ef.new_level || ""), C.jade, 2000);
      toast("突破至 " + (ef.new_level || "") + "！", "good");
    }
    if (ef.fire_deviation) {
      SFX.deviation();
      fx.deviation = now();
      bigText("走火入魔", C.red, 2200);
      toast("走火入魔！气息紊乱 3 回合", "warn");
    }
    if (ef.exp_gain > 0) fx.expFloats.push({ amount: ef.exp_gain, x: W / 2, y: L.btnY - 70, start: now() });
    if (ef.demon_cleared) { SFX.good(); bigText("破心魔", C.jade, 1800); toast("心魔已破！修炼加速", "good"); }
    if (ef.tribulation) {
      const ok = !!ef.tribulation_success;
      if (ok) SFX.tribWin(); else SFX.tribFail();
      bigText(ok ? "渡劫成功" : "渡劫失败", ok ? C.gold : C.red, 2200);
      toast(ok ? "渡劫成功！配额已刷新" : "渡劫失败……", ok ? "good" : "warn");
    }
    if (ef.restart) { fx.toasts = []; fx.bigText = null; fx.deviation = 0; lastLogLen = 0; resetStats(); }
    S = game.getState();
    if (!ef.restart) {
      if (ef.exp_gain > 0) stats.expTotal += ef.exp_gain;
      if (ef.level_up) stats.breakthroughs++;
      if (ef.tribulation) { if (ef.tribulation_success) stats.tribSuccess++; else stats.tribFail++; }
      if (S.is_game_over && screen === "play") {
        const c = S.character || {};
        if (c.realm === "飞升") {
          over = { win: true, realm: c.realm || "--", rounds: c.total_actions || 0 };
          screen = "gameover";
        } else if (!c.alive || c.deathCause) {
          // 气血耗尽 / 寿元耗尽：寿终坐化时气血仍在，故一并看 deathCause
          const cause = c.deathCause || "deviation";
          over = { win: false, realm: c.realm || "--", rounds: c.total_actions || 0,
                   deathCause: cause, maxCombo: c.max_combo || 0,
                   epitaph: DEATH_EPITAPHS[cause] || DEATH_EPITAPHS.deviation || "" };
          screen = "gameover";
        }
      }
    }
  } catch (e) { console.error("[canvas] 动作失败", e); }
}
/* pointerdown 统一处理鼠标/触摸/手写笔：手机上无 click 延迟，桌面端行为不变。
 * toGame() 已用 getBoundingClientRect 换算，CSS 缩放后坐标依然准确。 */
function onTap(e) {
  initAudio();   // 首次用户点击时初始化 AudioContext（手机自动播放策略要求）
  if (e.pointerType === "touch") { hoverBtn = null; hoverRestart = false; }
  const p = toGame(e);
  if (screen === "start") {
    if (inRect(p, START_BTN, 14)) { SFX.click(); newRun(); }
    return;
  }
  if (screen === "gameover") {
    if (inRect(p, AGAIN_BTN, 14)) { SFX.click(); newRun(); }
    else if (inRect(p, TITLE_BTN, 14)) { SFX.click(); screen = "start"; }
    return;
  }
  const r = L.restart;
  if (inRect(p, r, 10)) {
    doGameAction("restart");
    return;
  }
  const a = hitButton(p);
  if (!a) return;
  const b = (S.buttons || []).find(x => x.action === a);
  if (!b || !b.enabled || S.is_game_over) return;
  doGameAction(a);
}
canvas.addEventListener("pointerdown", onTap);
canvas.addEventListener("mousemove", e => {
  const p = toGame(e);
  hoverStart = hoverAgain = hoverTitle = false;
  hoverBtn = null; hoverRestart = false;
  if (screen === "start") {
    hoverStart = inRect(p, START_BTN);
  } else if (screen === "gameover") {
    hoverAgain = inRect(p, AGAIN_BTN);
    hoverTitle = inRect(p, TITLE_BTN);
  } else {
    const r = L.restart;
    hoverRestart = inRect(p, r);
    const a = hitButton(p);
    const b = a && (S.buttons || []).find(x => x.action === a);
    hoverBtn = (b && b.enabled && !S.is_game_over) ? a : null;
  }
  canvas.style.cursor = (hoverStart || hoverAgain || hoverTitle || hoverRestart || hoverBtn) ? "pointer" : "default";
});
canvas.addEventListener("contextmenu", e => e.preventDefault());  // 移动端禁长按菜单

/* ================= 启动 ================= */
loadAssets()
  .then(() => {
    setLoad(100, "完成");
    S = game.getState();
    lastLogLen = S.log.length;
    document.getElementById("loading").classList.add("hide");
    requestAnimationFrame(loop);
    console.log("[canvas] 启动完成");
  })
  .catch(e => {
    console.error("[canvas] 素材加载失败", e);
    setLoad(100, "素材加载失败，请刷新重试");
  });
