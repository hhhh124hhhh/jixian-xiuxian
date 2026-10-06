"""
方案B Web 版主入口（跑在 Pyodide 里）
流程：初始化 GameCore -> 首屏 render -> async 循环 poll 事件 -> 执行动作 -> 判特效 -> render
"""
import sys
import os
import asyncio

for _p in ("/", os.getcwd()):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core.game_core import GameCore
from web.py.web_interface import WebInterface
from web.py.bridge import play_effect, js_log


def detect_effects(game: GameCore, result: dict, prev_realm: str):
    """根据动作执行结果触发前端特效"""
    effects = result.get("effects") or {}
    try:
        # 突破：境界提升 -> 青玉扩散圆环
        if effects.get("level_up"):
            play_effect("breakthrough", {"realm": effects.get("new_level", "")})
        # 走火：fire_deviation 为 True -> 红色脉冲
        if effects.get("fire_deviation"):
            play_effect("deviation", {"turns": game.character.fire_deviation_turn if game.character else 0})
        # 经验上浮
        exp_gain = effects.get("exp_gain") or 0
        if isinstance(exp_gain, (int, float)) and exp_gain > 0:
            play_effect("exp_float", {"amount": int(exp_gain)})
        # 破心魔
        if effects.get("demon_cleared"):
            play_effect("demon_cleared", {})
        # 渡劫
        if effects.get("tribulation"):
            play_effect("tribulation", {"success": bool(effects.get("tribulation_success"))})
    except Exception as e:
        js_log("[web] 特效触发失败:", str(e))


async def game_loop(game: GameCore, ui: WebInterface):
    """主循环：事件 -> 动作 -> 特效 -> 渲染"""
    js_log("[web] 游戏主循环启动")
    while ui.is_running():
        try:
            event = ui.handle_input()
            if event:
                action_name = event.data.get("action")
                js_log("[web] 收到动作:", action_name)
                if action_name == "restart":
                    game.initialize_game()
                    ui.render(game.get_game_state())
                    play_effect("restart", {})
                    continue
                prev_realm = ""
                try:
                    prev_realm = game.character.get_status_summary().get("realm", "")
                except Exception:
                    pass
                result = game.execute_action(action_name)
                detect_effects(game, result, prev_realm)
                ui.render(game.get_game_state())
                if game.is_game_over:
                    play_effect("game_over", {})
        except Exception as e:
            js_log("[web] 主循环异常:", str(e))
        await asyncio.sleep(0.05)


def main():
    js_log("[web] 极简修仙 Web 版启动")
    game = GameCore()
    ok = game.initialize_game()
    js_log("[web] 游戏初始化:", ok)
    ui = WebInterface()
    ui.initialize()
    ui.render(game.get_game_state())
    # 在 Pyodide 里跑 async 循环，不阻塞浏览器
    asyncio.ensure_future(game_loop(game, ui))
    js_log("[web] 首屏已渲染，等待玩家操作")
    return 0


# Pyodide 通过 runPython 执行时直接启动
try:
    main()
except Exception as e:
    try:
        js_log("[web] 启动失败:", str(e))
    except Exception:
        print("[web] 启动失败:", e)
