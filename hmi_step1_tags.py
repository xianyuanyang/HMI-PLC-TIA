# -*- coding: utf-8 -*-
"""HMI 第一步：连接 + 变量表 + 全部 HMI 变量（符号绑定 PLC DB 成员）。"""
import sys, os, json
sys.path.insert(0, r'D:\系统\桌面\workbuddy\TIA_Tools')
os.environ['TIA_MCP_ATTACH_TIMEOUT_MS'] = '90000'
from mcp_client import MCP, text_of

HMI = 'HMI_RT_1'
PLC = 'G2_PLC_1'
CONN = 'HMI_Connection_1'
TABLE = 'J6_Tags'

# (tagName, dataType, plcTag)
CMD_BOOL = [
    ('Cmd_MO201_Start', 'DB_J6_Cmd.MO201_Start'), ('Cmd_MO201_Stop', 'DB_J6_Cmd.MO201_Stop'),
    ('Cmd_MO201_Reset', 'DB_J6_Cmd.MO201_Reset'),
    ('Cmd_MO601_Start', 'DB_J6_Cmd.MO601_Start'), ('Cmd_MO601_Stop', 'DB_J6_Cmd.MO601_Stop'),
    ('Cmd_MO601_Reset', 'DB_J6_Cmd.MO601_Reset'),
    ('Cmd_MO601B_Start', 'DB_J6_Cmd.MO601B_Start'), ('Cmd_MO601B_Stop', 'DB_J6_Cmd.MO601B_Stop'),
    ('Cmd_MO101_Start', 'DB_J6_Cmd.MO101_Start'), ('Cmd_MO101_Stop', 'DB_J6_Cmd.MO101_Stop'),
    ('Cmd_MO101_Reset', 'DB_J6_Cmd.MO101_Reset'),
    ('Cmd_Jet_Enable', 'DB_J6_Cmd.Jet_Enable'), ('Cmd_Jet_Auto', 'DB_J6_Cmd.Jet_Auto'),
    ('Cmd_VA101_Open', 'DB_J6_Cmd.VA101_Open'), ('Cmd_VA101_Close', 'DB_J6_Cmd.VA101_Close'),
    ('Cmd_VA102_Open', 'DB_J6_Cmd.VA102_Open'), ('Cmd_VA102_Close', 'DB_J6_Cmd.VA102_Close'),
    ('Cmd_VA103_Open', 'DB_J6_Cmd.VA103_Open'), ('Cmd_VA103_Close', 'DB_J6_Cmd.VA103_Close'),
    ('Cmd_VA104_Open', 'DB_J6_Cmd.VA104_Open'), ('Cmd_VA104_Close', 'DB_J6_Cmd.VA104_Close'),
    ('Cmd_VA105_Open', 'DB_J6_Cmd.VA105_Open'), ('Cmd_VA105_Close', 'DB_J6_Cmd.VA105_Close'),
    ('Cmd_VA106_Open', 'DB_J6_Cmd.VA106_Open'), ('Cmd_VA106_Close', 'DB_J6_Cmd.VA106_Close'),
    ('Cmd_VAPC1_Open', 'DB_J6_Cmd.VAPC1_Open'), ('Cmd_VAPC1_Close', 'DB_J6_Cmd.VAPC1_Close'),
    ('Cmd_VAPC2_Open', 'DB_J6_Cmd.VAPC2_Open'), ('Cmd_VAPC2_Close', 'DB_J6_Cmd.VAPC2_Close'),
    ('Cmd_VACS1_Open', 'DB_J6_Cmd.VACS1_Open'), ('Cmd_VACS1_Close', 'DB_J6_Cmd.VACS1_Close'),
    ('Cmd_SB401H_Open', 'DB_J6_Cmd.SB401H_Open'), ('Cmd_SB401H_Close', 'DB_J6_Cmd.SB401H_Close'),
    ('Cmd_SB401L_Open', 'DB_J6_Cmd.SB401L_Open'), ('Cmd_SB401L_Close', 'DB_J6_Cmd.SB401L_Close'),
]
CMD_REAL = [
    ('Cmd_Jet_ManFeed', 'DB_J6_Cmd.Jet_ManFeed'),
    ('Cmd_Jet_ManGrind', 'DB_J6_Cmd.Jet_ManGrind'),
]
STATE_BOOL = [
    ('St_EMOk', 'DB_J6_State.EMOk'),
    ('St_MO201_Run', 'DB_J6_State.MO201_Running'), ('St_MO601_Run', 'DB_J6_State.MO601_Running'),
    ('St_MO601B_Run', 'DB_J6_State.MO601B_Running'), ('St_MO101_Run', 'DB_J6_State.MO101_Running'),
    ('St_VA101_Auto', 'DB_J6_State.VA101_Auto'),
    ('St_AlmFault', 'DB_J6_State.Alm_Fault'), ('St_AlmValveFb', 'DB_J6_State.Alm_ValveFb'),
    ('St_AlmHiPress', 'DB_J6_State.Alm_HiPress'), ('St_AlmEM', 'DB_J6_State.Alm_EM'),
    ('St_AlmAIBroken', 'DB_J6_State.Alm_AI_Broken'),
]
STATE_REAL = [
    ('St_P101', 'DB_J6_State.P101_Bar'), ('St_P102', 'DB_J6_State.P102_Bar'),
    ('St_P103', 'DB_J6_State.P103_Bar'), ('St_P104', 'DB_J6_State.P104_Bar'),
    ('St_T101', 'DB_J6_State.T101_C'), ('St_MO601FB', 'DB_J6_State.MO601_FB_Hz'),
    ('St_OutFeed', 'DB_J6_State.Out_Feed_Bar'), ('St_OutGrind', 'DB_J6_State.Out_Grind_Bar'),
    ('St_ErrFeed', 'DB_J6_State.Err_Feed'), ('St_ErrGrind', 'DB_J6_State.Err_Grind'),
]
PARAM_REAL = [
    ('Prm_SP_Feed', 'DB_J6_Param.SP_Feed_Bar'), ('Prm_SP_Grind', 'DB_J6_Param.SP_Grind_Bar'),
    ('Prm_MO201_Speed', 'DB_J6_Param.MO201_SpeedSp'), ('Prm_MO601_Speed', 'DB_J6_Param.MO601_SpeedSp'),
    ('Prm_MO101_Speed', 'DB_J6_Param.MO101_SpeedSp'),
]

m = MCP()
def c(n, a=None, t=300):
    try:
        return text_of(m.call(n, a or {}, timeout=t))
    except Exception as e:
        return 'ERR ' + str(e)
def cvia(n, a=None, t=300):
    return c('CallTool', {'name': n, 'argumentsJson': json.dumps(a or {})}, t)

ok, fail = [], []
try:
    m.initialize()
    print('===== Connect ====='); print(c('Connect', t=180)[:150])
    print('===== EnsureUnifiedHmiConnection =====')
    r = cvia('EnsureUnifiedHmiConnection', {'hmiSoftwarePath': HMI, 'connectionName': CONN, 'plcName': PLC}, t=300)
    print(r[:600]); print()
    print('===== EnsureUnifiedHmiTagTable =====')
    print(cvia('EnsureUnifiedHmiTagTable', {'hmiSoftwarePath': HMI, 'tagTableName': TABLE}, t=180)[:300]); print()

    def ensure(tag, dtype, plc_tag):
        r = cvia('EnsureUnifiedHmiTag', {
            'hmiSoftwarePath': HMI, 'tagTableName': TABLE, 'tagName': tag,
            'hmiDataType': dtype, 'plcName': PLC, 'plcTag': plc_tag,
            'connectionName': CONN, 'requireVerifiedBinding': False,
        }, t=180)
        good = ('ERR' not in r) and ('success":true' in r.lower() or 'ok' in r.lower() or 'verified' in r.lower() or 'Symbolic' in r)
        (ok if good else fail).append((tag, r[:220]))

    for tag, pt in CMD_BOOL: ensure(tag, 'Bool', pt)
    for tag, pt in CMD_REAL: ensure(tag, 'Float', pt)
    for tag, pt in STATE_BOOL: ensure(tag, 'Bool', pt)
    for tag, pt in STATE_REAL: ensure(tag, 'Float', pt)
    for tag, pt in PARAM_REAL: ensure(tag, 'Float', pt)

    print('成功 %d / 失败 %d' % (len(ok), len(fail)))
    for t_, r_ in fail: print('FAIL', t_, '=>', r_)
finally:
    m.close()
