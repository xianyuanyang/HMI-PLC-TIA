# -*- coding: utf-8 -*-
"""极简 MCP stdio 客户端，用于驱动本地 TiaMcpServer.exe。"""
import json
import os
import queue
import subprocess
import sys
import threading
import time

EXE = r"D:\系统\桌面\workbuddy\TIA_Tools\TIA_MCP_v2711\TIA_MCP_Delivery_v2.7.11\runtime\v21\TiaMcpServer.exe"
TIA_LOC = r"D:\Program Files\Siemens\Automation\Portal V21"


class MCP:
    def __init__(self, extra_args=None):
        env = dict(os.environ)
        env["TiaPortalLocation"] = TIA_LOC
        env["TIA_MCP_ATTACH_TIMEOUT_MS"] = "15000"
        self.p = subprocess.Popen(
            [EXE] + (extra_args or []),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", bufsize=1, env=env,
        )
        self.q = queue.Queue()
        self.err_lines = []
        self._id = 0
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self):
        for line in self.p.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                self.q.put(json.loads(line))
            except Exception:
                pass

    def _read_stderr(self):
        for line in self.p.stderr:
            self.err_lines.append(line.rstrip())

    def _next_id(self):
        self._id += 1
        return self._id

    def send(self, method, params=None, notify=False):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        rid = None
        if not notify:
            rid = self._next_id()
            msg["id"] = rid
        self.p.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
        self.p.stdin.flush()
        return rid

    def request(self, method, params=None, timeout=90):
        rid = self.send(method, params)
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                m = self.q.get(timeout=1)
            except queue.Empty:
                continue
            if m.get("id") == rid:
                return m
            self.q.put(m)  # 其它消息放回去
        raise TimeoutError("%s 超时 (rid=%s)" % (method, rid))

    def initialize(self):
        r = self.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "workbuddy", "version": "1.0"},
        })
        self.send("notifications/initialized", {}, notify=True)
        return r

    def tools(self):
        r = self.request("tools/list", {}, timeout=120)
        return r.get("result", {}).get("tools", [])

    def call(self, name, args=None, timeout=180):
        return self.request("tools/call", {"name": name, "arguments": args or {}}, timeout=timeout)

    def close(self):
        try:
            self.p.stdin.close()
        except Exception:
            pass
        try:
            self.p.terminate()
        except Exception:
            pass


def text_of(resp):
    """提取 MCP 工具返回的文本内容。"""
    out = []
    for c in resp.get("result", {}).get("content", []):
        if c.get("type") == "text":
            out.append(c.get("text", ""))
    return "\n".join(out)


if __name__ == "__main__":
    m = MCP()
    try:
        init = m.initialize()
        print("initialize:", json.dumps(init.get("result", {}), ensure_ascii=False)[:400])
        tools = m.tools()
        print("工具总数:", len(tools))
        with open(r"D:\系统\桌面\workbuddy\TIA_Tools\tools_list.json", "w", encoding="utf-8") as f:
            json.dump(tools, f, ensure_ascii=False, indent=1)
        for t in tools:
            print("-", t["name"], "|", (t.get("description") or "").replace("\n", " ")[:110])
    finally:
        m.close()
