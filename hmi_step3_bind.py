# -*- coding: utf-8 -*-
"""HMI 第三步：变量动态化绑定 + 按钮动作绑定。"""
import sys, os, json
sys.path.insert(0, r'D:\系统\桌面\workbuddy\TIA_Tools')
os.environ['TIA_MCP_ATTACH_TIMEOUT_MS'] = '90000'
from mcp_client import MCP, text_of

HMI = 'HMI_RT_1'

# (screen, itemName, dataType, tagName)
DYN = [
    # --- 主画面 ---
    ('Screen_J6_Main', 'ioAlmEM', 'Bool', 'St_AlmEM'),
    ('Screen_J6_Main', 'ioAlmFault', 'Bool', 'St_AlmFault'),
    ('Screen_J6_Main', 'ioAlmHiP', 'Bool', 'St_AlmHiPress'),
    ('Screen_J6_Main', 'ioAlmVfb', 'Bool', 'St_AlmValveFb'),
    ('Screen_J6_Main', 'ioAlmAIB', 'Bool', 'St_AlmAIBroken'),
    ('Screen_J6_Main', 'ioEMOk', 'Bool', 'St_EMOk'),
    ('Screen_J6_Main', 'ioP101', 'Float', 'St_P101'),
    ('Screen_J6_Main', 'ioP102', 'Float', 'St_P102'),
    ('Screen_J6_Main', 'ioP103', 'Float', 'St_P103'),
    ('Screen_J6_Main', 'ioP104', 'Float', 'St_P104'),
    ('Screen_J6_Main', 'ioT101', 'Float', 'St_T101'),
    ('Screen_J6_Main', 'ioM201run', 'Bool', 'St_MO201_Run'),
    ('Screen_J6_Main', 'ioM601run', 'Bool', 'St_MO601_Run'),
    ('Screen_J6_Main', 'ioM601Brun', 'Bool', 'St_MO601B_Run'),
    ('Screen_J6_Main', 'ioM101run', 'Bool', 'St_MO101_Run'),
    # --- 电机画面 ---
    ('Screen_J6_Motors', 'ioSpMO201', 'Float', 'Prm_MO201_Speed'),
    ('Screen_J6_Motors', 'ioRunMO201', 'Bool', 'St_MO201_Run'),
    ('Screen_J6_Motors', 'ioSpMO601', 'Float', 'Prm_MO601_Speed'),
    ('Screen_J6_Motors', 'ioRunMO601', 'Bool', 'St_MO601_Run'),
    ('Screen_J6_Motors', 'ioSpMO601B', 'Float', 'Prm_MO601_Speed'),
    ('Screen_J6_Motors', 'ioRunMO601B', 'Bool', 'St_MO601B_Run'),
    ('Screen_J6_Motors', 'ioSpMO101', 'Float', 'Prm_MO101_Speed'),
    ('Screen_J6_Motors', 'ioRunMO101', 'Bool', 'St_MO101_Run'),
    # --- 气流粉碎画面 ---
    ('Screen_J6_JetMill', 'ioJetEnSt', 'Bool', 'Cmd_Jet_Enable'),
    ('Screen_J6_JetMill', 'ioJetAutoSt', 'Bool', 'Cmd_Jet_Auto'),
    ('Screen_J6_JetMill', 'ioSpF', 'Float', 'Prm_SP_Feed'),
    ('Screen_J6_JetMill', 'ioPvF', 'Float', 'St_P102'),
    ('Screen_J6_JetMill', 'ioOutF', 'Float', 'St_OutFeed'),
    ('Screen_J6_JetMill', 'ioErrF', 'Float', 'St_ErrFeed'),
    ('Screen_J6_JetMill', 'ioSpG', 'Float', 'Prm_SP_Grind'),
    ('Screen_J6_JetMill', 'ioPvG', 'Float', 'St_P103'),
    ('Screen_J6_JetMill', 'ioOutG', 'Float', 'St_OutGrind'),
    ('Screen_J6_JetMill', 'ioErrG', 'Float', 'St_ErrGrind'),
    ('Screen_J6_JetMill', 'ioManF', 'Float', 'Cmd_Jet_ManFeed'),
    ('Screen_J6_JetMill', 'ioManG', 'Float', 'Cmd_Jet_ManGrind'),
    ('Screen_J6_JetMill', 'ioP101w', 'Float', 'St_P101'),
    ('Screen_J6_JetMill', 'ioP104w', 'Float', 'St_P104'),
    ('Screen_J6_JetMill', 'ioT101w', 'Float', 'St_T101'),
    ('Screen_J6_JetMill', 'ioAlmHiPw', 'Bool', 'St_AlmHiPress'),
    ('Screen_J6_JetMill', 'ioAlmAIBw', 'Bool', 'St_AlmAIBroken'),
    ('Screen_J6_JetMill', 'ioVA101w', 'Bool', 'St_VA101_Auto'),
]

# 瞬态按钮 (screen, buttonName, tagName)
PRESSED = [
    ('Screen_J6_Motors', 'btnStartMO201', 'Cmd_MO201_Start'), ('Screen_J6_Motors', 'btnStopMO201', 'Cmd_MO201_Stop'),
    ('Screen_J6_Motors', 'btnResetMO201', 'Cmd_MO201_Reset'),
    ('Screen_J6_Motors', 'btnStartMO601', 'Cmd_MO601_Start'), ('Screen_J6_Motors', 'btnStopMO601', 'Cmd_MO601_Stop'),
    ('Screen_J6_Motors', 'btnResetMO601', 'Cmd_MO601_Reset'),
    ('Screen_J6_Motors', 'btnStartMO601B', 'Cmd_MO601B_Start'), ('Screen_J6_Motors', 'btnStopMO601B', 'Cmd_MO601B_Stop'),
    ('Screen_J6_Motors', 'btnStartMO101', 'Cmd_MO101_Start'), ('Screen_J6_Motors', 'btnStopMO101', 'Cmd_MO101_Stop'),
    ('Screen_J6_Motors', 'btnResetMO101', 'Cmd_MO101_Reset'),
]
for v in ['VA101', 'VA102', 'VA103', 'VA104', 'VA105', 'VA106', 'VAPC1', 'VAPC2', 'VACS1', 'SB401H', 'SB401L']:
    PRESSED.append(('Screen_J6_Valves', 'btn' + v + 'Open', 'Cmd_' + v + '_Open'))
    PRESSED.append(('Screen_J6_Valves', 'btn' + v + 'Close', 'Cmd_' + v + '_Close'))

# 置位/复位按钮 (screen, buttonName, actionKind, tagName)
ACTIONS = [
    ('Screen_J6_JetMill', 'btnJetEnable', 'set-bit', 'Cmd_Jet_Enable'),
    ('Screen_J6_JetMill', 'btnJetDisable', 'reset-bit', 'Cmd_Jet_Enable'),
    ('Screen_J6_JetMill', 'btnJetAuto', 'set-bit', 'Cmd_Jet_Auto'),
    ('Screen_J6_JetMill', 'btnJetManual', 'reset-bit', 'Cmd_Jet_Auto'),
]

# 画面导航
NAV = [
    ('Screen_J6_Main', 'btnGoMotors', 'Screen_J6_Motors'),
    ('Screen_J6_Main', 'btnGoValves', 'Screen_J6_Valves'),
    ('Screen_J6_Main', 'btnGoJetMill', 'Screen_J6_JetMill'),
    ('Screen_J6_Motors', 'btnBackMain', 'Screen_J6_Main'),
    ('Screen_J6_Valves', 'btnBackMain', 'Screen_J6_Main'),
    ('Screen_J6_JetMill', 'btnBackMain', 'Screen_J6_Main'),
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
def report(label, r):
    global ok
    if 'ERR' in r or '"success":false' in r:
        fail.append((label, r[:200]))
    else:
        ok += 1

try:
    m.initialize()
    print(c('Connect', t=180)[:80])
    # 1) IOField 动态化
    for scr, item, dt, tag in DYN:
        r = cvia('BindUnifiedHmiTagDynamization', {
            'hmiSoftwarePath': HMI, 'screenName': scr, 'itemName': item,
            'propertyName': 'ProcessValue', 'tagName': tag, 'dataType': dt}, t=180)
        report('DYN %s/%s->%s' % (scr, item, tag), r)
    # 2) 瞬态命令按钮
    for scr, btn, tag in PRESSED:
        r = cvia('BindUnifiedHmiButtonPressedTag', {
            'hmiSoftwarePath': HMI, 'screenName': scr, 'buttonName': btn, 'tagName': tag}, t=180)
        report('PRESS %s/%s->%s' % (scr, btn, tag), r)
    # 3) 置位/复位动作
    for scr, btn, kind, tag in ACTIONS:
        r = cvia('EnsureUnifiedHmiButtonAction', {
            'hmiSoftwarePath': HMI, 'screenName': scr, 'buttonName': btn,
            'eventType': 'Tapped', 'actionKind': kind, 'targetTag': tag}, t=240)
        report('ACT %s/%s %s->%s' % (scr, btn, kind, tag), r)
    # 4) 画面导航
    for scr, btn, target in NAV:
        r = cvia('EnsureUnifiedHmiButtonAction', {
            'hmiSoftwarePath': HMI, 'screenName': scr, 'buttonName': btn,
            'eventType': 'Tapped', 'actionKind': 'change-screen', 'targetScreen': target}, t=240)
        report('NAV %s/%s->%s' % (scr, btn, target), r)
    print('成功 %d / 失败 %d' % (ok, len(fail)))
    for l, r in fail: print('FAIL', l, '=>', r)
finally:
    m.close()
