"""
Pyodide JS 桥接封装
在浏览器里通过 Pyodide 的 js 模块调用前端函数；
在桌面测试环境（无 js 模块）下降级为空操作，保证可 import。
"""

try:
    import js as _js
    from pyodide.ffi import to_py as _to_py
    HAS_JS = True
except ImportError:
    _js = None
    HAS_JS = False


def _window():
    if not HAS_JS:
        return None
    return _js.window


def call_js(func_name, *args):
    """调用 window 上的 JS 全局函数，失败返回 None"""
    w = _window()
    if w is None:
        return None
    try:
        func = getattr(w, func_name, None)
        if func is None:
            return None
        return func(*args)
    except Exception:
        return None


def update_ui(state_dict):
    """把序列化后的游戏状态推给 JS 的 updateUI(state)"""
    return call_js("updateUI", state_dict)


def play_effect(name, data=None):
    """触发前端特效：playEffect(name, data)"""
    return call_js("playEffect", name, data or {})


def js_log(*args):
    """写到浏览器 console"""
    w = _window()
    if w is None:
        print(*args)
        return
    try:
        w.console.log(*args)
    except Exception:
        print(*args)


def pop_js_events():
    """从 window.gameEvents 取出并清空事件队列，返回 Python list"""
    w = _window()
    if w is None:
        return []
    try:
        q = getattr(w, "gameEvents", None)
        if q is None:
            return []
        items = []
        # JsProxy 数组 ->逐个 to_py
        n = int(q.length)
        for i in range(n):
            try:
                items.append(_to_py(q[i]))
            except Exception:
                items.append(dict(q[i]))
        # 清空队列
        q.length = 0
        # to_py 后的 dict 可能还是 proxy，统一转成普通 dict
        out = []
        for it in items:
            if isinstance(it, dict):
                out.append(it)
            else:
                try:
                    out.append(dict(it))
                except Exception:
                    out.append({"action": str(it)})
        return out
    except Exception:
        return []
