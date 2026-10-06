"""
Web 界面实现（方案B）
实现 ui.interface.GameInterface 抽象类：
  render(game_state) -> 序列化后调用 JS updateUI()
  handle_input()     -> 从 window.gameEvents 队列读用户点击
"""
import sys
import os

# Pyodide FS 根目录即工作区，保证 core/models 等可 import
for _p in ("/", os.getcwd()):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from typing import Dict, Any, Optional

# ui/__init__.py 依赖 pygame（桌面版），Web 版绕过包初始化，
# 直接用 importlib 加载 ui/interface.py 单文件
import importlib.util as _ilu


def _load_interface():
    spec = _ilu.spec_from_file_location("game_ui_interface", "/ui/interface.py")
    mod = _ilu.module_from_spec(spec)
    import sys as _sys
    _sys.modules["game_ui_interface"] = mod
    spec.loader.exec_module(mod)
    return mod


_ui_iface = _load_interface()
GameInterface = _ui_iface.GameInterface
GameStateRenderer = _ui_iface.GameStateRenderer
UIEvent = _ui_iface.UIEvent

from bridge import update_ui, pop_js_events, js_log


def serialize_state(game_state: Dict[str, Any], renderer: GameStateRenderer) -> Dict[str, Any]:
    """把 game_state 转成 JSON 可序列化的 dict 给 JS"""
    character = game_state.get("character")
    status = character.get_status_summary() if character else {}

    game_log = game_state.get("game_log")
    log_entries = game_log.get_recent_entries(30) if game_log else []

    actions = game_state.get("actions", [])
    buttons = []
    if character:
        try:
            btn_states = renderer.format_action_buttons(character, actions)
        except Exception:
            btn_states = []
        action_labels = game_state.get("action_labels") or {}
        # 注意：ButtonState.action 是类名派生的（如 consumepill），
        # 但 execute_action 按 action.name（如 consume_pill）查找，
        # 这里用真实 action.name 作为前端回传的 ID
        for b, a in zip(btn_states, actions):
            real_id = getattr(a, "name", b.action)
            label = action_labels.get(real_id) or action_labels.get(b.action) or b.name
            buttons.append({
                "name": b.name,
                "action": real_id,
                "label": label,
                "enabled": bool(b.enabled),
                "tooltip": b.tooltip or "",
            })

    quota = game_state.get("quota_status") or {}
    trib = {
        "ready": bool(game_state.get("tribulation_ready")),
        "rate": game_state.get("tribulation_rate") or 0,
        "fails": game_state.get("tribulation_fails") or 0,
    }

    return {
        "character": status,
        "log": log_entries,
        "buttons": buttons,
        "tide_effect": game_state.get("tide_effect"),
        "tide_progress": game_state.get("tide_progress") or 0,
        "breath_combo": game_state.get("breath_combo") or 0,
        "breath_combo_status": game_state.get("breath_combo_status") or "",
        "fire_deviation_turn": game_state.get("fire_deviation_turn") or 0,
        "demon_cleared_status": game_state.get("demon_cleared_status") or "",
        "quota": {
            "pills_left": quota.get("pills_left", 0),
            "cultivate_left": quota.get("cultivate_left", 0),
            "text": quota.get("text") or "",
            "exhausted": bool(quota.get("exhausted")),
        },
        "tribulation": trib,
        "power_level": game_state.get("power_level") or 0,
        "recommendation": game_state.get("recommendation") or "",
        "is_game_over": bool(game_state.get("is_game_over")),
        "difficulty": game_state.get("difficulty") or "normal",
        "total_actions": status.get("total_actions", 0),
    }


class WebInterface(GameInterface):
    """Web 前端界面"""

    def __init__(self):
        self.renderer = GameStateRenderer()
        self._running = True
        self._last_log_len = 0

    def initialize(self) -> bool:
        js_log("[web] WebInterface 初始化")
        return True

    def render(self, game_state: Dict[str, Any]) -> None:
        try:
            state = serialize_state(game_state, self.renderer)
            update_ui(state)
        except Exception as e:
            js_log("[web] render 失败:", str(e))

    def handle_input(self) -> Optional[UIEvent]:
        events = pop_js_events()
        if not events:
            return None
        e = events[0]
        action = e.get("action") if isinstance(e, dict) else None
        if not action:
            return None
        import time
        return UIEvent(event_type="action", data={"action": action}, timestamp=time.time())

    def shutdown(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running
