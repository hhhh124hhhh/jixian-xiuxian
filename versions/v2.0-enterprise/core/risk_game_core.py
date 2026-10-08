"""把风险修炼规则接入现有 PygameGameInterface，不替换界面/贴图/布局。"""
from models import CharacterStats, GameLog, RealmLevel
from core.risk_run import RiskRun, TIDES, REALMS, LIFESPAN, CULTIVATION_QUOTA, PILL_QUOTA


BUTTON_IDS = ("meditate", "consume_pill", "cultivate", "wait")
PLAY_ACTIONS = ("breathe", "bank", "brew", "tribulate")
DEMON_ACTIONS = ("demon_break", "demon_calm", "demon_convert", None)


class _RiskButton:
    def __init__(self, game, name, description):
        self.game, self.name, self.description = game, name, description

    def can_execute(self, character):
        return self.game._button_enabled(self.name)


class RiskGameCore:
    """兼容 GameApplication 所需的 GameCore 接口。"""

    def __init__(self, rng=None):
        self.run = RiskRun(rng=rng)
        self.character = None
        self.game_log = None
        self.is_game_over = False
        self.difficulty = "normal"
        self.game_state = {}
        self.available_actions = [
            _RiskButton(self, name, description)
            for name, description in zip(BUTTON_IDS, ("吐纳", "收功", "炼丹", "渡劫"))
        ]

    def initialize_game(self, character_name=None, difficulty="normal"):
        self.difficulty = difficulty
        self.run.reset()
        self.character = CharacterStats(character_name or "无名修士")
        self.game_log = GameLog()
        self.game_log.add_entry("【风险修炼】收功消耗 1 次配额；灵潮提前揭示，突破前请权衡炼丹与寿元。")
        self.game_log.add_entry("灵潮预告：" + TIDES[self.run.s.tide][0] + " · " + TIDES[self.run.s.tide][1])
        self.is_game_over = False
        self._update_game_state()
        return True

    def _mapping(self):
        return DEMON_ACTIONS if self.run.s.phase == "demon" else PLAY_ACTIONS

    def _button_enabled(self, button_id):
        if button_id not in BUTTON_IDS:
            return False
        actual = self._mapping()[BUTTON_IDS.index(button_id)]
        return bool(actual and self.run.can(actual))

    def execute_action(self, action_name):
        if action_name not in BUTTON_IDS:
            return {"success": False, "message": "未知操作", "effects": {}, "costs": {}}
        action = self._mapping()[BUTTON_IDS.index(action_name)]
        if not action:
            return {"success": False, "message": "心魔出现，请先作出选择。", "effects": {}, "costs": {}}
        result = self.run.act(action)
        if result["success"]:
            self.game_log.add_entry(result["message"])
            if action in ("bank", "demon_break", "demon_calm", "demon_convert") and self.run.s.phase == "playing":
                self.game_log.add_entry("下一轮灵潮：" + TIDES[self.run.s.tide][0] + " · " + TIDES[self.run.s.tide][1])
        self._update_game_state()
        return result

    def _sync_character(self):
        c, s = self.character, self.run.s
        c.health.max_hp = LIFESPAN
        c.health.current_hp = max(0, s.life)
        c.mana.max_mp = CULTIVATION_QUOTA
        c.mana.current_mp = max(0, s.quota)
        c.experience.current_realm = (
            RealmLevel.QI_REFINING if s.realm == 0 else
            RealmLevel.FOUNDATION if s.realm == 1 else RealmLevel.CORE_FORMATION
        )
        c.experience.realm_thresholds[RealmLevel.QI_REFINING] = 100
        c.experience.realm_thresholds[RealmLevel.FOUNDATION] = 250
        c.experience.current_level_experience = s.exp
        c.experience.total_experience = s.earned
        c.inventory.items["pill"] = s.pills
        c.breath_combo = s.combo
        c.total_actions = s.actions
        c.cultivate_quota = s.quota
        c.pills_quota = PILL_QUOTA - s.made
        c.tribulation_fails = s.fails

    def _update_game_state(self):
        if not self.character:
            return
        self._sync_character()
        s = self.run.s
        name, info = TIDES[s.tide]
        if s.phase == "demon":
            labels = ("破心魔", "静心", "化为资源", "待命")
            hint = f"心魔降临：可保留本轮 {10*s.demon_prior*s.demon_prior} 修为或转化丹药"
        else:
            labels = ("吐纳", "收功", "炼丹", "渡劫")
            hint = f"灵潮：{name}；{info}"
        self.game_state = {
            "character": self.character,
            "game_log": self.game_log,
            "actions": self.available_actions,
            "is_game_over": self.is_game_over,
            "risk_mode": True,
            "victory": s.phase == "won",
            "recommendation": hint,
            "tide_effect": {"label": f"{name}：{info}", "tone": "buff"},
            "breath_combo_status": (
                f"×{s.combo} · 下次走火 {self.run.next_fire}%"
                if self.run.next_fire is not None else "×7 · 可收功"
            ),
            "breath_combo": s.combo,
            "fire_deviation_turn": 1 if s.phase == "demon" else 0,
            "demon_cleared_status": "",
            "tribulation_ready": self.run.can("tribulate"),
            "tribulation_rate": self.run.chance,
            "tribulation_fails": s.fails,
            "quota_status": {
                "pills_left": PILL_QUOTA - s.made,
                "cultivate_left": s.quota,
                "pills_limit": PILL_QUOTA,
                "cultivate_limit": CULTIVATION_QUOTA,
                "text": f"寿元{s.life}/22 · 修炼{s.quota}/12 · 炼丹{s.made}/6 · 渡劫{self.run.chance}%",
                "exhausted": s.quota < 2,
            },
            "action_labels": dict(zip(BUTTON_IDS, labels)),
            "tide_name": name,
            "tide_description": info,
            "risk_phase": s.phase,
        }
        self.is_game_over = s.phase in ("won", "lost")
        self.game_state["is_game_over"] = self.is_game_over

    def get_game_state(self):
        return self.game_state.copy()

    def reset_game(self, character_name=None, difficulty=None):
        return self.initialize_game(character_name, difficulty or self.difficulty)

    def get_game_statistics(self):
        s = self.run.s
        return {
            "current_realm": REALMS[s.realm],
            "total_experience": s.earned,
            "total_actions": s.actions,
            "tribulation_attempts": s.attempts,
            "victory": s.phase == "won",
            "reason": s.last,
        }
