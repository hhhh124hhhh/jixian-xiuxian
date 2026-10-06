/* 极简修仙 Web 版 · 前端主逻辑 */
"use strict";

// 事件队列：Python 端 handle_input() 从这里读
window.gameEvents = [];

// ---------- Pyodide 启动 ----------
const PY_FILES = [
  "models.py",
  "rules.py",
  "actions.py",
  "core/__init__.py",
  "core/game_core.py",
  "core/action_registry.py",
  "core/event_handler.py",
  "core/state_manager.py",
  "core/tide_system.py",
  "actions/__init__.py",
  "actions/system_actions.py",
  "ui/interface.py",
  "bridge.py",
  "web_interface.py",
  "web_main.py",
];

function setLoad(pct, text) {
  const fill = document.getElementById("load-fill");
  const status = document.getElementById("load-status");
  if (fill) fill.style.width = pct + "%";
  if (status && text) status.textContent = text;
}

async function boot() {
  try {
    setLoad(10, "正在加载 Pyodide…");
    const pyodide = await loadPyodide();
    window._pyodide = pyodide;
    setLoad(35, "正在加载游戏逻辑…");

    // 把 Python 文件写入 Pyodide 文件系统（保持相对目录结构）
    const base = "py/";
    let i = 0;
    for (const f of PY_FILES) {
      const url = base + f;
      const resp = await fetch(url);
      if (!resp.ok) throw new Error("加载失败: " + url);
      const text = await resp.text();
      const dir = f.split("/").slice(0, -1).join("/");
      if (dir) pyodide.FS.mkdirTree("/" + dir);
      pyodide.FS.writeFile("/" + f, text);
      i++;
      setLoad(35 + Math.round((i / PY_FILES.length) * 40), `正在加载游戏逻辑… (${i}/${PY_FILES.length})`);
    }

    setLoad(85, "正在启动游戏…");
    // 运行主入口（内含初始化 + 首屏渲染 + async 主循环）
    await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, "/")
exec(open("/web_main.py").read())
`);
    setLoad(100, "完成");
    document.getElementById("loading").classList.add("hide");
    console.log("[web] Pyodide 启动完成");
  } catch (e) {
    setLoad(100, "启动失败: " + e.message);
    console.error("[web] 启动失败", e);
  }
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
    document.getElementById("exp-text").textContent = `${c.exp || 0}`;
    // 丹药/连击/配额
    document.getElementById("pills-count").textContent = c.pills || 0;
    const comboEl = document.getElementById("combo-line");
    comboEl.textContent = state.breath_combo_status || "--";
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
      tribEl.textContent = `渡劫：可渡（成功率 ${trib.rate}%）`;
      tribEl.classList.add("ready");
    } else {
      tribEl.textContent = "渡劫：时机未到";
      tribEl.classList.remove("ready");
    }
    // 指引
    document.getElementById("reco-line").textContent = "指引：" + (state.recommendation || "--");
    // 按钮
    const btns = state.buttons || [];
    const btnEls = document.querySelectorAll(".act-btn");
    btnEls.forEach((el) => {
      const action = el.dataset.action;
      const b = btns.find((x) => x.action === action);
      if (b) {
        el.disabled = !b.enabled;
        const span = el.querySelector("span");
        if (span) span.textContent = b.label || b.name;
        el.title = b.tooltip || "";
      }
    });
    // 日志（增量追加）
    const logs = state.log || [];
    if (logs.length > lastLogLen) {
      const box = document.getElementById("game-log");
      for (let k = lastLogLen; k < logs.length; k++) {
        const div = document.createElement("div");
        div.textContent = logs[k];
        const t = logs[k];
        if (/潮汐|灵气/.test(t)) div.className = "tide";
        else if (/走火|失败|心魔/.test(t)) div.className = "warn";
        else if (/突破|成功|获得/.test(t)) div.className = "good";
        box.appendChild(div);
      }
      box.scrollTop = box.scrollHeight;
      lastLogLen = logs.length;
    } else if (logs.length < lastLogLen) {
      // 重开后重置
      lastLogLen = 0;
      const box = document.getElementById("game-log");
      box.innerHTML = "";
      logs.forEach((t) => {
        const div = document.createElement("div");
        div.textContent = t;
        box.appendChild(div);
      });
      lastLogLen = logs.length;
    }
  } catch (e) {
    console.error("[web] updateUI 失败", e);
  }
};

function setBar(name, cur, max) {
  cur = cur || 0; max = max || 1;
  document.getElementById(name + "-fill").style.width = Math.max(0, Math.min(100, (cur / max) * 100)) + "%";
  document.getElementById(name + "-text").textContent = `${cur}/${max}`;
}

// ---------- Python -> JS：特效 ----------
window.playEffect = function (name, data) {
  data = data || {};
  console.log("[web] 特效:", name, data);
  const layer = document.getElementById("fx-layer");
  if (name === "breakthrough") {
    // 青玉扩散圆环 x3 + 文字
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
    void document.body.offsetWidth; // 重启动画
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

// ---------- JS -> Python：按钮点击入队 ----------
document.querySelectorAll(".act-btn, .sys-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (btn.disabled) return;
    window.gameEvents.push({ action: btn.dataset.action });
  });
});

// 启动
boot();
