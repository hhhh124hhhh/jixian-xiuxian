"""
方案B Web 版主入口（跑在 Pyodide 里）
JS 直接调用 do_action(action)，Python 执行并返回新状态。
"""
import sys
import os
import json

for _p in ("/", os.getcwd()):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core.game_core import GameCore
from web_interface import WebInterface
from bridge import play_effect, js_log

_game = None
_ui = None


def detect_effects(game, result, prev_realm):
    effects = result.get("effects") or {}
    try:
        if effects.get("level_up"):
            play_effect("breakthrough", {"realm": effects.get("new_level", "")})
        if effects.get("fire_deviation"):
            play_effect("deviation", {})
        exp_gain = effects.get("exp_gain") or 0
        if isinstance(exp_gain, (int, float)) and exp_gain > 0:
            play_effect("exp_float", {"amount": int(exp_gain)})
        if effects.get("demon_cleared"):
            play_effect("demon_cleared", {})
        if effects.get("tribulation"):
            play_effect("tribulation", {"success": bool(effects.get("tribulation_success"))})
    except Exception as e:
        js_log("[web] 特效失败:", str(e))


def do_action(action_name):
    """JS 直接调用：执行动作，返回 JSON 状态字符串"""
    global _game, _ui
    try:
        if action_name == "restart":
            _game.initialize_game()
        else:
            prev_realm = ""
            try:
                prev_realm = _game.character.get_status_summary().get("realm", "")
            except Exception:
                pass
            result = _game.execute_action(action_name)
            detect_effects(_game, result, prev_realm)
        state = _game.get_game_state()
        _ui.render(state)
        return json.dumps({"ok": True})
    except Exception as e:
        js_log("[web] do_action 异常:", str(e))
        return json.dumps({"ok": False, "error": str(e)})


def main():
    global _game, _ui
    js_log("[web] 启动")
    _game = GameCore()
    _game.initialize_game()
    _ui = WebInterface()
    _ui.initialize()
    _ui.render(_game.get_game_state())
    js_log("[web] 就绪")
    return 0

try:
    main()
except Exception as e:
    try:
        js_log("[web] 启动失败:", str(e))
    except Exception:
        print("[web] 启动失败:", e)
