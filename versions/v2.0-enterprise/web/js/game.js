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
game.init("无名修士", "normal");
let S = game.getState();          // 缓存的最新状态
let lastLogLen = S.log.length;

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
  ctx.fillStyle = C.dark;
  ctx.fillRect(0, 0, W, L.hudH);
  ctx.fillStyle = "rgba(127,209,168,0.25)";
  ctx.fillRect(0, L.hudH - 1, W, 1);

  // 头像圆
  ctx.beginPath(); ctx.arc(40, 38, 22, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(127,209,168,0.15)"; ctx.fill();
  ctx.lineWidth = 2; ctx.strokeStyle = C.jade; ctx.stroke();
  ctx.fillStyle = C.jade; ctx.font = F(22, "bold"); ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText("修", 40, 39);

  // 名字·境界
  ctx.textAlign = "left";
  ctx.fillStyle = C.cream; ctx.font = F(20, "bold");
  ctx.fillText(c.name || "无名修士", 72, 26);
  const nm = ctx.measureText(c.name || "无名修士").width;
  ctx.fillStyle = C.jade; ctx.font = F(16);
  ctx.fillText("· " + (c.realm || "炼气期"), 72 + nm + 6, 26);

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
    ctx.fillStyle = "rgba(255,255,255,0.12)";
    roundRect(bx, y, bw, 9, 4); ctx.fill();
    const pct = b[4] !== undefined ? b[4] / 100 : (b[1] / Math.max(1, b[2]));
    ctx.fillStyle = b[3];
    if (pct > 0) { roundRect(bx, y, Math.max(9, bw * Math.min(1, pct)), 9, 4); ctx.fill(); }
    ctx.fillStyle = C.dim; ctx.font = F(11); ctx.textAlign = "left";
    ctx.fillText((b[1] || 0) + "/" + b[2], bx + bw + 6, y + 9);
  });

  // 中部：丹药 / 连击 / 配额
  ctx.fillStyle = C.gold; ctx.font = F(15, "bold"); ctx.textAlign = "left";
  ctx.fillText("丹药 " + (c.pills || 0), 300, 30);
  ctx.fillStyle = (S.fire_deviation_turn > 0) ? C.red : C.cream;
  ctx.font = F(14);
  ctx.fillText(S.breath_combo_status || S.demon_cleared_status || "--", 300, 54);
  ctx.fillStyle = C.dim; ctx.font = F(13);
  ctx.fillText((S.quota && S.quota.text) || "", 470, 30);
  ctx.fillText("资质 " + (c.talent || "--"), 470, 54);

  // 右上：回合 + 重开
  ctx.fillStyle = C.dim; ctx.font = F(14); ctx.textAlign = "right";
  ctx.fillText("第 " + (c.total_actions || 0) + " 回合", 836, 30);
  const r = L.restart;
  const hov = hoverRestart;
  ctx.fillStyle = hov ? "rgba(232,197,107,0.25)" : "rgba(255,255,255,0.08)";
  roundRect(r.x, r.y, r.w, r.h, 14); ctx.fill();
  ctx.strokeStyle = "rgba(232,197,107,0.4)"; ctx.lineWidth = 1;
  roundRect(r.x, r.y, r.w, r.h, 14); ctx.stroke();
  ctx.fillStyle = C.gold; ctx.font = F(13); ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText("↻ 重开", r.x + r.w / 2, r.y + r.h / 2 + 1);
  ctx.textBaseline = "alphabetic";
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
    ctx.fillStyle = enabled ? C.cream : "rgba(157,184,176,0.6)";
    ctx.font = F(16, "bold"); ctx.textAlign = "center";
    ctx.fillText(label, def.cx, def.cy + R + 24);
  });
}

function drawStatus() {
  const y = L.statusY;
  ctx.textAlign = "center"; ctx.font = F(14);
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
}

function logColor(t) {
  if (/\[错误\]/.test(t)) return C.red;
  if (/潮汐|灵气/.test(t)) return C.jade;
  if (/走火|失败|心魔|终结/.test(t)) return "#e08a8a";
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
  const start = Math.max(0, logs.length - maxLines);
  ctx.font = F(14);
  for (let i = 0; i < Math.min(maxLines, logs.length); i++) {
    const t = logs[start + i];
    ctx.fillStyle = logColor(t);
    let txt = t;
    while (ctx.measureText(txt).width > lg.w - padX * 2 && txt.length > 4) txt = txt.slice(0, -2);
    if (txt !== t) txt += "…";
    ctx.fillText(txt, lg.x + padX, topY + i * lineH);
  }
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

function drawGameOver() {
  if (!S.is_game_over) return;
  ctx.fillStyle = "rgba(4,8,8,0.62)";
  ctx.fillRect(0, 0, W, H);
  const c = S.character || {};
  const win = (c.realm === "飞升");
  ctx.fillStyle = win ? C.gold : C.cream;
  ctx.font = F(48, "bold"); ctx.textAlign = "center";
  ctx.shadowColor = "rgba(0,0,0,0.8)"; ctx.shadowBlur = 16;
  ctx.fillText(win ? "羽 化 飞 升" : "仙 途 终 结", W / 2, H / 2 - 10);
  ctx.shadowBlur = 0;
  ctx.fillStyle = C.dim; ctx.font = F(16);
  ctx.fillText("点击右上角 ↻ 重开 再入轮回", W / 2, H / 2 + 40);
}

/* ================= 主循环 ================= */
let tideActive = false, hoverBtn = null, hoverRestart = false;

function render(t) {
  ctx.clearRect(0, 0, W, H);
  tideActive = !!(S.tide_effect && S.tide_effect.tone);
  drawBackground();
  drawHUD();
  drawBanner();
  drawButtons(t);
  drawStatus();
  drawLog();
  drawEffects(t);
  drawGameOver();
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
  for (const def of BTN_DEFS) {
    const dx = p.x - def.cx, dy = p.y - def.cy;
    if (dx * dx + dy * dy <= L.btnR * L.btnR) return def.action;
  }
  return null;
}
function doGameAction(action) {
  try {
    const r = game.doAction(action);
    if (!r.success) {
      toast(r.message, "warn");
    } else {
      fx.press = { action, start: now() };
    }
    const ef = r.effects || {};
    if (ef.level_up) {
      fx.rings.push({ cx: W / 2, cy: L.btnY, start: now() });
      bigText("突破 · " + (ef.new_level || ""), C.jade, 2000);
      toast("突破至 " + (ef.new_level || "") + "！", "good");
    }
    if (ef.fire_deviation) {
      fx.deviation = now();
      bigText("走火入魔", C.red, 2200);
      toast("走火入魔！气息紊乱 3 回合", "warn");
    }
    if (ef.exp_gain > 0) fx.expFloats.push({ amount: ef.exp_gain, x: W / 2, y: L.btnY - 70, start: now() });
    if (ef.demon_cleared) { bigText("破心魔", C.jade, 1800); toast("心魔已破！修炼加速", "good"); }
    if (ef.tribulation) {
      const ok = !!ef.tribulation_success;
      bigText(ok ? "渡劫成功" : "渡劫失败", ok ? C.gold : C.red, 2200);
      toast(ok ? "渡劫成功！配额已刷新" : "渡劫失败……", ok ? "good" : "warn");
    }
    if (ef.restart) { fx.toasts = []; fx.bigText = null; fx.deviation = 0; lastLogLen = 0; }
    S = game.getState();
    if (S.is_game_over && !ef.restart) bigText((S.character.realm === "飞升") ? "羽 化 飞 升" : "仙 途 终 结", C.gold, 3000);
  } catch (e) { console.error("[canvas] 动作失败", e); }
}
canvas.addEventListener("click", e => {
  const p = toGame(e);
  const r = L.restart;
  if (p.x >= r.x && p.x <= r.x + r.w && p.y >= r.y && p.y <= r.y + r.h) {
    doGameAction("restart");
    return;
  }
  const a = hitButton(p);
  if (!a) return;
  const b = (S.buttons || []).find(x => x.action === a);
  if (!b || !b.enabled || S.is_game_over) return;
  doGameAction(a);
});
canvas.addEventListener("mousemove", e => {
  const p = toGame(e);
  const r = L.restart;
  hoverRestart = p.x >= r.x && p.x <= r.x + r.w && p.y >= r.y && p.y <= r.y + r.h;
  const a = hitButton(p);
  const b = a && (S.buttons || []).find(x => x.action === a);
  hoverBtn = (b && b.enabled && !S.is_game_over) ? a : null;
  canvas.style.cursor = (hoverRestart || hoverBtn) ? "pointer" : "default";
});
canvas.addEventListener("touchstart", e => {
  // 移动端：touch 等同 click（click 事件本身也会触发，这里只做 hover 清理）
  hoverBtn = null; hoverRestart = false;
}, { passive: true });

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
