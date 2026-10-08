"""风险修炼模式：纯规则层，不依赖 Pygame，可注入随机源以便测试。

已锁定的数值：走火率 0/5/10/15/22/30/40%，境界每期 12 次修炼、
6 颗丹药，渡劫成功率 50% + 每丹 17%，前两次渡劫失败不扣修为。
新增的试验参数集中在此文件顶部，不影响旧模式。
"""
from dataclasses import dataclass
from math import ceil
from random import Random

FIRE_RATES = (0, 5, 10, 15, 22, 30, 40)
TARGETS = (100, 250)
REALMS = ("炼气期", "筑基期", "结丹期")
CULTIVATION_QUOTA = 12
PILL_QUOTA = 6
LIFESPAN = 22
ALCHEMY_EXP_COST = 40
ALCHEMY_LIFE_COST = 2
TRIBULATION_LIFE_COST = 3
TIDES = (
    ("平稳灵息", "正常收功；无额外效果"),
    ("灵气奔涌", "×4及以上收功额外获得 60 修为"),
    ("丹火旺盛", "×3及以上收功，使下一颗丹药少花 20 修为"),
    ("固本培元", "×5及以上收功，恢复 2 年寿元"),
)


@dataclass
class RunState:
    realm: int = 0
    exp: int = 0
    combo: int = 0
    quota: int = CULTIVATION_QUOTA
    life: int = LIFESPAN
    pills: int = 0
    made: int = 0
    fails: int = 0
    phase: str = "playing"
    demon_prior: int = 0
    tide: int = 0
    discount: bool = False
    actions: int = 0
    earned: int = 0
    attempts: int = 0
    last: str = ""


class RiskRun:
    """明确的状态转换；只有合法操作才改变状态。"""

    def __init__(self, rng=None):
        self.rng = rng or Random()
        self.reset()

    def reset(self):
        self.s = RunState(tide=self.rng.randrange(len(TIDES)))
        self.s.last = "灵潮已提前显现。吐纳有风险，收功消耗 1 次修炼配额。"
        return self.s

    @property
    def goal(self):
        return TARGETS[self.s.realm] if self.s.realm < len(TARGETS) else 0

    @property
    def chance(self):
        return min(100, 50 + 17 * self.s.pills)

    @property
    def next_fire(self):
        return FIRE_RATES[self.s.combo] if self.s.combo < 7 else None

    @property
    def pending_exp(self):
        return 10 * self.s.combo * self.s.combo

    def can(self, action):
        s = self.s
        if s.phase == "demon":
            return {
                "demon_break": s.pills >= 1,
                "demon_calm": True,
                "demon_convert": s.pills < PILL_QUOTA and s.made < PILL_QUOTA and s.life > 2,
            }.get(action, False)
        if s.phase != "playing":
            return False
        return {
            "breathe": s.quota >= 2 and s.life > 0 and s.combo < 7,
            "bank": s.quota >= 1 and s.combo > 0,
            "brew": s.combo == 0 and s.made < PILL_QUOTA and s.pills < PILL_QUOTA
                and s.life > ALCHEMY_LIFE_COST
                and s.exp >= (ALCHEMY_EXP_COST // 2 if s.discount else ALCHEMY_EXP_COST),
            "tribulate": s.combo == 0 and s.exp >= self.goal
                and s.life >= TRIBULATION_LIFE_COST,
        }.get(action, False)

    def _new_tide(self):
        self.s.tide = self.rng.randrange(len(TIDES))

    def _check_end(self):
        s = self.s
        if s.phase != "playing":
            return
        if s.life <= 0:
            s.phase, s.last = "lost", "寿元耗尽，寿终坐化。"
        elif s.combo == 0 and s.life < TRIBULATION_LIFE_COST:
            s.phase, s.last = "lost", "剩余寿元不足以渡劫，大限已至。"
        elif s.combo == 0 and s.exp < self.goal and s.quota < 2:
            s.phase, s.last = "lost", "修炼配额不足以完成下一次吐纳与收功，突破失败。"

    def act(self, action):
        if not self.can(action):
            return {"success": False, "message": "当前状态不能执行该操作。"}
        s = self.s
        s.actions += 1
        msg = ""

        if action == "breathe":
            risk = self.next_fire
            roll = self.rng.random() * 100
            s.quota -= 1
            s.life -= 1
            if s.life <= 0:
                s.phase = "lost"
                msg = "最后一次吐纳耗尽寿元，寿终坐化。"
            elif roll < risk:
                prior = s.combo
                s.combo = 0
                s.demon_prior = prior
                s.phase = "demon"
                msg = f"冲击 ×{prior + 1} 走火！随机点数 {roll:.1f} < 走火率 {risk}%。请选择心魔应对。"
            else:
                s.combo += 1
                msg = f"吐纳成功：连击 ×{s.combo}。现收功可获 {self.pending_exp} 修为。"

        elif action == "bank":
            s.quota -= 1
            gain = self.pending_exp
            bonus = ""
            if s.tide == 1 and s.combo >= 4:
                gain += 60
                bonus = "；灵气奔涌 +60"
            elif s.tide == 2 and s.combo >= 3:
                s.discount = True
                bonus = "；获得下一颗丹药的 20 修为优惠"
            elif s.tide == 3 and s.combo >= 5:
                s.life = min(LIFESPAN, s.life + 2)
                bonus = "；固本培元恢复 2 年寿元"
            s.exp += gain
            s.earned += gain
            msg = f"×{s.combo} 收功，获得 {gain} 修为{bonus}。"
            s.combo = 0
            self._new_tide()

        elif action == "brew":
            cost = ALCHEMY_EXP_COST // 2 if s.discount else ALCHEMY_EXP_COST
            s.exp -= cost
            s.life -= ALCHEMY_LIFE_COST
            s.pills += 1
            s.made += 1
            s.discount = False
            msg = f"炼丹成功：消耗 {cost} 修为、2 年寿元。持有 {s.pills} 丹，渡劫率 {self.chance}%。"

        elif action == "tribulate":
            rate = self.chance
            roll = self.rng.random() * 100
            s.life -= TRIBULATION_LIFE_COST
            s.pills = 0
            s.attempts += 1
            if roll < rate:
                s.realm += 1
                s.exp = 0
                s.quota = CULTIVATION_QUOTA
                s.life = LIFESPAN
                s.made = 0
                s.fails = 0
                s.discount = False
                self._new_tide()
                if s.realm == len(REALMS) - 1:
                    s.phase = "won"
                    msg = f"渡劫成功！随机点数 {roll:.1f} < {rate}%，结成金丹，获胜！"
                else:
                    msg = f"渡劫成功！随机点数 {roll:.1f} < {rate}%，筑基成功，寿元与配额刷新。"
            else:
                s.fails += 1
                loss = 0 if s.fails <= 2 else ceil(s.exp * 0.5)
                s.exp -= loss
                msg = (f"渡劫失败：随机点数 {roll:.1f} ≥ {rate}%。本境第 {s.fails} 次失败，"
                       + (f"扣除 {loss} 修为。" if loss else "劫后余生保底，修为不扣。")
                       + " 丹药耗尽，寿元 -3。")

        elif action in ("demon_break", "demon_calm", "demon_convert"):
            banked = 10 * s.demon_prior * s.demon_prior
            if action == "demon_break":
                s.pills -= 1
                s.exp += banked
                s.earned += banked
                msg = f"破心魔：消耗 1 丹，保全 {banked} 修为。"
            elif action == "demon_calm":
                gain = banked // 2
                s.exp += gain
                s.earned += gain
                msg = f"静心：保留一半收益，获得 {gain} 修为。"
            else:
                s.life -= ALCHEMY_LIFE_COST
                s.pills += 1
                s.made += 1
                msg = "化为资源：消耗 2 年寿元和 1 次炼丹配额，获得 1 丹药。"
            s.phase = "playing"
            s.demon_prior = 0
            self._new_tide()

        s.last = msg
        self._check_end()
        return {"success": True, "message": msg, "effects": {}, "costs": {}}
