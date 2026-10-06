"""
方案B Web 版主入口（跑在 Pyodide 里）
流程：初始化 GameCore -> 首屏 render -> JS 定时调用 tick() -> 事件 -> 动作 -> 特效 -> 渲染

改用 tick 模式（替代 asyncio 无限循环）：
- Pyodide 里 asyncio.ensure_future 的后台任务不可靠
- JS 用 setInterval 每 100ms 调用一次 window.pyTick()，Python 执行单步
"""
import sys
import os

for _p in ("/", os.getcwd()):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core.game_core import GameCore
from web_interface import WebInterface
from bridge import play_effect, js_log

# 全局单例，供 tick() 使用
_game = None
_ui = None


def detect_effects(game: GameCore, result: dict, prev_realm: str):
    """根据动作执行结果触发前端特效"""
    effects = result.get("effects") or {}
    try:
        if effects.get("level_up"):
            play_effect("breakthrough", {"realm": effects.get("new_level", "")})
        if effects.get("fire_deviation"):
            play_effect("deviation", {"turns": game.character.fire_deviation_turn if game.character else 0})
        exp_gain = effects.get("exp_gain") or 0
        if isinstance(exp_gain, (int, float)) and exp_gain > 0:
            play_effect("exp_float", {"amount": int(exp_gain)})
        if effects.get("demon_cleared"):
            play_effect("demon_cleared", {})
        if effects.get("tribulation"):
            play_effect("tribulation", {"success": bool(effects.get("tribulation_success"))})
    except Exception as e:
        js_log("[web] 特效触发失败:", str(e))


def tick():
    """单步：处理一个输入事件（由 JS 定时调用）。返回 True 表示有动作执行。"""
    global _game, _ui
    if _game is None or _ui is None:
        return False
    if not _ui.is_running():
        return False
    try:
        event = _ui.handle_input()
        if not event:
            return False
        action_name = event.data.get("action")
        js_log("[web] 收到动作:", action_name)
        if action_name == "restart":
            _game.initialize_game()
            _ui.render(_game.get_game_state())
            play_effect("restart", {})
            return True
        prev_realm = ""
        try:
            prev_realm = _game.character.get_status_summary().get("realm", "")
        except Exception:
            pass
        result = _game.execute_action(action_name)
        detect_effects(_game, result, prev_realm)
        _ui.render(_game.get_game_state())
        if _game.is_game_over:
            play_effect("game_over", {})
        return True
    except Exception as e:
        js_log("[web] tick 异常:", str(e))
        return False


def main():
    global _game, _ui
    js_log("[web] 极简修仙 Web 版启动")
    _game = GameCore()
    ok = _game.initialize_game()
    js_log("[web] 游戏初始化:", ok)
    _ui = WebInterface()
    _ui.initialize()
    _ui.render(_game.get_game_state())
    js_log("[web] 首屏已渲染，等待玩家操作（tick 模式）")
    return 0


# Pyodide 通过 runPython 执行时直接启动
try:
    main()
except Exception as e:
    try:
        js_log("[web] 启动失败:", str(e))
    except Exception:
        print("[web] 启动失败:", e)
