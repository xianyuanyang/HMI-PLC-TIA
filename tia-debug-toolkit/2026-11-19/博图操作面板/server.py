# -*- coding: utf-8 -*-
"""
TIA Portal 本地桥接服务 (路线 B 后端)
------------------------------------------------------------
浏览器面板 -> 本服务(localhost) -> tia_client.py -> TiaMcpServer.exe -> TIA Portal

特性:
- 零第三方依赖: 只用 Python 标准库 (http.server / json / threading), 新电脑无需 pip install
- 长连接: 引擎进程只启动一次, 所有调用复用 (实时轮询快)
- 串行化: 引擎 stdin/stdout 不支持并发, 全局锁保证一次一个调用
- 安全闸: 只读工具直接放行; 危险工具(下载/写值/在线)需前端显式勾选 authorized
- 只读优先: 默认面板只做读; 写操作独立分区且需二次确认

启动:  python server.py            (默认监听 127.0.0.1:8765)
访问:  浏览器打开 http://127.0.0.1:8765/
停止:  在窗口按 Ctrl+C
"""
import json
import os
import sys
import threading
import traceback
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from tia_client import TiaClient, FORBIDDEN_UNLESS_AUTHORIZED, EXE, TIA_LOC

PORT = 8765
HOST = "127.0.0.1"

# ---- 全局: 单例客户端 + 串行锁 ----
_client = None
_client_lock = threading.Lock()      # 保护 client 创建与所有 call (引擎不支持并发)
_state = {"project": "", "attached": False, "ip": "192.168.0.1"}

# 危险工具: 必须前端勾"我确认"且后端收到 authorized=true 才放行
DANGEROUS = set(FORBIDDEN_UNLESS_AUTHORIZED)


def get_client():
    global _client
    with _client_lock:
        if _client is None:
            _client = TiaClient()
        return _client


def call_tool(tool, args, authorized=False, via_meta=False, timeout=240):
    """统一调用入口, 带危险工具闸门。返回 (ok, data_dict)。"""
    if tool in DANGEROUS and not authorized:
        return False, {"error": "危险操作被拦截: %s 需在面板勾选'我确认'后执行" % tool}
    try:
        c = get_client()
        r = c.call_via_meta(tool, args or {}, timeout=timeout, authorized=authorized) if via_meta \
            else c.call(tool, args or {}, timeout=timeout, authorized=authorized)
        if isinstance(r, dict) and r.get("_rpc_error"):
            return False, {"error": str(r["_rpc_error"])}
        if isinstance(r, dict) and r.get("isError"):
            return False, {"error": r.get("text", "工具返回错误")}
        return True, {"text": r.get("text", "") if isinstance(r, dict) else str(r),
                      "raw": r.get("raw") if isinstance(r, dict) else None}
    except Exception as e:
        return False, {"error": "%s: %s" % (type(e).__name__, e), "trace": traceback.format_exc(limit=3)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # 精简日志: 只打印请求行
        sys.stderr.write("[HTTP] %s %s\n" % (self.command, self.path))

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self):
        path = os.path.join(HERE, "index.html")
        if not os.path.isfile(path):
            self._send(500, {"error": "找不到 index.html"})
            return
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(200, {})

    def do_GET(self):
        p = urlparse(self.path).path
        if p in ("/", "/index.html"):
            self._send_html()
        elif p == "/api/status":
            self._send(200, {
                "ok": True,
                "engine": EXE,
                "engine_exists": os.path.isfile(EXE),
                "tia_location": TIA_LOC or "(由引擎自动检测)",
                "client_alive": _client is not None,
                "state": _state,
                "dangerous_tools": sorted(DANGEROUS),
            })
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        p = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception as e:
            self._send(400, {"ok": False, "error": "bad json: %s" % e})
            return

        try:
            if p == "/api/connect":
                self._api_connect(body)
            elif p == "/api/call":
                tool = body.get("tool", "")
                ok, data = call_tool(tool, body.get("args"),
                                     authorized=bool(body.get("authorized")),
                                     via_meta=bool(body.get("viaMeta", True)),
                                     timeout=int(body.get("timeout", 240)))
                self._send(200 if ok else 200, {"ok": ok, **data})
            elif p == "/api/live":
                self._api_live(body)
            elif p == "/api/reset":
                self._api_reset()
            else:
                self._send(404, {"ok": False, "error": "not found"})
        except Exception as e:
            self._send(200, {"ok": False, "error": "%s: %s" % (type(e).__name__, e),
                             "trace": traceback.format_exc(limit=3)})

    def _api_connect(self, body):
        project = body.get("projectName", "")
        ip = body.get("ip")
        if ip:
            _state["ip"] = ip
        seq = []
        c = get_client()
        with _client_lock:
            r1 = c.call("Connect")
            seq.append({"step": "Connect", "text": r1.get("text", "")[:400], "isError": r1.get("isError")})
            proj_text = ""
            if project:
                r2 = c.call("AttachToOpenProject", {"projectName": project})
                seq.append({"step": "AttachToOpenProject", "text": r2.get("text", "")[:400], "isError": r2.get("isError")})
                if not r2.get("isError"):
                    _state["project"] = project
                    _state["attached"] = True
            else:
                r2 = c.call("GetProject")
                proj_text = r2.get("text", "")[:400]
                seq.append({"step": "GetProject", "text": proj_text, "isError": r2.get("isError")})
        self._send(200, {"ok": True, "steps": seq, "state": _state})

    def _api_live(self, body):
        """实时值读取 (S7 只读通道), 供面板轮询。"""
        ip = body.get("ip") or _state["ip"]
        items = body.get("items", [])
        if isinstance(items, str):
            items = [s.strip() for s in items.replace("，", ",").split(",") if s.strip()]
        if not items:
            self._send(200, {"ok": False, "error": "items 为空"})
            return
        args = {"ip": ip, "itemsJson": json.dumps(items, ensure_ascii=False)}
        ok, data = call_tool("ReadPlcLiveValuesS7", args, via_meta=True, timeout=60)
        self._send(200, {"ok": ok, "ip": ip, "items": items, **data})

    def _api_reset(self):
        global _client
        with _client_lock:
            try:
                if _client:
                    _client.close()
            except Exception:
                pass
            _client = None
        _state.update({"project": "", "attached": False})
        self._send(200, {"ok": True, "msg": "引擎连接已重置, 下次调用会重新启动"})


def main():
    print("=" * 60)
    print("TIA Portal 本地桥接服务 (路线 B)")
    print("=" * 60)
    print("引擎:", EXE, "(存在)" if os.path.isfile(EXE) else "(不存在!)")
    print("TIA :", TIA_LOC or "(由引擎自动检测)")
    print("监听: http://%s:%d/" % (HOST, PORT))
    print("面板: 浏览器打开上面地址; 停止按 Ctrl+C")
    print("=" * 60)
    if not os.path.isfile(EXE):
        print("!! 警告: 找不到引擎 exe, 请检查 04_MCP引擎 是否随包解压")
    # 端口占用检测: 若已有服务在跑, 不重复启动, 直接打开浏览器并退出
    import socket
    _s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _s.settimeout(0.5)
    _busy = _s.connect_ex((HOST, PORT)) == 0
    _s.close()
    if _busy:
        print("\n[提示] 端口 %d 已有服务在运行 (可能之前双击的窗口还开着)。" % PORT)
        print("       面板其实已经可用, 正在为你打开浏览器。")
        print("       若要重启服务: 关掉之前那个黑色窗口, 再双击本文件。")
        try:
            webbrowser.open("http://%s:%d/" % (HOST, PORT))
        except Exception:
            pass
        return
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    # 服务起来后自动打开浏览器 (延时 1s, 失败也不影响服务)
    def _open_browser():
        try:
            import time
            time.sleep(1)
            webbrowser.open("http://%s:%d/" % (HOST, PORT))
        except Exception:
            pass
    threading.Thread(target=_open_browser, daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n正在停止...")
    finally:
        with _client_lock:
            if _client:
                _client.close()
        srv.server_close()
        print("已停止")


if __name__ == "__main__":
    main()
