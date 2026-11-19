# 博图操作面板（路线 B · 本地直连版）

一个跑在浏览器里的博图操作台。**双击 `启动面板.bat` 即可用**，无需 AI 对话在线——面板直接通过本地引擎操作 TIA Portal。

---

## 1. 它和"对话里那个面板"有什么不同

| | 对话内 HTML 面板（路线 A） | 本面板（路线 B） |
|---|---|---|
| 谁执行 | 按钮发指令给 AI，AI 调工具 | 面板 → 本地服务 → 引擎，**不经 AI** |
| 实时值 | 需 AI 读后回显 | **自动轮询，每 1.5 秒刷新** |
| 部署 | 零部署 | 双击 bat（需 Python 3） |
| 安全闸 | AI 把关 | 后端二次授权闸（危险操作默认拦截） |

## 2. 架构

```
浏览器面板 (index.html)
    ↓ HTTP (localhost:8765)
本地桥接服务 (server.py, 纯 Python 标准库)
    ↓ stdio JSON-RPC 2.0 (长连接, 串行化)
TiaMcpServer.exe (04_MCP引擎, v21)
    ↓ TIA Openness API
TIA Portal V21
```
数据全在本机，不经云端。

## 3. 新电脑使用步骤

1. **装 TIA Portal V21**（勾 Openness）+ 把当前用户加入 `Siemens TIA Openness` 组并**注销重登**（详见工具包的《TIA_V21从零到一调试手册》）。
2. **装 Python 3**（本面板用标准库，无需 `pip install` 任何包）。
3. **拷贝整个 `博图操作面板` 文件夹**到新电脑（内含 04_MCP引擎，自包含）。
4. **先手动打开 TIA V21 并打开目标工程**。
5. **双击 `启动面板.bat`** → 浏览器自动打开 `http://127.0.0.1:8765/`。
6. 面板里填工程名、PLC IP → 点【连接博图】→ 开始操作。

手动启动方式：命令行 `cd` 到本目录，运行 `python server.py`，再浏览器打开上面的地址。

## 4. 面板功能分区

1. **会话与连接**：连接博图 / 重置引擎 / 状态查看。
2. **浏览与块操作**：常用只读工具一键执行（GetState/GetProject/GetProjectTree/GetDevices）；任意工具名 + JSON 参数走 CallTool 元调用，覆盖全部工具。
3. **在线监视**：填变量地址 → 读一次 / 开自动轮询（1.5s）。走 S7 只读通道，不写 PLC。
4. **受控写入与下载**（危险区）：默认禁用，**必须勾选"我确认现场安全"才启用**；后端对 DownloadToPlc 等 12 个危险工具有二次授权闸，未授权一律拦截。

## 5. 安全设计

- **只读优先**：浏览、导出、在线读值是常规操作。
- **危险工具默认拦截**：`DownloadToPlc`、`GoOnline/Offline`、`SetWatchTableModifyValue`、各类 `Delete*` 等共 12 个，前端不勾确认 + 后端无 authorized=true，一律不放行。
- **下载参数**：默认 `keepActualValues=true`（保留 DB 实际值）、`startAfterDownload=false`（保持 STOP），与 J6 手册一致。

## 6. 常见问题

- **面板打不开 / 状态显示"服务未启动"**：确认 bat 窗口没关、Python 能运行、端口 8765 没被占用。
- **引擎缺失**：确认 `04_MCP引擎` 文件夹完整；`python -c "import tia_client; print(tia_client.EXE)"` 看路径。
- **连接报 UAC**：先在 TIA GUI 里打开工程，再点连接。
- **实时值读到乱数/读不到**：DB 是否优化访问、地址是否针对本工程重新标定（见《DB1地址速查表》）；G2 CPU 的 S7 直读方式需另行确认。
- **改了引擎路径**：编辑 `tia_client.py` 顶部 `_EXE_CANDIDATES`，或用环境变量 `TiaPortalLocation` 指定 TIA 安装目录。

---
*路线 B 本地直连面板 · 与《博图调试工具包》配套 · 2026-11-19*
