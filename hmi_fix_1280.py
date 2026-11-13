# -*- coding: utf-8 -*-
"""按 1280x800 重建 4 个 WinCC Unified 画面：布局(全部在可视区) + IO域绑定 + 命令按钮 + 导航跳转。
顺序：EnsureUnifiedHmiScreen -> ApplyUnifiedHmiScreenDesignJson -> 绑定(ProcessValue/命令) -> 导航事件。
"""
import sys, os, json
sys.path.insert(0, r'D:\系统\桌面\workbuddy\TIA_Tools')
os.environ['TIA_MCP_ATTACH_TIMEOUT_MS'] = '120000'
from mcp_client import MCP, text_of

HMI = 'HMI_RT_1'
W, H = 1280, 800

def T(name, l, t, w, h, text, size=16, bold=False):
    d = {'name': name, 'type': 'Text', 'left': l, 'top': t, 'width': w, 'height': h, 'text': text}
    d['font'] = {'Size': size, 'Weight': 'Bold' if bold else 'Normal'}
    return d
def BTN(name, l, t, w, h, text):
    return {'name': name, 'type': 'Button', 'left': l, 'top': t, 'width': w, 'height': h, 'text': text}
def IOF(name, l, t, w, h):
    return {'name': name, 'type': 'IOField', 'left': l, 'top': t, 'width': w, 'height': h}

# ===================== 画面 1 主画面 =====================
main = [T('tTitle', 20, 12, 760, 44, '陕西天宇 J6 气流粉碎系统', 26, True)]
main += [T('tAlarm', 20, 72, 180, 28, '报警状态', 18, True)]
alarms = [('ioAlmEM','急停动作'),('ioAlmFault','设备故障'),('ioAlmHiP','压力超限'),
          ('ioAlmVfb','阀反馈异常'),('ioAlmAIB','变送器断线'),('ioEMOk','急停回路正常')]
for i,(io,lab) in enumerate(alarms):
    col=i%3; row=i//3; x=20+col*420; y=112+row*46
    main.append(T('t'+io, x, y, 150, 34, lab, 15))
    main.append(IOF(io, x+155, y, 70, 34))
main += [T('tPress', 20, 218, 220, 28, '压力总览 (Bar)', 18, True)]
press=[('ioP101','P101 主管'),('ioP102','P102 进料'),('ioP103','P103 粉碎'),('ioP104','P104 喷吹'),('ioT101','T101 温度')]
for i,(io,lab) in enumerate(press):
    x=20+i*250; y=258
    main.append(T('t'+io, x, y, 100, 34, lab, 15)); main.append(IOF(io, x+105, y, 95, 34))
main += [T('tMotor', 20, 318, 220, 28, '电机运行状态', 18, True)]
mot=[('ioM201run','MO201 给料'),('ioM601run','MO601 排风'),('ioM601Brun','MO601B 散热'),('ioM101run','MO101 喷吹')]
for i,(io,lab) in enumerate(mot):
    x=20+i*310; y=358
    main.append(T('t'+io, x, y, 150, 34, lab, 15)); main.append(IOF(io, x+155, y, 80, 34))
main += [BTN('btnGoMotors', 20, 700, 250, 70, '电机控制'),
         BTN('btnGoValves', 300, 700, 250, 70, '阀门控制'),
         BTN('btnGoJetMill', 580, 700, 250, 70, '气流粉碎')]

# ===================== 画面 2 电机控制 =====================
motors=[T('tTitle', 20, 12, 400, 40, '电机控制', 24, True)]
mrow=[('MO201 给料电机','MO201'),('MO601A 排风机','MO601'),('MO601B 散热风机','MO601B'),('MO101 喷吹风机','MO101')]
for i,(lab,pre) in enumerate(mrow):
    y=80+i*95
    motors.append(T('t'+pre, 20, y, 240, 40, lab, 16, True))
    motors.append(T('tSp'+pre, 280, y+5, 120, 30, '转速给定', 14))
    motors.append(IOF('ioSp'+pre, 410, y, 130, 40))
    motors.append(BTN('btnStart'+pre, 560, y, 140, 50, '启动'))
    motors.append(BTN('btnStop'+pre, 720, y, 140, 50, '停止'))
    if pre!='MO601B':
        motors.append(BTN('btnReset'+pre, 880, y, 140, 50, '复位'))
    motors.append(T('tRun'+pre, 1050, y+5, 80, 30, '运行', 14))
    motors.append(IOF('ioRun'+pre, 1140, y, 90, 40))
motors.append(BTN('btnBackMain', 20, 720, 260, 70, '返回主画面'))

# ===================== 画面 3 阀门控制 =====================
valves=[T('tTitle', 20, 12, 520, 40, '阀门控制 (脉冲命令：按下动作)', 22, True)]
vrow=[('VA101 主进气','VA101'),('VA102 喷吹进气','VA102'),('VA103 喷吹补气','VA103'),('VA104 中心环','VA104'),
      ('VA105 进粉拐角','VA105'),('VA106 旋风筒','VA106'),('VAPC1 上蝶阀','VAPC1'),('VAPC2 下蝶阀','VAPC2'),
      ('VACS1 高效入口','VACS1'),('SB401-H 高位抖袋','SB401H'),('SB401-L 低位抖袋','SB401L')]
for i,(lab,pre) in enumerate(vrow):
    col=0 if i<6 else 1; row=i if i<6 else i-6; x=20+col*640; y=80+row*62
    valves.append(T('t'+pre, x, y+8, 250, 40, lab, 15))
    valves.append(BTN('btn'+pre+'Open', x+265, y, 120, 50, '开阀'))
    valves.append(BTN('btn'+pre+'Close', x+395, y, 120, 50, '关阀'))
valves.append(BTN('btnBackMain', 20, 720, 260, 70, '返回主画面'))

# ===================== 画面 4 气流粉碎 =====================
jet=[T('tTitle', 20, 12, 700, 40, '气流粉碎 - 比例阀压力控制', 22, True)]
jet += [BTN('btnJetEnable', 20, 70, 110, 48, '使能'), BTN('btnJetDisable', 140, 70, 110, 48, '禁用'),
        BTN('btnJetAuto', 260, 70, 110, 48, '自动 PI'), BTN('btnJetManual', 380, 70, 110, 48, '手动输出')]
jet += [T('tJetEnSt', 510, 75, 60, 40, '使能', 14), IOF('ioJetEnSt', 575, 70, 70, 40)]
jet += [T('tJetAutoSt', 660, 75, 60, 40, '自动', 14), IOF('ioJetAutoSt', 725, 70, 70, 40)]
jet += [T('tLoopF', 20, 135, 360, 28, '进料压力回路 (Bar)', 18, True)]
jet += [T('tSpF', 20, 175, 90, 36, '设定SP', 14), IOF('ioSpF', 115, 172, 120, 44),
        T('tPvF', 250, 175, 90, 36, '实际PV', 14), IOF('ioPvF', 345, 172, 120, 44),
        T('tOutF', 480, 175, 90, 36, '阀输出', 14), IOF('ioOutF', 575, 172, 120, 44),
        T('tErrF', 710, 175, 90, 36, '偏差', 14), IOF('ioErrF', 805, 172, 120, 44)]
jet += [T('tLoopG', 20, 235, 360, 28, '粉碎压力回路 (Bar)', 18, True)]
jet += [T('tSpG', 20, 275, 90, 36, '设定SP', 14), IOF('ioSpG', 115, 272, 120, 44),
        T('tPvG', 250, 275, 90, 36, '实际PV', 14), IOF('ioPvG', 345, 272, 120, 44),
        T('tOutG', 480, 275, 90, 36, '阀输出', 14), IOF('ioOutG', 575, 272, 120, 44),
        T('tErrG', 710, 275, 90, 36, '偏差', 14), IOF('ioErrG', 805, 272, 120, 44)]
jet += [T('tMan', 20, 335, 360, 28, '手动输出 (手动模式有效)', 18, True)]
jet += [T('tManF', 20, 375, 130, 36, '进料阀开度', 14), IOF('ioManF', 155, 372, 120, 44),
        T('tManG', 300, 375, 130, 36, '粉碎阀开度', 14), IOF('ioManG', 435, 372, 120, 44)]
jet += [T('tWatch', 20, 435, 300, 28, '其他监视', 18, True)]
watch=[('ioP101w','P101 主管'),('ioP104w','P104 喷吹'),('ioT101w','T101 温度'),
       ('ioAlmHiPw','压力超限'),('ioAlmAIBw','变送器断线'),('ioVA101w','主进气阀')]
for i,(io,lab) in enumerate(watch):
    col=i%3; row=i//3; x=20+col*420; y=475+row*52
    jet.append(T('t'+io, x, y+4, 150, 34, lab, 14)); jet.append(IOF(io, x+155, y, 90, 34))
jet.append(BTN('btnBackMain', 20, 720, 260, 70, '返回主画面'))

SCREENS = [('Screen_J6_Main', main), ('Screen_J6_Motors', motors),
           ('Screen_J6_Valves', valves), ('Screen_J6_JetMill', jet)]

# IO域 ProcessValue 绑定 (screen, item, dataType, tag)
DYN = [
 ('Screen_J6_Main','ioAlmEM','Bool','St_AlmEM'),('Screen_J6_Main','ioAlmFault','Bool','St_AlmFault'),
 ('Screen_J6_Main','ioAlmHiP','Bool','St_AlmHiPress'),('Screen_J6_Main','ioAlmVfb','Bool','St_AlmValveFb'),
 ('Screen_J6_Main','ioAlmAIB','Bool','St_AlmAIBroken'),('Screen_J6_Main','ioEMOk','Bool','St_EMOk'),
 ('Screen_J6_Main','ioP101','Float','St_P101'),('Screen_J6_Main','ioP102','Float','St_P102'),
 ('Screen_J6_Main','ioP103','Float','St_P103'),('Screen_J6_Main','ioP104','Float','St_P104'),
 ('Screen_J6_Main','ioT101','Float','St_T101'),('Screen_J6_Main','ioM201run','Bool','St_MO201_Run'),
 ('Screen_J6_Main','ioM601run','Bool','St_MO601_Run'),('Screen_J6_Main','ioM601Brun','Bool','St_MO601B_Run'),
 ('Screen_J6_Main','ioM101run','Bool','St_MO101_Run'),
 ('Screen_J6_Motors','ioSpMO201','Float','Prm_MO201_Speed'),('Screen_J6_Motors','ioRunMO201','Bool','St_MO201_Run'),
 ('Screen_J6_Motors','ioSpMO601','Float','Prm_MO601_Speed'),('Screen_J6_Motors','ioRunMO601','Bool','St_MO601_Run'),
 ('Screen_J6_Motors','ioSpMO601B','Float','Prm_MO601_Speed'),('Screen_J6_Motors','ioRunMO601B','Bool','St_MO601B_Run'),
 ('Screen_J6_Motors','ioSpMO101','Float','Prm_MO101_Speed'),('Screen_J6_Motors','ioRunMO101','Bool','St_MO101_Run'),
 ('Screen_J6_JetMill','ioJetEnSt','Bool','Cmd_Jet_Enable'),('Screen_J6_JetMill','ioJetAutoSt','Bool','Cmd_Jet_Auto'),
 ('Screen_J6_JetMill','ioSpF','Float','Prm_SP_Feed'),('Screen_J6_JetMill','ioPvF','Float','St_P102'),
 ('Screen_J6_JetMill','ioOutF','Float','St_OutFeed'),('Screen_J6_JetMill','ioErrF','Float','St_ErrFeed'),
 ('Screen_J6_JetMill','ioSpG','Float','Prm_SP_Grind'),('Screen_J6_JetMill','ioPvG','Float','St_P103'),
 ('Screen_J6_JetMill','ioOutG','Float','St_OutGrind'),('Screen_J6_JetMill','ioErrG','Float','St_ErrGrind'),
 ('Screen_J6_JetMill','ioManF','Float','Cmd_Jet_ManFeed'),('Screen_J6_JetMill','ioManG','Float','Cmd_Jet_ManGrind'),
 ('Screen_J6_JetMill','ioP101w','Float','St_P101'),('Screen_J6_JetMill','ioP104w','Float','St_P104'),
 ('Screen_J6_JetMill','ioT101w','Float','St_T101'),('Screen_J6_JetMill','ioAlmHiPw','Bool','St_AlmHiPress'),
 ('Screen_J6_JetMill','ioAlmAIBw','Bool','St_AlmAIBroken'),('Screen_J6_JetMill','ioVA101w','Bool','St_VA101_Auto'),
]

# 命令按钮：瞬态(按下=1) -> BindUnifiedHmiButtonPressedTag
PRESSED = []
motpre=[('MO201','Cmd_MO201'),('MO601','Cmd_MO601'),('MO601B','Cmd_MO601B'),('MO101','Cmd_MO101')]
for pre,cmd in motpre:
    PRESSED.append(('Screen_J6_Motors','btnStart'+pre, cmd+'_Start'))
    PRESSED.append(('Screen_J6_Motors','btnStop'+pre, cmd+'_Stop'))
    if pre!='MO601B':
        PRESSED.append(('Screen_J6_Motors','btnReset'+pre, cmd+'_Reset'))
for pre,cmd in [('VA101','Cmd_VA101'),('VA102','Cmd_VA102'),('VA103','Cmd_VA103'),('VA104','Cmd_VA104'),
                ('VA105','Cmd_VA105'),('VA106','Cmd_VA106'),('VAPC1','Cmd_VAPC1'),('VAPC2','Cmd_VAPC2'),
                ('VACS1','Cmd_VACS1'),('SB401H','Cmd_SB401H'),('SB401L','Cmd_SB401L')]:
    PRESSED.append(('Screen_J6_Valves','btn'+pre+'Open', cmd+'_Open'))
    PRESSED.append(('Screen_J6_Valves','btn'+pre+'Close', cmd+'_Close'))

# 命令按钮：置位/复位(锁存) -> EnsureUnifiedHmiButtonAction
ACTIONS = [
 ('Screen_J6_JetMill','btnJetEnable','set-bit','Cmd_Jet_Enable'),
 ('Screen_J6_JetMill','btnJetDisable','reset-bit','Cmd_Jet_Enable'),
 ('Screen_J6_JetMill','btnJetAuto','set-bit','Cmd_Jet_Auto'),
 ('Screen_J6_JetMill','btnJetManual','reset-bit','Cmd_Jet_Auto'),
]

# 导航：Tapped -> ActivateScreen
NAV = [
 ('Screen_J6_Main','btnGoMotors','Screen_J6_Motors'),
 ('Screen_J6_Main','btnGoValves','Screen_J6_Valves'),
 ('Screen_J6_Main','btnGoJetMill','Screen_J6_JetMill'),
 ('Screen_J6_Motors','btnBackMain','Screen_J6_Main'),
 ('Screen_J6_Valves','btnBackMain','Screen_J6_Main'),
 ('Screen_J6_JetMill','btnBackMain','Screen_J6_Main'),
]

m = MCP()
def c(n, a=None, t=600):
    try: return text_of(m.call(n, a or {}, timeout=t))
    except Exception as e: return 'ERR ' + str(e)
def cvia(n, a=None, t=600):
    return c('CallTool', {'name': n, 'argumentsJson': json.dumps(a or {}, ensure_ascii=False)}, t)

fails=[]
def rep(label, r):
    if 'ERR' in r or '"success":false' in r.replace(' ',''):
        fails.append((label, r[:240]))

try:
    m.initialize()
    print('Connect:', c('Connect', t=240)[:120])

    # 1) 重建画面布局
    for name, items in SCREENS:
        r = cvia('EnsureUnifiedHmiScreen', {'hmiSoftwarePath': HMI, 'screenName': name, 'width': W, 'height': H}, t=240)
        rep('EnsureScreen '+name, r)
        design = {'screenName': name, 'width': W, 'height': H, 'items': items}
        r2 = cvia('ApplyUnifiedHmiScreenDesignJson', {
            'hmiSoftwarePath': HMI, 'screenName': name,
            'designJson': json.dumps(design, ensure_ascii=False), 'strict': True}, t=600)
        rep('Design '+name, r2)
        print('画面 %s 布局完成' % name)

    # 2) IO域 ProcessValue 绑定（设计之后）
    for scr, item, dt, tag in DYN:
        r = cvia('BindUnifiedHmiTagDynamization', {
            'hmiSoftwarePath': HMI, 'screenName': scr, 'itemName': item,
            'propertyName': 'ProcessValue', 'tagName': tag, 'dataType': dt}, t=180)
        rep('DYN %s/%s->%s' % (scr, item, tag), r)

    # 3) 命令按钮 - 瞬态
    for scr, btn, tag in PRESSED:
        r = cvia('BindUnifiedHmiButtonPressedTag', {
            'hmiSoftwarePath': HMI, 'screenName': scr, 'buttonName': btn, 'tagName': tag}, t=180)
        rep('PRESS %s/%s->%s' % (scr, btn, tag), r)
    # 3b) 命令按钮 - 置/复位
    for scr, btn, kind, tag in ACTIONS:
        r = cvia('EnsureUnifiedHmiButtonAction', {
            'hmiSoftwarePath': HMI, 'screenName': scr, 'buttonName': btn,
            'eventType': 'Tapped', 'actionKind': kind, 'targetTag': tag}, t=240)
        rep('ACT %s/%s %s->%s' % (scr, btn, kind, tag), r)

    # 4) 导航按钮 Tapped -> ActivateScreen
    for scr, btn, target in NAV:
        cvia('EnsureUnifiedHmiButtonEventHandler', {
            'hmiSoftwarePath': HMI, 'screenName': scr, 'buttonName': btn, 'eventType': 'Tapped'}, t=180)
        r = cvia('SetUnifiedHmiButtonEventScriptCode', {
            'hmiSoftwarePath': HMI, 'screenName': scr, 'buttonName': btn, 'eventType': 'Tapped',
            'scriptCode': 'ActivateScreen("%s");' % target, 'globalDefinitionAreaScriptCode': '', 'async': False, 'syntaxCheck': False}, t=180)
        rep('NAV %s/%s->%s' % (scr, btn, target), r)

    # 5) 编译 HMI
    r = cvia('CompileAndDiagnoseHmi', {'hmiSoftwarePath': HMI}, t=600)
    rep('CompileHMI', r)
    print('编译结果:', r[:300])

    print('\n===== 失败 %d 项 =====' % len(fails))
    for l, r in fails: print('FAIL', l, '=>', r)
finally:
    m.close()
