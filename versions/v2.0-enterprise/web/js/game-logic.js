/* 极简修仙 · 纯游戏逻辑（无 DOM 操作，可跑在浏览器/Node）
 * 由 versions/v2.0-enterprise 的 Python 代码逐字移植：
 *   models.py / rules.py / actions.py / core/game_core.py / core/tide_system.py
 * 数值与规则与 Python 版保持一致。
 */
"use strict";

(function (global) {
  // ---------- 常量 ----------
  const REALMS = ["炼气期", "筑基期", "结丹期", "元婴期", "化神期", "飞升"];
  const REALM_THRESHOLDS = [100, 200, 400, 800, 1600, Infinity];

  const BREATH_COMBO_MAX = 6;
  const BREATH_MULTIPLIERS = [1.0, 1.5, 2.2, 3.2, 4.5, 6.0, 7.0];
  const FIRE_RATES = [0.0, 0.0, 0.03, 0.08, 0.15, 0.25, 0.40];
  const DEVIATION_DURATION = 3;
  const DEVIATION_EXP_RATIO = 0.7;
  const DEVIATION_COST_RATIO = 1.2;

  const TRIB_MAX_RATE = 1.0;
  const TRIB_SURVIVAL_LIMIT = 2;
  const TRIB_SURVIVAL_EXP = 10;

  const CULTIVATE_QUOTA = 12;
  const QUOTA_EXHAUSTED_MSG = "配额已用完，渡劫后刷新";

  const DEMON_BONUS_USES = 3;
  const DEMON_MULTIPLIER = 1.4;

  const TALENT_MULT = { meditate: 0.8, cultivate: 1.5, pill: 1.0, wait: 0.2 };

  const TIDE_EFFECTS = [
    { action: "cultivate", stat: "exp", ratio: 0.15, label: "下次修炼经验 +15%", tone: "buff" },
    { action: "meditate", stat: "mp", ratio: 0.15, label: "下次打坐回蓝 +15%", tone: "buff" },
    { action: "cultivate", stat: "exp", ratio: -0.10, label: "下次修炼经验 -10%", tone: "debuff" },
    { action: "meditate", stat: "mp", ratio: -0.10, label: "下次打坐回蓝 -10%", tone: "debuff" },
  ];
  const TIDE_ACTION_LABELS = { cultivate: "修炼", meditate: "打坐" };

  const DIFFICULTIES = {
    easy: { talentMin: 5, talentMax: 10, pills: 3 },
    normal: { talentMin: 1, talentMax: 10, pills: 1 },
    hard: { talentMin: 1, talentMax: 6, pills: 0 },
  };

  // ---------- 数值配置（所有平衡数值集中于此，逻辑层不写死） ----------
  const BALANCE = {
    player: { maxHp: 100, maxMp: 100 },
    lifespan: { "炼气期": 60, "筑基期": 100, "结丹期": 140, "元婴期": 180, "化神期": 220 },
    lifespanWarn: { aging: 20, dying: 10 },
    combo: {
      deviationDamage: [0, 10, 15, 25, 35, 50, 70],
    },
    meditate: { hp: 15, mp: 30 },
    wait: { hp: 8, mp: 3 },
    pill: { hp: 40, mp: 30, quota: 6 },
    tribulation: { baseRate: 0.50, pillRateStep: 0.10, maxPills: 3, successHeal: 20, failHpLoss: 60, failExpLossRatio: 0.30 },
    wounded: { threshold: 30, extraDamage: 10 },
  };

  const DEATH_EPITAPHS = {
    deviation: "贪一息之功，损百年道行。",
    tribulation: "雷劫之下，终差一线。",
    lifespan: "大限已至，坐化于蒲团之上。",
    demon: "心魔未除，道躯先灭。",
  };

  // 旧常量保留（外部可能引用），取值改由 BALANCE 派生，避免两处数字打架
  const PILLS_QUOTA = BALANCE.pill.quota;
  const TRIB_BASE_RATE = BALANCE.tribulation.baseRate;
  const TRIB_PILL_STEP = BALANCE.tribulation.pillRateStep;
  const TRIB_EXP_LOSS_RATIO = BALANCE.tribulation.failExpLossRatio;

  // ---------- 小工具 ----------
  function clampInt(v, lo, hi) {
    v = parseInt(v, 10);
    if (isNaN(v)) v = lo;
    return Math.max(lo, Math.min(hi, v));
  }
  // 模仿 Python :g 格式化（去掉浮点噪音）
  function fmtG(n) {
    return String(parseFloat(n.toPrecision(6)));
  }
  function randInt(lo, hi) {
    return lo + Math.floor(Math.random() * (hi - lo + 1));
  }
  function talentBonus(base, talent, actionType) {
    const m = TALENT_MULT[actionType] || 1.0;
    return Math.floor(base + talent * m);
  }
  function clampCombo(c) { return clampInt(c, 0, BREATH_COMBO_MAX); }
  function comboMult(c) { return BREATH_MULTIPLIERS[clampCombo(c)]; }
  function fireRate(c) { return FIRE_RATES[clampCombo(c)]; }
  // 走火阶梯伤害：气血见底（重伤）时额外加重
  function deviationDamage(combo, ch) {
    let dmg = BALANCE.combo.deviationDamage[clampCombo(combo)] || 0;
    if (ch && ch.hp <= BALANCE.wounded.threshold) dmg += BALANCE.wounded.extraDamage;
    return dmg;
  }
  function tribRate(pillsUsed) {
    const raw = Math.max(0, parseInt(pillsUsed, 10) || 0);
    const p = Math.min(raw, BALANCE.tribulation.maxPills);
    return Math.round(Math.min(TRIB_MAX_RATE, BALANCE.tribulation.baseRate + BALANCE.tribulation.pillRateStep * p) * 100) / 100;
  }
  function tribRatePct(pillsUsed) { return Math.round(tribRate(pillsUsed) * 100); }

  // ---------- 角色 ----------
  function createCharacter(name, difficulty) {
    const d = DIFFICULTIES[difficulty] || DIFFICULTIES.normal;
    const life = lifespanMaxFor({ realmIndex: 0 });
    return {
      name: name || "无名修士",
      maxHp: BALANCE.player.maxHp, hp: BALANCE.player.maxHp,
      maxMp: BALANCE.player.maxMp, mp: 50,
      talent: randInt(d.talentMin, d.talentMax),
      pills: d.pills,
      expTotal: 0, expCurrent: 0, realmIndex: 0,
      meditationStreak: 0, totalActions: 0,
      breathCombo: 0, fireDeviationTurn: 0,
      tribulationFails: 0, demonClearedBonus: 0,
      pillsQuota: BALANCE.pill.quota, cultivateQuota: CULTIVATE_QUOTA,
      pillsUsedInRealm: 0,
      lifespan: life, lifespanMax: life,
      deathCause: null, maxCombo: 0,
    };
  }

  function isAlive(ch) { return ch.hp > 0; }
  function realmName(ch) { return REALMS[ch.realmIndex]; }
  // 当前境界的寿元上限（飞升无对应表项，沿用最高一档）
  function lifespanMaxFor(ch) {
    const byRealm = BALANCE.lifespan[realmName(ch)];
    if (byRealm != null) return byRealm;
    const names = Object.keys(BALANCE.lifespan);
    return BALANCE.lifespan[names[names.length - 1]];
  }
  // 突破后刷新寿元到新境界上限
  function refreshLifespan(ch) {
    ch.lifespanMax = lifespanMaxFor(ch);
    ch.lifespan = ch.lifespanMax;
  }
  function realmThreshold(ch) { return REALM_THRESHOLDS[ch.realmIndex]; }
  function isExpFull(ch) {
    return ch.realmIndex < REALMS.length - 1 && ch.expCurrent >= REALM_THRESHOLDS[ch.realmIndex];
  }
  function expProgress(ch) {
    const t = REALM_THRESHOLDS[ch.realmIndex];
    if (!isFinite(t)) return 100;
    return Math.min(100, (ch.expCurrent / t) * 100);
  }

  function restoreHp(ch, amount) {
    const before = ch.hp;
    ch.hp = Math.min(ch.maxHp, ch.hp + amount);
    return ch.hp - before;
  }
  function restoreMp(ch, amount) {
    const before = ch.mp;
    ch.mp = Math.min(ch.maxMp, ch.mp + amount);
    return ch.mp - before;
  }
  // 返回 {leveled, msg}
  function addExperience(ch, amount) {
    ch.expTotal += amount;
    ch.expCurrent += amount;
    const threshold = REALM_THRESHOLDS[ch.realmIndex];
    if (ch.expCurrent >= threshold && ch.realmIndex < REALMS.length - 1) {
      ch.realmIndex += 1;
      ch.expCurrent = ch.expCurrent - threshold;
      refreshLifespan(ch);
      return { leveled: true, msg: "突破至 " + REALMS[ch.realmIndex] + "！" };
    }
    return { leveled: false, msg: null };
  }
  function spendRealmExp(ch, amount) {
    const loss = Math.max(0, Math.min(Math.floor(amount), ch.expCurrent));
    ch.expCurrent -= loss;
    ch.expTotal -= loss;
    return loss;
  }

  function comboStatus(ch) {
    const combo = clampCombo(ch.breathCombo);
    const turns = clampInt(ch.fireDeviationTurn, 0, DEVIATION_DURATION);
    if (turns > 0) return "气息紊乱（剩" + turns + "回合）";
    if (combo <= 0) return "";
    return "连击" + combo + " · 收益×" + fmtG(comboMult(combo)) +
      " · 走火" + fmtG(fireRate(combo) * 100) + "%";
  }
  function demonStatus(ch) {
    const b = clampInt(ch.demonClearedBonus, 0, DEMON_BONUS_USES);
    if (b <= 0) return "";
    return "破心魔×" + fmtG(DEMON_MULTIPLIER) + "（剩" + b + "次）";
  }
  function quotaText(ch) {
    return "丹药 " + ch.pillsQuota + "/" + BALANCE.pill.quota +
      " · 修炼 " + ch.cultivateQuota + "/" + CULTIVATE_QUOTA;
  }

  function recommendation(ch) {
    if (!isAlive(ch)) return "修炼失败，请重新开始";
    if (ch.pillsQuota <= 0 || ch.cultivateQuota <= 0) {
      if (isExpFull(ch)) {
        return "经验已满，点击渡劫（成功率" + tribRatePct(ch.pillsUsedInRealm) + "%）突破";
      }
      return QUOTA_EXHAUSTED_MSG;
    }
    const hpPct = ch.hp / ch.maxHp, mpPct = ch.mp / ch.maxMp;
    if (hpPct < 0.3) {
      return ch.pills > 0 ? "生命垂危，建议立即服用丹药" : "生命垂危且无丹药，建议等待恢复";
    }
    if (mpPct < 0.3) {
      return ch.pills > 0 ? "仙力不足，建议服用丹药恢复" : "仙力不足，建议打坐恢复";
    }
    if (mpPct > 0.8 && ch.pills > 2) return "状态良好，建议全力修炼";
    if (ch.pills === 0) return "缺少丹药，建议多打坐积累";
    return "状态适中，可以根据需要选择修炼或恢复";
  }

  // ---------- 潮汐 ----------
  function createTide() {
    return { actionCount: 0, pending: null, totalTriggered: 0 };
  }
  function tidePreview(effect) {
    const al = TIDE_ACTION_LABELS[effect.action] || "对应";
    return effect.label + "，下一次" + al + "行动生效";
  }
  // 返回 {label, tone, before, after} 或 null
  function tideCheckAndConsume(tide, actionName, result, ch) {
    const t = tide.pending;
    if (t && t.action === actionName) {
      let before, after;
      if (t.stat === "exp") {
        before = result.effects.exp_gain || 0;
        const delta = Math.round(before * t.ratio);
        if (delta !== 0) addExperience(ch, delta);
        result.effects.exp_gain = before + delta;
        after = before + delta;
      } else {
        before = result.effects.mp_recovery || 0;
        const delta = Math.round(before * t.ratio);
        if (delta >= 0) restoreMp(ch, delta);
        else ch.mp = Math.max(0, ch.mp + delta);
        result.effects.mp_recovery = before + delta;
        after = before + delta;
      }
      tide.pending = null;
      return { label: t.label, tone: t.tone, before: before, after: after };
    }
    return null;
  }
  // 返回 {effect, preview, total} 或 null
  function tideRegister(tide, result) {
    if (result.effects.level_up) return null;
    tide.actionCount += 1;
    if (tide.actionCount >= 5) {
      const src = TIDE_EFFECTS[Math.floor(Math.random() * TIDE_EFFECTS.length)];
      tide.pending = { action: src.action, stat: src.stat, ratio: src.ratio, label: src.label, tone: src.tone };
      tide.actionCount = 0;
      tide.totalTriggered += 1;
      return { effect: tide.pending, preview: tidePreview(tide.pending), total: tide.totalTriggered };
    }
    return null;
  }

  // ---------- 动作 ----------
  function meditateCan(ch) { return isAlive(ch); }
  function meditateLabel(ch) { return ch.fireDeviationTurn > 0 ? "破心魔" : "打坐"; }
  function doMeditate(ch, log) {
    ch.totalActions += 1;
    const demonCleared = ch.fireDeviationTurn > 0;
    const mpRecovery = BALANCE.meditate.mp;
    let expGain = talentBonus(3, ch.talent, "meditate");
    const expFull = isExpFull(ch);
    if (expFull) expGain = 0;
    const actualHp = restoreHp(ch, BALANCE.meditate.hp);
    const actualMp = restoreMp(ch, mpRecovery);
    let leveled = false, levelMsg = null, newLevel = null;
    if (!expFull) {
      const r = addExperience(ch, expGain);
      leveled = r.leveled; levelMsg = r.msg;
      if (leveled) newLevel = realmName(ch);
    }
    ch.breathCombo = 0;
    ch.fireDeviationTurn = Math.max(0, clampInt(ch.fireDeviationTurn, 0, DEVIATION_DURATION) - 1);
    if (demonCleared) {
      ch.fireDeviationTurn = 0;
      ch.demonClearedBonus = DEMON_BONUS_USES;
    }
    ch.meditationStreak += 1;
    let pillBonus = 0;
    if (ch.meditationStreak % 5 === 0) { ch.pills += 1; pillBonus = 1; }

    const msgs = ["你进入打坐修炼状态，恢复" + actualHp + "点气血和" + actualMp + "点仙力，获得" + expGain + "点经验"];
    if (expFull) msgs.push("经验已满，修为暂存，等你渡劫");
    if (demonCleared) msgs.push("破心魔！气息紊乱尽消，接下来" + DEMON_BONUS_USES + "次修炼收益×" + fmtG(DEMON_MULTIPLIER));
    else if (ch.fireDeviationTurn > 0) msgs.push("气息紊乱尚余" + ch.fireDeviationTurn + "回合");
    if (leveled) msgs.push(levelMsg);
    if (pillBonus > 0) msgs.push("连续打坐" + ch.meditationStreak + "次，获得" + pillBonus + "颗丹药！");
    const message = msgs.join("，");
    log.push(message);
    const effects = {
      hp_recovery: actualHp, mp_recovery: actualMp, exp_gain: expGain, pill_bonus: pillBonus,
      demon_cleared: demonCleared, demon_cleared_bonus: ch.demonClearedBonus,
    };
    if (leveled) { effects.level_up = true; effects.new_level = newLevel; }
    return { success: true, message: message, effects: effects, costs: { time: 1 } };
  }
  function meditateFail(ch) { return "无法执行进入冥想状态，恢复仙力并获得少量经验"; }

  function pillCan(ch) {
    return isAlive(ch) && ch.pills >= 1 && ch.pillsQuota > 0;
  }
  function pillLabel(ch) { return ch.fireDeviationTurn > 0 ? "静心" : "吃丹药"; }
  function doPill(ch, log) {
    const calming = ch.fireDeviationTurn > 0;
    ch.pills -= 1;
    ch.totalActions += 1;
    const hpRecovery = talentBonus(BALANCE.pill.hp, ch.talent, "pill");
    const mpRecovery = talentBonus(BALANCE.pill.mp, ch.talent, "pill");
    let expGain = talentBonus(5, ch.talent, "pill");
    const expFull = isExpFull(ch);
    if (expFull) expGain = 0;
    const actualHp = restoreHp(ch, hpRecovery);
    const actualMp = restoreMp(ch, mpRecovery);
    let leveled = false, levelMsg = null, newLevel = null;
    if (!expFull) {
      const r = addExperience(ch, expGain);
      leveled = r.leveled; levelMsg = r.msg;
      if (leveled) newLevel = realmName(ch);
    }
    if (calming) { ch.breathCombo = 0; ch.fireDeviationTurn = 0; }
    ch.pillsUsedInRealm = Math.max(0, ch.pillsUsedInRealm + 1);
    ch.pillsQuota = Math.max(0, ch.pillsQuota - 1);
    ch.meditationStreak = 0;
    const label = calming ? "静心" : "服用丹药";
    const msgs = ["你" + label + "，服下一颗丹药，恢复" + actualHp + "点生命和" + actualMp + "点仙力"];
    if (expGain > 0) msgs.push("获得" + expGain + "点经验");
    if (expFull) msgs.push("经验已满，修为暂存，等你渡劫");
    if (calming) msgs.push("气息紊乱已平，连击散去（无加速）");
    if (leveled) msgs.push(levelMsg);
    msgs.push("丹药 " + ch.pillsQuota + "/" + BALANCE.pill.quota);
    const message = msgs.join("，") + "。";
    log.push(message);
    const effects = {
      hp_recovery: actualHp, mp_recovery: actualMp, exp_gain: expGain,
      pills_quota_left: ch.pillsQuota, pills_used_in_realm: ch.pillsUsedInRealm,
      calming: calming,
    };
    if (leveled) { effects.level_up = true; effects.new_level = newLevel; }
    return { success: true, message: message, effects: effects, costs: { pills: 1 } };
  }
  function pillFail(ch) {
    if (!isAlive(ch)) return "你已经无法行动";
    if (ch.pills < 1) return "没有丹药可用";
    if (ch.pillsQuota <= 0) return QUOTA_EXHAUSTED_MSG;
    return "无法服用丹药";
  }

  function cultMpCost(ch) {
    let cost = 20;
    if (ch.fireDeviationTurn > 0) cost = Math.round(cost * DEVIATION_COST_RATIO);
    return Math.max(0, cost);
  }
  function cultCan(ch) {
    if (!isAlive(ch)) return false;
    if (isExpFull(ch)) return true;
    return ch.mp >= cultMpCost(ch) && ch.cultivateQuota > 0;
  }
  function cultLabel(ch) {
    if (isExpFull(ch)) return "渡劫（成功率" + tribRatePct(ch.pillsUsedInRealm) + "%）";
    return "修炼";
  }
  function doCultivate(ch, log) {
    if (isExpFull(ch)) return doTribulation(ch, log);
    const mpCost = cultMpCost(ch);
    ch.mp = Math.max(0, ch.mp - mpCost);
    ch.totalActions += 1;
    const comboBefore = clampCombo(ch.breathCombo);
    // 隐藏测试钩子 ?debug_deviation=100：强制走火且伤害固定 999（仅测试用）
    const forceDev = ch._debugForceDeviation === true;
    const deviated = forceDev ? true : Math.random() < fireRate(comboBefore);
    const demonActive = clampInt(ch.demonClearedBonus, 0, DEMON_BONUS_USES) > 0;
    let expGain, multiplier = comboMult(comboBefore);
    let deviationDmg = 0;
    if (deviated) {
      deviationDmg = forceDev ? 999 : deviationDamage(comboBefore, ch);
      ch.hp = Math.max(0, ch.hp - deviationDmg);
      if (!isAlive(ch)) ch.deathCause = "deviation";
      ch.breathCombo = 0;
      ch.fireDeviationTurn = DEVIATION_DURATION;
      expGain = 0;
    } else {
      expGain = 10 * multiplier;
      if (ch.fireDeviationTurn > 0) expGain *= DEVIATION_EXP_RATIO;
      if (demonActive) expGain *= DEMON_MULTIPLIER;
      expGain = Math.max(0, Math.round(expGain));
      ch.breathCombo = clampCombo(comboBefore + 1);
      ch.maxCombo = Math.max(ch.maxCombo, ch.breathCombo);
      if (expGain > 0) ch.demonClearedBonus = Math.max(0, ch.demonClearedBonus - 1);
    }
    const r = addExperience(ch, expGain);
    const leveled = r.leveled;
    let newLevel = null;
    if (leveled) newLevel = realmName(ch);
    ch.cultivateQuota = Math.max(0, ch.cultivateQuota - 1);
    ch.meditationStreak = 0;
    const msgs = [];
    if (deviated) {
      msgs.push("气息走火！你连吐纳的" + fmtG(multiplier) + "倍收益尽数散去，进入气息紊乱（" + ch.fireDeviationTurn + "回合）");
      msgs.push("走火反噬，损失" + deviationDmg + "点气血");
    } else {
      msgs.push("你运转心法，修为精进，获得" + expGain + "点经验（连击" + comboBefore + "→" + ch.breathCombo + "，收益×" + fmtG(multiplier) + "）");
      if (ch.fireDeviationTurn > 0) msgs.push("气息紊乱中，本次仙力消耗×" + fmtG(DEVIATION_COST_RATIO) + "、收益×" + fmtG(DEVIATION_EXP_RATIO));
      if (demonActive && expGain > 0) msgs.push("破心魔加持，收益×" + fmtG(DEMON_MULTIPLIER) + "（剩" + ch.demonClearedBonus + "次）");
    }
    msgs.push("修炼 " + ch.cultivateQuota + "/" + CULTIVATE_QUOTA);
    if (leveled) msgs.push(r.msg);
    const message = msgs.join("，") + "。";
    log.push(message);
    const effects = {
      exp_gain: expGain, breath_combo: ch.breathCombo,
      fire_deviation_turn: ch.fireDeviationTurn, fire_deviation: deviated,
      deviation_damage: deviationDmg,
      demon_cleared_bonus: ch.demonClearedBonus, cultivate_quota_left: ch.cultivateQuota,
    };
    if (leveled) { effects.level_up = true; effects.new_level = newLevel; }
    return { success: true, message: message, effects: effects, costs: { mp: mpCost, time: 2 } };
  }
  function doTribulation(ch, log) {
    const pillsUsed = ch.pillsUsedInRealm;
    const rate = tribRate(pillsUsed);
    ch.totalActions += 1;
    ch.meditationStreak = 0;
    const succeeded = Math.random() < rate;
    const effects = {
      tribulation: true, tribulation_success: succeeded,
      tribulation_rate: rate, pills_used_in_realm: pillsUsed,
    };
    const msgs = ["天劫降临！以本境界" + pillsUsed + "颗丹药为凭，成功率" + fmtG(rate * 100) + "%"];
    if (succeeded) {
      const prevRealm = realmName(ch);
      ch.realmIndex += 1;
      ch.expCurrent = 0;
      ch.pillsQuota = BALANCE.pill.quota;
      ch.cultivateQuota = CULTIVATE_QUOTA;
      ch.pillsUsedInRealm = 0;
      refreshLifespan(ch);
      const healed = restoreHp(ch, BALANCE.tribulation.successHeal);
      msgs.push("雷劫加身，你自" + prevRealm + "突破至" + realmName(ch) + "！");
      msgs.push("境界配额已刷新（丹药 " + ch.pillsQuota + "/" + BALANCE.pill.quota + " · 修炼 " + ch.cultivateQuota + "/" + CULTIVATE_QUOTA + "）");
      msgs.push("天劫余韵洗练筋骨，恢复" + healed + "点气血");
      msgs.push("寿元重续 " + ch.lifespanMax + " 年");
      effects.level_up = true;
      effects.new_level = realmName(ch);
      effects.pills_quota_left = ch.pillsQuota;
      effects.cultivate_quota_left = ch.cultivateQuota;
      effects.hp_recovery = healed;
    } else {
      const lostHp = Math.min(ch.hp, BALANCE.tribulation.failHpLoss);
      ch.hp = Math.max(0, ch.hp - BALANCE.tribulation.failHpLoss);
      if (!isAlive(ch)) ch.deathCause = "tribulation";
      const penalty = Math.floor(ch.expCurrent * BALANCE.tribulation.failExpLossRatio);
      const lost = spendRealmExp(ch, penalty);
      ch.tribulationFails = Math.max(0, ch.tribulationFails + 1);
      msgs.push("雷劫加身，道基受损，折损" + lostHp + "点气血，损失" + lost + "点当前境界经验（-" + fmtG(BALANCE.tribulation.failExpLossRatio * 100) + "%）");
      const comp = ch.tribulationFails <= TRIB_SURVIVAL_LIMIT ? TRIB_SURVIVAL_EXP : 0;
      if (comp > 0) {
        addExperience(ch, comp);
        msgs.push("成就「劫后余生」（第" + ch.tribulationFails + "次劫）：心有所悟，补回" + comp + "点经验");
      }
      effects.exp_lost = lost;
      effects.hp_lost = lostHp;
      effects.tribulation_fails = ch.tribulationFails;
      effects.survival_achievement = comp > 0;
      effects.comp_exp = comp;
      effects.pills_quota_left = ch.pillsQuota;
      effects.cultivate_quota_left = ch.cultivateQuota;
    }
    const message = msgs.join("，") + "。";
    log.push(message);
    return { success: true, message: message, effects: effects, costs: { time: 2 } };
  }
  function cultFail(ch) {
    if (!isAlive(ch)) return "你已经无法行动";
    if (ch.mp < cultMpCost(ch)) return "仙力不足，无法修炼";
    if (ch.cultivateQuota <= 0) return QUOTA_EXHAUSTED_MSG;
    return "无法修炼";
  }

  function waitCan(ch) { return isAlive(ch); }
  function doWait(ch, log) {
    ch.totalActions += 1;
    const actualHp = restoreHp(ch, BALANCE.wait.hp);
    const actualMp = restoreMp(ch, BALANCE.wait.mp);
    ch.breathCombo = 0;
    ch.meditationStreak = 0;
    const message = "你静心等待，恢复" + actualHp + "点生命和" + actualMp + "点仙力。";
    log.push(message);
    return {
      success: true, message: message,
      effects: { hp_recovery: actualHp, mp_recovery: actualMp },
      costs: { time: 1 },
    };
  }

  const ACTIONS = {
    meditate: { can: meditateCan, do: doMeditate, fail: meditateFail, label: meditateLabel, desc: "进入冥想状态，恢复仙力并获得少量经验" },
    consume_pill: { can: pillCan, do: doPill, fail: pillFail, label: pillLabel, desc: "服用丹药快速恢复生命力和仙力" },
    cultivate: { can: cultCan, do: doCultivate, fail: cultFail, label: cultLabel, desc: "运转心法，大量提升修为" },
    wait: { can: waitCan, do: doWait, fail: function () { return "无法执行静心养神，缓慢恢复状态"; }, label: function () { return "等待"; }, desc: "静心养神，缓慢恢复状态" },
  };

  // ---------- 游戏 ----------
  function createGame() {
    const game = {
      ch: null, log: [], tide: createTide(),
      isGameOver: false, difficulty: "normal",

      init: function (name, difficulty) {
        this.difficulty = difficulty || "normal";
        this.ch = createCharacter(name, this.difficulty);
        this.log = [];
        this.tide = createTide();
        this.isGameOver = false;
        this.log.push("欢迎来到极简修仙世界，" + this.ch.name + "！");
        this.log.push("你的资质为 " + this.ch.talent + "，开始你的修仙之旅。");
        return true;
      },

      reset: function (name, difficulty) {
        return this.init(name || (this.ch && this.ch.name), difficulty || this.difficulty);
      },

      doAction: function (actionName) {
        const ch = this.ch;
        if (this.isGameOver || !ch) {
          return { success: false, message: "游戏已结束", effects: {}, costs: {} };
        }
        if (actionName === "restart") {
          this.reset();
          return { success: true, message: "新的轮回开始", effects: { restart: true }, costs: {} };
        }
        const a = ACTIONS[actionName];
        if (!a) return { success: false, message: "未找到动作: " + actionName, effects: {}, costs: {} };
        if (!a.can(ch)) {
          return { success: false, message: a.fail(ch), effects: {}, costs: {} };
        }
        const result = a.do(ch, this.log);

        // 寿元：每成功行动折寿一年
        if (result.success) ch.lifespan = Math.max(0, ch.lifespan - 1);

        // 潮汐：仅成功且非渡劫的动作
        if (result.success && !result.effects.tribulation) {
          const consumed = tideCheckAndConsume(this.tide, actionName, result, ch);
          if (consumed) {
            result.effects.tide_applied = consumed.label;
            this.log.push("潮汐应验：" + consumed.label);
          }
          const triggered = tideRegister(this.tide, result);
          if (triggered) {
            this.log.push("灵气潮汐预兆：" + triggered.preview);
          }
        }

        this.checkGameOver();
        return result;
      },

      checkGameOver: function () {
        const ch = this.ch;
        if (!ch) return;
        if (!isAlive(ch)) {
          this.isGameOver = true;
          ch.deathCause = ch.deathCause || "deviation";
          this.log.push("你身死道消，仙途终结。");
        } else if (ch.lifespan <= 0) {
          this.isGameOver = true;
          ch.deathCause = "lifespan";
          this.log.push("寿元耗尽，你寿终坐化。");
        } else if (realmName(ch) === "飞升") {
          this.isGameOver = true;
          this.log.push("恭喜！你已成功飞升，达成完美结局！");
        }
      },

      // 生成给 UI 的状态（与旧 updateUI 兼容）
      getState: function () {
        const ch = this.ch;
        if (!ch) return { character: {}, log: [], buttons: [] };
        const c = {
          name: ch.name, realm: realmName(ch),
          hp: ch.hp, max_hp: ch.maxHp, mp: ch.mp, max_mp: ch.maxMp,
          exp: ch.expCurrent, exp_progress: expProgress(ch),
          exp_threshold: realmThreshold(ch),
          pills: ch.pills, total_actions: ch.totalActions,
          talent: ch.talent, alive: isAlive(ch),
          lifespan: ch.lifespan, lifespan_max: ch.lifespanMax,
          lifespan_warn: ch.lifespan <= BALANCE.lifespanWarn.dying ? "dying"
            : (ch.lifespan <= BALANCE.lifespanWarn.aging ? "aging" : "normal"),
          deathCause: ch.deathCause, max_combo: ch.maxCombo,
        };
        const buttons = ["meditate", "consume_pill", "cultivate", "wait"].map(function (id) {
          const a = ACTIONS[id];
          return {
            name: id, action: id,
            label: a.label(ch),
            enabled: !this.isGameOver && a.can(ch),
            tooltip: a.desc,
          };
        }, this);
        const tide = this.tide.pending ? {
          label: this.tide.pending.label,
          preview: tidePreview(this.tide.pending),
          tone: this.tide.pending.tone,
        } : null;
        return {
          character: c,
          log: this.log.slice(),
          buttons: buttons,
          tide_effect: tide,
          tide_progress: this.tide.actionCount,
          breath_combo: ch.breathCombo,
          breath_combo_status: comboStatus(ch),
          fire_deviation_turn: ch.fireDeviationTurn,
          fire_rate: fireRate(ch.breathCombo),
          deviation_damage: deviationDamage(ch.breathCombo, ch),
          demon_cleared_status: demonStatus(ch),
          quota: { text: quotaText(ch) },
          tribulation: {
            ready: isExpFull(ch),
            rate: tribRatePct(ch.pillsUsedInRealm),
            fails: ch.tribulationFails,
          },
          recommendation: recommendation(ch),
          is_game_over: this.isGameOver,
          difficulty: this.difficulty,
        };
      },
    };
    return game;
  }

  // ---------- 导出 ----------
  const api = {
    createGame: createGame,
    REALMS: REALMS,
    DEATH_EPITAPHS: DEATH_EPITAPHS,
    // 供测试用的内部规则
    _rules: {
      tribRate: tribRate, tribRatePct: tribRatePct,
      comboMult: comboMult, fireRate: fireRate,
      deviationDamage: deviationDamage, lifespanMaxFor: lifespanMaxFor,
      BALANCE: BALANCE,
      PILLS_QUOTA: PILLS_QUOTA, CULTIVATE_QUOTA: CULTIVATE_QUOTA,
    },
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  } else {
    global.GameLogic = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
