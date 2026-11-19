"""Local stdio MCP client for TIA Portal Openness MCP (v2.7.11 / V21).

Bypasses the WorkBuddy UI MCP loader: starts TiaMcpServer.exe directly and
talks JSON-RPC 2.0 over stdin/stdout.

Policy: download / online-write tools are blocked by default. They can only be
invoked with an explicit `authorized=True` argument, which must be passed only
after the user has directly asked for that online action in the conversation.
"""
import json
import os
import queue
import subprocess
import threading
import time

# ---- 路径解析：不再硬编码盘符，按脚本自身位置推导，找不到再退回候选路径 ----
_HERE = os.path.dirname(os.path.abspath(__file__))

_EXE_CANDIDATES = [
    # 路线B面板内置引擎（04_MCP引擎 直接是引擎根目录，新电脑最稳）
    os.path.join(_HERE, "04_MCP引擎", "runtime", "v21", "TiaMcpServer.exe"),
    os.path.join(_HERE, "04_MCP引擎", "TIA_MCP_Delivery_v2.7.11", "runtime", "v21", "TiaMcpServer.exe"),
    # 与解压后的工具包同级：../博图调试工具包_2026-11-19/04_MCP引擎/...
    os.path.join(_HERE, "..", "博图调试工具包_2026-11-19", "04_MCP引擎", "TIA_MCP_Delivery_v2.7.11", "runtime", "v21", "TiaMcpServer.exe"),
    # 通用相对路径（旧手册布局 / 常见布局）
    os.path.join(_HERE, "..", "04_MCP引擎", "TIA_MCP_Delivery_v2.7.11", "runtime", "v21", "TiaMcpServer.exe"),
    os.path.join(_HERE, "TIA_MCP_Delivery_v2.7.11", "runtime", "v21", "TiaMcpServer.exe"),
    os.path.join(_HERE, "runtime", "v21", "TiaMcpServer.exe"),
    r"D:\系统\桌面\workbuddy\TIA_Tools\TIA_MCP_v2711\TIA_MCP_Delivery_v2.7.11\runtime\v21\TiaMcpServer.exe",
    r"D:\系统\桌面\workbuddy\TIA_Tools\tia-portal-openness-mcp\runtime\v21\TiaMcpServer.exe",
]
EXE = next((p for p in _EXE_CANDIDATES if os.path.isfile(p)), _EXE_CANDIDATES[0])

_TIA_CANDIDATES = [
    os.environ.get("TiaPortalLocation", ""),
    r"D:\Program Files\Siemens\Automation\Portal V21",
    r"C:\Program Files\Siemens\Automation\Portal V21",
    r"D:\Program Files\Siemens\Automation\Portal V20",
    r"C:\Program Files\Siemens\Automation\Portal V20",
]
TIA_LOC = next((p for p in _TIA_CANDIDATES
                if p and os.path.isdir(os.path.join(p, "PublicAPI"))), "")

ARGS = [EXE, "--tia-major-version", "21"]
if TIA_LOC:
    ARGS += ["--tia-portal-location", TIA_LOC]

# Online / write-to-PLC tools. Blocked unless the caller passes authorized=True,
# which is only allowed after the user explicitly asked for that action.
FORBIDDEN_UNLESS_AUTHORIZED = {
    "DownloadToPlc", "GoOnline", "GoOffline", "GoOfflineAll",
    "SetWatchTableModifyValue", "InvokeObject", "InvokeService",
    "DeletePlcBlock", "DeletePlcTagTable", "DeletePlcType", "DeletePlcWatchTable",
    "DeletePlcExternalSource",
}

# Kept for backward compatibility with earlier scripts.
FORBIDDEN = FORBIDDEN_UNLESS_AUTHORIZED


class TiaClient:
    def __init__(self, args=None, verbose=False):
        self.p = subprocess.Popen(
            args or ARGS,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
            cwd=os.path.dirname(EXE),
        )
        self.q = queue.Queue()
        self.stderr_lines = []
        self.verbose = verbose
        self.rid = 0
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()
        self._initialize()

    def _read_stdout(self):
        try:
            for line in self.p.stdout:
                self.q.put(line.rstrip("\n"))
        finally:
            self.q.put(None)

    def _read_stderr(self):
        try:
            for line in self.p.stderr:
                self.stderr_lines.append(line.rstrip())
        except Exception:
            pass

    def _send(self, obj):
        self.p.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n")
        self.p.stdin.flush()

    def _wait(self, rid, timeout=180):
        end = time.time() + timeout
        while time.time() < end:
            try:
                line = self.q.get(timeout=1)
            except queue.Empty:
                continue
            if line is None:
                return {"error": {"message": "server stdout closed"}}
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                if self.verbose:
                    print("NON_JSON:", line[:200])
                continue
            if obj.get("id") == rid:
                return obj
            if self.verbose:
                print("OTHER_MSG:", str(obj)[:200])
        return {"error": {"message": "timeout"}}

    def _initialize(self):
        self.rid += 1
        rid = self.rid
        self._send({
            "jsonrpc": "2.0", "id": rid, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "tia-local-client", "version": "1.0"},
            },
        })
        r = self._wait(rid, timeout=90)
        if "error" in r:
            raise RuntimeError("initialize failed: " + str(r["error"]))
        self.server_info = r.get("result", {}).get("serverInfo", {})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    def raw_call(self, method, params=None, timeout=180):
        self.rid += 1
        rid = self.rid
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}})
        return self._wait(rid, timeout=timeout)

    def list_tools(self, timeout=90):
        r = self.raw_call("tools/list", {}, timeout=timeout)
        return r.get("result", {}).get("tools", [])

    def call(self, name, args=None, timeout=240, authorized=False):
        if name in FORBIDDEN_UNLESS_AUTHORIZED and not authorized:
            raise RuntimeError("BLOCKED by project policy (needs explicit user authorization): " + name)
        r = self.raw_call("tools/call", {"name": name, "arguments": args or {}}, timeout=timeout)
        if "error" in r:
            return {"_rpc_error": r["error"]}
        result = r.get("result", {})
        out = {"isError": result.get("isError", False)}
        texts = [c.get("text", "") for c in result.get("content", []) if isinstance(c, dict)]
        out["text"] = "\n".join(texts)
        out["raw"] = result
        return out

    def call_via_meta(self, name, args, timeout=240, authorized=False):
        """Call a full-roster tool through CallTool(name, argumentsJson)."""
        if name in FORBIDDEN_UNLESS_AUTHORIZED and not authorized:
            raise RuntimeError("BLOCKED by project policy (needs explicit user authorization): " + name)
        payload = json.dumps(args, ensure_ascii=False)
        return self.call("CallTool", {"name": name, "argumentsJson": payload},
                         timeout=timeout, authorized=authorized)

    def text(self, r, limit=None):
        t = r.get("text", "") if isinstance(r, dict) else str(r)
        return t[:limit] if limit else t

    def close(self):
        try:
            self.p.terminate()
            self.p.wait(timeout=8)
        except Exception:
            try:
                self.p.kill()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def save(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return path


if __name__ == "__main__":
    # 自检：只列出工具数量，不打开工程、不写任何东西
    print("EXE     :", EXE, "(存在)" if os.path.isfile(EXE) else "(不存在!)")
    print("TIA_LOC :", TIA_LOC or "(未探测到，将由引擎自行检测)")
    if not os.path.isfile(EXE):
        raise SystemExit("找不到 TiaMcpServer.exe，请检查交付包是否完整解压。")
    with TiaClient() as c:
        tools = c.list_tools()
        print("连接成功，工具数 :", len(tools))
        print("前 10 个工具     :", ", ".join(t["name"] for t in tools[:10]))
        print("\n用法示例：")
        print('  from tia_client import TiaClient')
        print('  with TiaClient() as c:')
        print('      print(c.text(c.call("Connect")))')
        print('      print(c.text(c.call("GetProject")))')

