# J6 气流粉碎系统 — PLC + WinCC Unified HMI 组态/调试工具集

本仓库配套 `J6_气流粉碎_调试SOP.md`，把"从零到可下载调试"的自动化脚本固化下来，便于在干净环境复现组态、下载与排错。

## 适用项目
- 陕西天宇 J6 气流粉碎系统
- TIA Portal V21 + STEP 7 + WinCC Unified Comfort
- S7-1200 (CPU 1214C) + MTP1200 Unified Pro (6AV2128-3MB06)
- HMI 画面分辨率 1280x800

## 目录结构
- `J6_气流粉碎_调试SOP.md` — 完整 SOP（软件清单、环境、工程结构、MCP 工具签名、黄金组态顺序、下载调试、踩坑速查、新对话起步提示）
- `mcp_client.py` — JSON-RPC 客户端，驱动 TIA MCP 服务（必用）
- `hmi_step1_tags.py` — 建 HMI 标签表 J6_Tags（63 个绝对地址）
- `hmi_step2_screens.py` — 创建 4 个 1280x800 画面 + 布局
- `hmi_step3_bind.py` / `hmi_step4_rebind.py` — IO 域/命令/导航绑定（历史步骤）
- `hmi_fix_1280.py` — **推荐**：一步到位重建 4 画面 + 全绑定 + 导航
- `hmi_test_main.py` — 主画面端到端验证示例
- `verify_and_compile.py` — 跨画面回读校验 + 离线编译
- `compile_offline.py` / `go_offline.py` — 离线/编译辅助
- `tools_list_v2711.json` — MCP V2.7.11 工具清单（速查）
- `J6_IO_List_export.xml` — IO 列表导出（标签参考）

## 关于 MCP 工具交付包（重要）
`TIA_MCP_Delivery_v2.7.11`（含 `TiaMcpServer.exe`）是第三方自动化工具，**未纳入本仓库**（体积大且为交付物）。
获取方式：见 SOP 第 1 节"需要下载/安装的软件清单"，从你本地的 `TIA_MCP_Delivery_v2.7.11_20261107.zip` 解压，或向原交付方获取。
解压后把 `runtime/v21/TiaMcpServer.exe` 路径在 `mcp_client.py` 里指向即可。

## 快速开始
1. 安装 TIA Portal V21（含 Openness）、.NET 运行时、Python 3.10+（`pip install pythonnet`）。
2. 解压 MCP 交付包，确认 `mcp_client.py` 中 `TiaPortalLocation` 与 `TiaMcpServer.exe` 路径正确。
3. 打开 TIA Portal 工程（SOP 中的 Test.ap21 示例），保持运行。
4. 运行 `python hmi_fix_1280.py` 完成 HMI 组态，再用 TIA Portal GUI 传送 HMI 到面板。

> 注意：PLC/HMI 的**下载**仍需在 TIA Portal GUI 完成；MCP 只负责组态/编译。
> 文中 IP（192.168.0.x）、工程路径均为示例/你的内网配置，请按实际修改。

## 许可
脚本仅供本项目调试使用；MCP 交付包版权归原交付方所有。
