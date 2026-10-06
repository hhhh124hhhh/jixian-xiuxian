/* 极简修仙 Web 版 · 前端主逻辑（纯 JS，无 Pyodide） */
"use strict";

// ---------- 启动 ----------
const game = GameLogic.createGame();
game.init("无名修士", "normal");

function setLoad(pct, text) {
  const fill = document.getElementById("load-fill");
  const status = document.getElementById("load-status");
  if (fill) fill.style.width = pct + "%";
  if (status && text) status.textContent = text;
}

// ---------- Python -> JS：状态更新 ----------
let lastLogLen = 0;

window.updateUI = function (state) {
  try {
    const c = state.character || {};
    // 角色
    document.getElementById("char-name").textContent = c.name || "无名修士";
    document.getElementById("char-realm").textContent = c.realm || "炼气期";
    document.getElementById("turn-count").textContent = c.total_actions || 0;
    // 血条
    setBar("hp", c.hp, c.max_hp);
    setBar("mp", c.mp, c.max_mp);
    // 经验条（用百分比）
    const expPct = c.exp_progress || 0;
    document.getElementById("exp-fill").style.width = Math.min(100, expPct) + "%";
    const thr = c.exp_threshold;
    document.getElementById("exp-text").textContent =
      (c.exp || 0) + (isFinite(thr) ? "/" + thr : "");
    // 丹药/连击/配额
    document.getElementById("pills-count").textContent = c.pills || 0;
    const comboEl = document.getElementById("combo-line");
    const comboTxt = state.breath_combo_status || state.demon_cleared_status || "--";
    comboEl.textContent = comboTxt;
    comboEl.classList.toggle("warn", (state.fire_deviation_turn || 0) > 0);
    document.getElementById("quota-line").textContent = (state.quota && state.quota.text) || "--";
    // 潮汐
    const tideEl = document.getElementById("tide-line");
    const tide = state.tide_effect;
    if (tide) {
      tideEl.textContent = "灵气潮汐：" + (tide.label || tide.preview || "有感应");
      tideEl.classList.add("active");
    } else {
      tideEl.textContent = "灵气潮汐：平静";
      tideEl.classList.remove("active");
    }
    // 渡劫
    const tribEl = document.getElementById("trib-line");
    const trib = state.tribulation || {};
    if (trib.ready) {
      tribEl.textContent = "渡劫：可渡（成功率 " + trib.rate + "%）";
      tribEl.classList.add("ready");
    } else {
      tribEl.textContent = "渡劫：时机未到";
      tribEl.classList.remove("ready");
    }
    // 指引
    document.getElementById("reco-line").textContent = "指引：" + (state.recommendation || "--");
    // 按钮
    const btns = state.buttons || [];
    document.querySelectorAll(".act-btn").forEach((el) => {
      const action = el.dataset.action;
      const b = btns.find((x) => x.action === action);
      if (b) {
        el.disabled = !b.enabled;
        const span = el.querySelector("span");
        if (span) span.textContent = b.label || b.name;
        el.title = b.tooltip || "";
      }
    });
    // 游戏结束时只留重开
    const over = !!state.is_game_over;
    document.querySelectorAll(".act-btn").forEach((el) => {
      if (over) el.disabled = true;
    });
    // 日志（增量追加）
    const logs = state.log || [];
    const box = document.getElementById("game-log");
    if (logs.length > lastLogLen) {
      for (let k = lastLogLen; k < logs.length; k++) {
        box.appendChild(logDiv(logs[k]));
      }
      box.scrollTop = box.scrollHeight;
      lastLogLen = logs.length;
    } else if (logs.length < lastLogLen) {
      // 重开后重置
      box.innerHTML = "";
      logs.forEach((t) => box.appendChild(logDiv(t)));
      box.scrollTop = box.scrollHeight;
      lastLogLen = logs.length;
    }
  } catch (e) {
    console.error("[web] updateUI 失败", e);
  }
};

function logDiv(t) {
  const div = document.createElement("div");
  div.textContent = t;
  if (/\[错误\]/.test(t)) div.className = "log-error";
  else if (/潮汐|灵气/.test(t)) div.className = "tide";
  else if (/走火|失败|心魔|终结/.test(t)) div.className = "warn";
  else if (/突破|成功|获得/.test(t)) div.className = "good";
  return div;
}

function setBar(name, cur, max) {
  cur = cur || 0; max = max || 1;
  document.getElementById(name + "-fill").style.width = Math.max(0, Math.min(100, (cur / max) * 100)) + "%";
  document.getElementById(name + "-text").textContent = cur + "/" + max;
}

// ---------- 特效 ----------
window.playEffect = function (name, data) {
  data = data || {};
  const layer = document.getElementById("fx-layer");
  if (name === "breakthrough") {
    for (let i = 1; i <= 3; i++) {
      const ring = document.createElement("div");
      ring.className = "fx-ring r" + i;
      layer.appendChild(ring);
      setTimeout(() => ring.remove(), 1600);
    }
    const txt = document.createElement("div");
    txt.className = "fx-breakthrough-text";
    txt.textContent = "突破 · " + (data.realm || "");
    layer.appendChild(txt);
    setTimeout(() => txt.remove(), 1800);
  } else if (name === "exp_float") {
    const el = document.createElement("div");
    el.className = "fx-exp";
    el.textContent = "+" + (data.amount || 0) + " 经验";
    el.style.left = (45 + Math.random() * 10) + "%";
    layer.appendChild(el);
    setTimeout(() => el.remove(), 1300);
  } else if (name === "deviation") {
    document.body.classList.remove("deviation");
    void document.body.offsetWidth;
    document.body.classList.add("deviation");
    const txt = document.createElement("div");
    txt.className = "fx-deviation-text";
    txt.textContent = "走火入魔";
    layer.appendChild(txt);
    setTimeout(() => { txt.remove(); document.body.classList.remove("deviation"); }, 3200);
  } else if (name === "tribulation") {
    const el = document.createElement("div");
    el.className = "fx-trib " + (data.success ? "ok" : "fail");
    el.textContent = data.success ? "渡劫成功" : "渡劫失败";
    layer.appendChild(el);
    setTimeout(() => el.remove(), 2000);
  } else if (name === "demon_cleared") {
    const el = document.createElement("div");
    el.className = "fx-breakthrough-text";
    el.textContent = "破心魔";
    layer.appendChild(el);
    setTimeout(() => el.remove(), 1800);
  } else if (name === "game_over") {
    const el = document.createElement("div");
    el.className = "fx-deviation-text";
    el.textContent = "仙途终结";
    layer.appendChild(el);
    setTimeout(() => el.remove(), 3000);
  }
  // restart 无特效，静默
};

// ---------- Toast 通知（桌面版移植：200ms淡入 → 2.5s停留 → 300ms淡出） ----------
window.showToast = function (message, type) {
  const layer = document.getElementById("toast-layer");
  if (!layer) return;
  const el = document.createElement("div");
  el.className = "toast" + (type ? " " + type : "");
  el.textContent = message;
  layer.appendChild(el);
  // CSS 动画 3s 后移除
  setTimeout(() => el.remove(), 3100);
};

function triggerEffects(effects) {
  effects = effects || {};
  if (effects.level_up) {
    window.playEffect("breakthrough", { realm: effects.new_level || "" });
    window.showToast("突破至 " + (effects.new_level || "") + "！", "good");
  }
  if (effects.fire_deviation) {
    window.playEffect("deviation", {});
    window.showToast("走火入魔！气息紊乱 3 回合", "warn");
  }
  const eg = effects.exp_gain || 0;
  if (eg > 0) window.playEffect("exp_float", { amount: eg });
  if (effects.demon_cleared) {
    window.playEffect("demon_cleared", {});
    window.showToast("心魔已破！修炼加速", "good");
  }
  if (effects.tribulation) {
    window.playEffect("tribulation", { success: !!effects.tribulation_success });
    window.showToast(
      effects.tribulation_success ? "渡劫成功！配额已刷新" : "渡劫失败……",
      effects.tribulation_success ? "good" : "warn"
    );
  }
}

// ---------- 按钮 ----------
document.querySelectorAll(".act-btn, .sys-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (btn.disabled) return;
    const action = btn.dataset.action;
    try {
      const r = game.doAction(action);
      if (!r.success) {
        const box = document.getElementById("game-log");
        const div = document.createElement("div");
        div.className = "log-error";
        div.textContent = r.message;
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;
      }
      triggerEffects(r.effects);
      window.updateUI(game.getState());
      if (game.getState().is_game_over) window.playEffect("game_over", {});
    } catch (e) {
      console.error("[web] 动作失败", e);
    }
  });
});

// ---------- 启动 ----------
setLoad(100, "完成");
window.updateUI(game.getState());
document.getElementById("loading").classList.add("hide");
console.log("[web] 纯 JS 版启动完成");
