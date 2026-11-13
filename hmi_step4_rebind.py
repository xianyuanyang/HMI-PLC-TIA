# -*- coding: utf-8 -*-
"""HMI 第四步：非集成连接 -> 绝对地址重绑（偏移已经 snap7 双重验证）。"""
import sys, os, json
sys.path.insert(0, r'D:\系统\桌面\workbuddy\TIA_Tools')
os.environ['TIA_MCP_ATTACH_TIMEOUT_MS'] = '90000'
from mcp_client import MCP, text_of

HMI = 'HMI_RT_1'
PLC = 'G2_PLC_1'
CONN = 'HMI_Connection_1'
TABLE = 'J6_Tags'

# DB2 = Cmd: 13 命令 bool 0.0~1.4 | ManFeed DBD2 | ManGrind DBD6 | 22 阀 bool 10.0~12.5
CMD_BOOL = [
    ('Cmd_MO201_Start', '%DB2.DBX0.0'), ('Cmd_MO201_Stop', '%DB2.DBX0.1'), ('Cmd_MO201_Reset', '%DB2.DBX0.2'),
    ('Cmd_MO601_Start', '%DB2.DBX0.3'), ('Cmd_MO601_Stop', '%DB2.DBX0.4'), ('Cmd_MO601_Reset', '%DB2.DBX0.5'),
    ('Cmd_MO601B_Start', '%DB2.DBX0.6'), ('Cmd_MO601B_Stop', '%DB2.DBX0.7'),
    ('Cmd_MO101_Start', '%DB2.DBX1.0'), ('Cmd_MO101_Stop', '%DB2.DBX1.1'), ('Cmd_MO101_Reset', '%DB2.DBX1.2'),
    ('Cmd_Jet_Enable', '%DB2.DBX1.3'), ('Cmd_Jet_Auto', '%DB2.DBX1.4'),
    ('Cmd_VA101_Open', '%DB2.DBX10.0'), ('Cmd_VA101_Close', '%DB2.DBX10.1'),
    ('Cmd_VA102_Open', '%DB2.DBX10.2'), ('Cmd_VA102_Close', '%DB2.DBX10.3'),
    ('Cmd_VA103_Open', '%DB2.DBX10.4'), ('Cmd_VA103_Close', '%DB2.DBX10.5'),
    ('Cmd_VA104_Open', '%DB2.DBX10.6'), ('Cmd_VA104_Close', '%DB2.DBX10.7'),
    ('Cmd_VA105_Open', '%DB2.DBX11.0'), ('Cmd_VA105_Close', '%DB2.DBX11.1'),
    ('Cmd_VA106_Open', '%DB2.DBX11.2'), ('Cmd_VA106_Close', '%DB2.DBX11.3'),
    ('Cmd_VAPC1_Open', '%DB2.DBX11.4'), ('Cmd_VAPC1_Close', '%DB2.DBX11.5'),
    ('Cmd_VAPC2_Open', '%DB2.DBX11.6'), ('Cmd_VAPC2_Close', '%DB2.DBX11.7'),
    ('Cmd_VACS1_Open', '%DB2.DBX12.0'), ('Cmd_VACS1_Close', '%DB2.DBX12.1'),
    ('Cmd_SB401H_Open', '%DB2.DBX12.2'), ('Cmd_SB401H_Close', '%DB2.DBX12.3'),
    ('Cmd_SB401L_Open', '%DB2.DBX12.4'), ('Cmd_SB401L_Close', '%DB2.DBX12.5'),
]
CMD_REAL = [('Cmd_Jet_ManFeed', '%DB2.DBD2'), ('Cmd_Jet_ManGrind', '%DB2.DBD6')]
# DB3 = State: EMOk 0.0 | 12 Real DBD2..46 | 11 bool 50.0~51.1
STATE_BOOL = [
    ('St_EMOk', '%DB3.DBX0.0'),
    ('St_VA101_Auto', '%DB3.DBX50.0'),
    ('St_MO201_Run', '%DB3.DBX50.1'), ('St_MO601_Run', '%DB3.DBX50.2'),
    ('St_MO601B_Run', '%DB3.DBX50.3'), ('St_MO101_Run', '%DB3.DBX50.4'),
    ('St_AlmFault', '%DB3.DBX50.5'), ('St_AlmValveFb', '%DB3.DBX50.6'),
    ('St_AlmHiPress', '%DB3.DBX50.7'), ('St_AlmEM', '%DB3.DBX51.0'),
    ('St_AlmAIBroken', '%DB3.DBX51.1'),
]
STATE_REAL = [
    ('St_P101', '%DB3.DBD2'), ('St_P102', '%DB3.DBD6'), ('St_P103', '%DB3.DBD10'),
    ('St_P104', '%DB3.DBD14'), ('St_T101', '%DB3.DBD18'), ('St_MO601FB', '%DB3.DBD30'),
    ('St_OutFeed', '%DB3.DBD34'), ('St_OutGrind', '%DB3.DBD38'),
    ('St_ErrFeed', '%DB3.DBD42'), ('St_ErrGrind', '%DB3.DBD46'),
]
# DB1 = Param (偶数对齐): SP DBD0/4 | Speed SP: MO201 DBD50, MO101 DBD54, MO601 DBD58
PARAM_REAL = [
    ('Prm_SP_Feed', '%DB1.DBD0'), ('Prm_SP_Grind', '%DB1.DBD4'),
    ('Prm_MO201_Speed', '%DB1.DBD50'), ('Prm_MO101_Speed', '%DB1.DBD54'), ('Prm_MO601_Speed', '%DB1.DBD58'),
]

m = MCP()
def c(n, a=None, t=300):
    try:
        return text_of(m.call(n, a or {}, timeout=t))
    except Exception as e:
        return 'ERR ' + str(e)
def cvia(n, a=None, t=300):
    return c('CallTool', {'name': n, 'argumentsJson': json.dumps(a or {})}, t)

ok, fail = 0, []
try:
    m.initialize()
    print(c('Connect', t=180)[:80])
    def ensure(tag, dtype, addr):
        global ok
        r = cvia('EnsureUnifiedHmiTag', {
            'hmiSoftwarePath': HMI, 'tagTableName': TABLE, 'tagName': tag,
            'hmiDataType': dtype, 'plcName': PLC, 'plcTag': '',
            'connectionName': CONN, 'address': addr, 'requireVerifiedBinding': False,
        }, t=180)
        good = 'ERR' not in r and '"success":true' in r.replace(' ', '')
        if good: ok += 1
        else: fail.append((tag, r[:200]))
    for tag, addr in CMD_BOOL: ensure(tag, 'Bool', addr)
    for tag, addr in CMD_REAL: ensure(tag, 'Float', addr)
    for tag, addr in STATE_BOOL: ensure(tag, 'Bool', addr)
    for tag, addr in STATE_REAL: ensure(tag, 'Float', addr)
    for tag, addr in PARAM_REAL: ensure(tag, 'Float', addr)
    print('重绑成功 %d / 失败 %d' % (ok, len(fail)))
    for t_, r_ in fail: print('FAIL', t_, '=>', r_)
    # 抽查读回 Address
    for tag in ['Cmd_MO201_Start', 'St_P102', 'Prm_SP_Feed', 'Cmd_Jet_ManFeed']:
        r = cvia('GetObjectProperty', {'objectKind': 'HmiTag', 'objectPath': '%s:%s:%s' % (HMI, TABLE, tag), 'propertyPath': 'Address'}, t=120)
        print('读回', tag, '=>', r[:200])
finally:
    m.close()
