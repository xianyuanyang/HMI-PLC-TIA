# J6 气流粉碎系统 — PLC + WinCC Unified HMI 下载/调试 SOP

> 目的：把"从零到可下载调试"的完整路径固化下来。新对话只要读这一份，就能在干净环境里复现组态、下载与排错。
> 适用项目：陕西天宇 J6 气流粉碎系统，TIA Portal V21，S7-1200 + MTP1200 Unified Pro。
> 最后更新：2026-11-13

---

## 0. 一页结论（先看这个）

- **PLC**：S7-1200（CPU 1214C），IP `192.168.0.1`，程序 = OB1 + DB1(参数) + DB2(命令) + DB3(状态)。已下载，**必须切到 RUN 实时数据才显示**。
- **HMI**：MTP1200 Unified Pro（`6AV2128-3MB06`），IP `192.168.0.2`，软件 `HMI_RT_1`，4 个画面 `Screen_J6_Main / Motors / Valves / JetMill`，连接 `HMI_Connection_1`（S7-1200/1500 通道，非集成），HMI 标签表 `J6_Tags`（63 个绝对地址标签）。
- **PC（工程机）**：IP `192.168.0.240`。
- **画面分辨率**：**1280×800（面板原生分辨率）**。所有元素必须落在 0~1280 / 0~800 内，否则被裁切（导航按钮之前因放在 y=950 而看不到）。
- **HMI 下载只能走 TIA Portal GUI**（MCP 没有传送工具，且传送确认框跨进程封送会失败）。MCP 只负责组态/编译。
- **重做画面的正确顺序**：先 `ApplyUnifiedHmiScreenDesignJson` 布局 → 再 `BindUnifiedHmiTagDynamization` 绑定。反序会把绑定清空。

---

## 1. 需要下载/安装的软件清单

| 软件 | 版本/说明 | 获取方式 | 用途 |
|---|---|---|---|
| **TIA Portal** | **V21**（含 STEP 7 + WinCC Unified Comfort + Openness） | 西门子工业在线支持 (Siemens Industry Online Support) 下载 | 工程组态、编译、下载、HMI 传送 |
| **TIA Portal Update** | V21 Update 2 Hotfix 1（本工程 LastUsed 版本） | 同上，补丁集 | 工程兼容 |
| **.NET 运行时** | 与 MCP 交付包匹配的 .NET（TiaMcpServer.exe 依赖） | 微软官网 / 交付包自带 | 运行 MCP 服务 |
| **MCP 工具交付包** | `TIA_MCP_Delivery_v2.7.11`（本地交付，含 `TiaMcpServer.exe`） | 本地路径 `(MCP 交付包未随仓库发布，见 README)`，解压后 `...\runtime\v21\TiaMcpServer.exe` | 通过 Openness 自动化组态 HMI/PLC |
| **Python 3** | 3.10+（仅当要用本地 Python 驱动脚本时需要） | python.org | 运行 `mcp_client.py` 等驱动脚本 |
| **pythonnet** | `pip install pythonnet`（仅 Python 直连 Openness 时需要） | PyPI | 让 Python 调用 `Siemens.Engineering.*` DLL |
| **WinCC Unified 运行/传送** | 随 TIA Portal 安装 | — | HMI 面板传送与运行 |

> 说明：日常"改画面/组态"用 **MCP 交付包 + Python 驱动脚本**即可；真正的 PLC/HMI **下载**仍需在 TIA Portal GUI 里点。

---

## 2. 环境准备（一次性）

1. 安装 TIA Portal V21（勾选 STEP 7、WinCC Unified Comfort、Openness/Openness API）。
2. 安装 .NET 运行时（若 TiaMcpServer.exe 启动报缺运行时）。
3. 解压 `TIA_MCP_Delivery_v2.7.11_20261107.zip` 到 `本仓库根目录\TIA_MCP_v2711\`。
4. （可选）安装 Python 3.10+ 与 `pip install pythonnet`。
5. 把工程机网卡 IP 设为 `192.168.0.240`，子网掩码 `255.255.255.0`，确保能 ping 通 `192.168.0.1`（PLC）和 `192.168.0.2`（HMI）。

---

## 3. 工程结构（务必先理解）

工程文件：`<你的TIA工程目录>\Test.ap21`

### 3.1 PLC 侧（G2_PLC_1 / CPU 1214C @ 192.168.0.1）
- **OB1**：主循环，调用逻辑。
- **DB1 `Prm_*`（参数）**：`Prm_SP_Feed`(DBD0)、`Prm_SP_Grind`(DBD4)、`Prm_MO201_Speed`(DBD50)、`Prm_MO101_Speed`(DBD54)、`Prm_MO601_Speed`(DBD58)。
- **DB2 `Cmd_*`（命令位/手动值）**：电机 Start/Stop/Reset 位 `0.0~1.2`；`Cmd_Jet_Enable`(1.3)、`Cmd_Jet_Auto`(1.4)；阀门 Open/Close 位 `10.0~12.5`；`Cmd_Jet_ManFeed`(DBD2)、`Cmd_Jet_ManGrind`(DBD6)。
- **DB3 `St_*`（状态/反馈）**：`St_EMOk`(0.0)；运行/报警位 `50.0~51.1`；12 个 Real：`St_P101~St_T104`、`St_T101`、`St_MO601FB`、`St_OutFeed/OutGrind`、`St_ErrFeed/ErrGrind`（DBD2~DBD46）。
- **关键设置**：CPU 属性里必须勾选 **"允许从远程伙伴（PLC/HMI/…）通过 PUT/GET 通信访问"**，否则 HMI 非集成连接读不到数据。

### 3.2 HMI 侧（HMI_1 / HMI_RT_1 @ 192.168.0.2）
- **连接** `HMI_Connection_1`：S7-1200/1500 通道，**非集成连接**（HMI 标签用绝对地址）。
- **HMI 标签表** `J6_Tags`：63 个标签，全部按绝对地址绑定（如 `St_P101 → %DB3.DBD2`），与 PLC 的 DB 一一对应。
- **4 个画面**（1280×800）：
  - `Screen_J6_Main`：报警×6、压力×5、电机运行×4、3 个导航按钮（电机/阀门/气流粉碎）。
  - `Screen_J6_Motors`：4 台电机（转速给定 IO + 启动/停止/复位按钮 + 运行指示），返回主画面。
  - `Screen_J6_Valves`：11 个阀（开/关按钮），返回主画面。
  - `Screen_J6_JetMill`：进料/粉碎两个 PID 回路 + 手动输出 + 使能/模式切换 + 监视量，返回主画面。

---

## 4. 用 MCP 自动化组态（核心）

### 4.1 连接方式
本地驱动脚本 `mcp_client.py` 会**启动子进程 `TiaMcpServer.exe`** 并通过 stdio(JSON-RPC) 与之通信；该服务再 **Attach 到已经在运行的 TIA Portal 工程实例**（所以 TIA Portal 必须先把工程打开）。

```
mcp_client.py  ──stdio──▶  TiaMcpServer.exe  ──Openness──▶  TIA Portal(已打开 Test.ap21)
```

最小可用骨架（`mcp_client` 已封装好）：
```python
from mcp_client import MCP, text_of
m = MCP()
m.initialize()
print(text_of(m.call('Connect', timeout=180)))           # 挂载到 TIA Portal
# 所有 HMI/PLC 高级操作都走 CallTool 派发：
r = m.call('CallTool', {'name': '工具名', 'argumentsJson': '{...}'}, timeout=600)
```
> 注意：`TiaMcpServer.exe` 需要环境变量 `TiaPortalLocation`（脚本里已设为 `<TIA Portal V21 安装目录>`）。

### 4.2 关键工具签名速查（V2.7.11）
| 工具 | 关键参数 | 说明 |
|---|---|---|
| `Connect` | — | 挂载到已打开的 TIA Portal 工程 |
| `EnsureUnifiedHmiScreen` | `hmiSoftwarePath, screenName, width, height` | 创建/校验画面（**尺寸=1280/800**） |
| `ApplyUnifiedHmiScreenDesignJson` | `hmiSoftwarePath, screenName, designJson, strict=true` | 一次性铺整个画面布局（Text/Button/IOField）。**会清空元素已有绑定** |
| `BindUnifiedHmiTagDynamization` | `hmiSoftwarePath, screenName, itemName, propertyName='ProcessValue', tagName, dataType` | 把 IO 域的 ProcessValue 动态化绑到 HMI 标签 |
| `BindUnifiedHmiButtonPressedTag` | `hmiSoftwarePath, screenName, buttonName, tagName` | 按钮"按下=1、松开=0"的瞬态脉冲绑定（适合启停/开关阀命令） |
| `EnsureUnifiedHmiButtonAction` | `hmiSoftwarePath, screenName, buttonName, eventType='Tapped', actionKind='set-bit'\|'reset-bit'\|'toggle-bit', targetTag` | 置位/复位型按钮动作（适合使能/模式锁存） |
| `EnsureUnifiedHmiButtonEventHandler` | `hmiSoftwarePath, screenName, buttonName, eventType='Tapped'` | 确保按钮事件处理器存在 |
| `SetUnifiedHmiButtonEventScriptCode` | `hmiSoftwarePath, screenName, buttonName, eventType='Tapped', scriptCode, syntaxCheck=false` | 给事件写 JS 脚本（导航跳转用它） |
| `CompileAndDiagnoseHmi` / `CompileAndDiagnosePlc` | `hmiSoftwarePath` / `plcSoftwarePath` | 编译并诊断（**会与在线态交互，工程在线时可能报 "online mode 不允许"**） |
| `CompileSoftware` | `softwarePath` | **离线编译首选**：返回 `errorCount/warningCount`。本次 4 画面重建后编译 = 0 错误 0 警告 |
| `SaveProject` | — | 把内存改动落盘（"Local project saved"）。也可在 GUI 按 Ctrl+S |
| `DownloadToPlc` | — | 下载 PLC（MCP 能做；HMI 传送不行） |
| `GetObjectProperty` | `objectKind='HmiScreenItem', objectPath='HMI_RT_1:画面:元素', propertyPath` | 回读属性做校验 |

### 4.3 画面组态的"黄金顺序"（别踩坑）
```
EnsureUnifiedHmiScreen(1280,800)
  → ApplyUnifiedHmiScreenDesignJson(布局)        # 先铺元素
  → BindUnifiedHmiTagDynamization(IO域→ProcessValue)   # 后绑定
  → BindUnifiedHmiButtonPressedTag / EnsureUnifiedHmiButtonAction  # 命令按钮
  → EnsureUnifiedHmiButtonEventHandler + SetUnifiedHmiButtonEventScriptCode  # 导航
  → CompileAndDiagnoseHmi
```
**导航跳转脚本**（不能用 EnsureUnifiedHmiButtonAction 的 change-screen）：
```python
cvia('EnsureUnifiedHmiButtonEventHandler',
     {'hmiSoftwarePath':'HMI_RT_1','screenName':'Screen_J6_Main',
      'buttonName':'btnGoMotors','eventType':'Tapped'})
cvia('SetUnifiedHmiButtonEventScriptCode',
     {'hmiSoftwarePath':'HMI_RT_1','screenName':'Screen_J6_Main',
      'buttonName':'btnGoMotors','eventType':'Tapped',
      'scriptCode':'ActivateScreen("Screen_J6_Motors");',
      'syntaxCheck':False})
```

### 4.4 现成本地脚本（按依赖顺序）
都在 `本仓库根目录\`：
- `mcp_client.py` — JSON-RPC 客户端（必用）。
- `hmi_step1_tags.py` — 建 HMI 标签表 `J6_Tags`（63 个绝对地址）。
- `hmi_step2_screens.py` — 创建 4 个画面 + 布局。
- `hmi_step3_bind.py` — IO 域/命令按钮/导航绑定（旧版，导航用的 change-screen 已废弃）。
- `hmi_step4_rebind.py` — 按绝对地址重绑标签。
- **`hmi_fix_1280.py` — 当前推荐：按 1280×800 重建 4 画面 + 全绑定 + 导航（一步到位）**。

运行示例（工程已在 TIA Portal 打开）：
```bash
cd 本仓库根目录
python hmi_fix_1280.py
```

---

## 5. 下载与调试步骤（当天实际走通的路径）

### 5.1 PLC
1. TIA Portal 打开 `Test.ap21`。
2. 编译 PLC（或 `CompileAndDiagnosePlc`）。
3. 下载 PLC：`DownloadToPlc`（或 GUI 下载到设备），接口选 PN/IE。
4. **在线后把 CPU 切到 RUN**（这是实时数据能显示的前提！STOP 时 WinCC Unified RT 会报连接中断）。

### 5.2 HMI
1. 跑 `hmi_fix_1280.py` 完成组态（或分步 step1~4）。
2. 离线编译校验：用 `CompileSoftware`（`softwarePath:'HMI_RT_1'`）看 `errorCount/warningCount`；**不要用 `CompileAndDiagnoseHmi`**——工程在线时会报 "online mode 不允许"。
3. 保存工程：`SaveProject`（MCP）或在 TIA Portal 里 **Ctrl+S**。
4. 选中 HMI_1 → **"下载到设备 / 传送"**（用 WinCC Unified 传送向导，选 PN/IE，目标 192.168.0.2）。传送会自动再编译一次并报告错误。
   - ⚠️ 这一步**必须人工在 GUI 完成**：MCP 没有 HMI 传送工具，且传送时的确认对话框无法跨进程封送。

### 5.3 面板验证清单
- [ ] 4 个画面都能看到，且**全部内容在 1280×800 内**（无被裁切）。
- [ ] 主画面 3 个导航按钮（电机控制/阀门控制/气流粉碎）可见且**点击能跳转**。
- [ ] 各子画面"返回主画面"可用。
- [ ] IO 域显示**实时数值**（压力/温度/运行位/状态位）。
- [ ] 命令按钮可控（启停电机、开关阀、使能/模式切换）。

---

## 6. 今天踩过的坑（排错速查）

1. **导航按钮"看不到"**：之前画面按 1920×1080 布局，导航按钮放在 y=950，超出面板 800 高度被裁掉 → 全部改到 1280×800 且按钮落在 y≤800。
2. **IO 域不显示数据（ProcessValue 为空）**：`ApplyUnifiedHmiScreenDesignJson` 会清空元素绑定，旧流程在绑定之后又跑了设计 → 顺序改成"先设计后绑定"即解决。校验方法：用 `GetObjectProperty` 读 `Dynamizations`，应能看到 `TagDynamization` 项。
3. **画面与 PLC 连不上/不显示实时数据**：
   - 根因①：CPU 在 STOP → 切 RUN。
   - 根因②：IO 域 ProcessValue 没真正动态化（Dynamizations 为空）→ 重新绑定。
   - 根因③：CPU 没开 PUT/GET 访问 → 勾选允许。
   - 根因④：HMI 连接 `HMI_Connection_1` 用错驱动（必须是 S7-1200/1500 通道，非集成）→ 检查连接参数。
4. **导航用 `EnsureUnifiedHmiButtonAction(actionKind='change-screen')` 失败**：该工具只支持 set/reset/toggle-bit。改用 `SetUnifiedHmiButtonEventScriptCode` + `ActivateScreen("画面名");`。
5. **命令按钮语义**：瞬态脉冲（启停/开关阀）用 `BindUnifiedHmiButtonPressedTag`；锁存置/复位（使能/模式）用 `EnsureUnifiedHmiButtonAction(set-bit/reset-bit)`。
6. **pythonnet 直连 Openness 报错** `GetService[HmiTarget]` 类型约束冲突：TIA Portal 进程加载的程序集与脚本加载的存在"双加载"导致类型身份不一致。结论：**优先用 MCP 工具**，不要自己用 pythonnet 调 `HmiTarget` 泛型；若必须直连，要确保同一程序集只加载一次。
7. **HMI 编译报 "online mode 不允许"**：`CompileAndDiagnoseHmi` 会与在线态交互，工程在线时失败。改用 `CompileSoftware(softwarePath)` 做离线编译；或者在 TIA Portal GUI 传送时自动编译。本次 4 画面重建后 `CompileSoftware` = 0 错误 0 警告。

---

## 7. 给"新对话"的起步提示（直接复制用）

> 我要继续调试 J6 气流粉碎系统的 TIA Portal 工程（路径 `<你的TIA工程目录>\Test.ap21`）。
> 已知：S7-1200(192.168.0.1) + MTP1200 Unified Pro(192.168.0.2)，HMI 软件 `HMI_RT_1`，画面 1280×800，连接 `HMI_Connection_1`，HMI 标签表 `J6_Tags`。
> 自动化走 MCP 交付包 `TIA_MCP_Delivery_v2.7.11`（exe 在 `(MCP 交付包未随仓库发布，见 README)`），由 `本仓库根目录\mcp_client.py` 驱动。
> 改画面用 `hmi_fix_1280.py`；组态顺序必须"先 ApplyUnifiedHmiScreenDesignJson 后 BindUnifiedHmiTagDynamization"；导航用 `SetUnifiedHmiButtonEventScriptCode` 写 `ActivateScreen(...)`。HMI 下载只能在 TIA Portal GUI 传送。先看 `J6_气流粉碎_调试SOP.md`。

---

## 8. 文件索引（本机）
- 工程：`<你的TIA工程目录>\Test.ap21`
- 工具/脚本：`本仓库根目录\`（含 `mcp_client.py`、`hmi_fix_1280.py`、MCP 交付包解压目录 `TIA_MCP_v2711\`）
- 本 SOP：`本仓库根目录\J6_气流粉碎_调试SOP.md`
