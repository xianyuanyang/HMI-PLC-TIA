# -*- coding: utf-8 -*-
"""HMI 第二步：创建 4 个画面并应用布局。"""
import sys, os, json
sys.path.insert(0, r'D:\系统\桌面\workbuddy\TIA_Tools')
os.environ['TIA_MCP_ATTACH_TIMEOUT_MS'] = '90000'
from mcp_client import MCP, text_of

HMI = 'HMI_RT_1'
W, H = 1920, 1080

def T(name, l, t, w, h, text, size=20, bold=False):
    d = {'name': name, 'type': 'Text', 'left': l, 'top': t, 'width': w, 'height': h, 'text': text}
    if size or bold: d['font'] = {'Size': size or 20, 'Weight': 'Bold' if bold else 'Normal'}
    return d

def BTN(name, l, t, w, h, text):
    return {'name': name, 'type': 'Button', 'left': l, 'top': t, 'width': w, 'height': h, 'text': text}

def IOF(name, l, t, w, h):
    return {'name': name, 'type': 'IOField', 'left': l, 'top': t, 'width': w, 'height': h}

def RECT(name, l, t, w, h):
    return {'name': name, 'type': 'Rectangle', 'left': l, 'top': t, 'width': w, 'height': h}

# ============ 画面 1: 主画面 ============
main_items = [
    T('tTitle', 40, 20, 900, 70, '陕西天宇 J6 气流粉碎系统', 32, True),
    # 报警区
    T('tAlarm', 40, 120, 300, 45, '报警状态', 22, True),
    T('tAlmEM', 40, 180, 220, 40, '急停动作'), IOF('ioAlmEM', 270, 180, 100, 40),
    T('tAlmFault', 400, 180, 220, 40, '设备故障'), IOF('ioAlmFault', 630, 180, 100, 40),
    T('tAlmHiP', 760, 180, 220, 40, '压力超限'), IOF('ioAlmHiP', 990, 180, 100, 40),
    T('tAlmVfb', 40, 240, 220, 40, '阀反馈异常'), IOF('ioAlmVfb', 270, 240, 100, 40),
    T('tAlmAIB', 400, 240, 220, 40, '变送器断线'), IOF('ioAlmAIB', 630, 240, 100, 40),
    T('tEMOk', 760, 240, 220, 40, '急停回路正常'), IOF('ioEMOk', 990, 240, 100, 40),
    # 压力总览
    T('tPress', 40, 330, 300, 45, '压力总览 (Bar)', 22, True),
    T('tP101', 40, 390, 200, 40, 'P101 主管'), IOF('ioP101', 250, 390, 140, 40),
    T('tP102', 420, 390, 200, 40, 'P102 进料'), IOF('ioP102', 630, 390, 140, 40),
    T('tP103', 800, 390, 200, 40, 'P103 粉碎'), IOF('ioP103', 1010, 390, 140, 40),
    T('tP104', 40, 450, 200, 40, 'P104 喷吹'), IOF('ioP104', 250, 450, 140, 40),
    T('tT101', 420, 450, 200, 40, 'T101 温度 C'), IOF('ioT101', 630, 450, 140, 40),
    # 电机状态
    T('tMotor', 40, 540, 300, 45, '电机运行状态', 22, True),
    T('tM201', 40, 600, 200, 40, 'MO201 给料'), IOF('ioM201run', 250, 600, 100, 40),
    T('tM601', 420, 600, 200, 40, 'MO601 排风'), IOF('ioM601run', 630, 600, 100, 40),
    T('tM601B', 800, 600, 220, 40, 'MO601B 散热'), IOF('ioM601Brun', 1030, 600, 100, 40),
    T('tM101', 40, 660, 200, 40, 'MO101 喷吹'), IOF('ioM101run', 250, 660, 100, 40),
    # 导航
    BTN('btnGoMotors', 40, 950, 260, 70, '电机控制'),
    BTN('btnGoValves', 340, 950, 260, 70, '阀门控制'),
    BTN('btnGoJetMill', 640, 950, 260, 70, '气流粉碎'),
]

# ============ 画面 2: 电机控制 ============
def motor_row(y, label, pre, has_reset=True):
    items = [T('t' + pre, 40, y, 240, 45, label, 20, True)]
    items.append(T('tSp' + pre, 300, y, 140, 40, '转速给定'))
    items.append(IOF('ioSp' + pre, 450, y, 140, 40))
    items.append(BTN('btnStart' + pre, 650, y, 150, 50, '启动'))
    items.append(BTN('btnStop' + pre, 820, y, 150, 50, '停止'))
    if has_reset:
        items.append(BTN('btnReset' + pre, 990, y, 150, 50, '复位'))
    items.append(T('tRun' + pre, 1200, y, 120, 40, '运行'))
    items.append(IOF('ioRun' + pre, 1330, y, 100, 40))
    return items

motors_items = [T('tTitle', 40, 20, 700, 70, '电机控制', 32, True)]
motors_items += motor_row(160, 'MO201 给料电机', 'MO201')
motors_items += motor_row(330, 'MO601A 排风机', 'MO601')
motors_items += motor_row(500, 'MO601B 散热风机', 'MO601B', has_reset=False)
motors_items += motor_row(670, 'MO101 喷吹风机', 'MO101')
motors_items += [T('tNote', 40, 800, 1400, 40, '命令为瞬态：按下即动作，松开自动清零；转速给定 0~量程上限'),
                 BTN('btnBackMain', 40, 950, 260, 70, '返回主画面')]

# ============ 画面 3: 阀门控制 ============
valves = [('VA101 主进气', 'VA101'), ('VA102 喷吹进气', 'VA102'), ('VA103 喷吹补气', 'VA103'),
          ('VA104 中心环', 'VA104'), ('VA105 进粉拐角', 'VA105'), ('VA106 旋风筒', 'VA106'),
          ('VAPC1 上蝶阀', 'VAPC1'), ('VAPC2 下蝶阀', 'VAPC2'), ('VACS1 高效入口', 'VACS1'),
          ('SB401-H 高位抖袋', 'SB401H'), ('SB401-L 低位抖袋', 'SB401L')]
valves_items = [T('tTitle', 40, 20, 700, 70, '阀门控制 (脉冲命令：按下动作)', 32, True)]
for i, (label, pre) in enumerate(valves):
    col = 0 if i < 6 else 1
    row = i if i < 6 else i - 6
    x = 40 + col * 950
    y = 140 + row * 120
    valves_items.append(T('t' + pre, x, y + 10, 260, 40, label))
    valves_items.append(BTN('btn' + pre + 'Open', x + 300, y, 130, 55, '开阀'))
    valves_items.append(BTN('btn' + pre + 'Close', x + 450, y, 130, 55, '关阀'))
valves_items.append(BTN('btnBackMain', 40, 950, 260, 70, '返回主画面'))

# ============ 画面 4: 气流粉碎 PID ============
jet_items = [
    T('tTitle', 40, 20, 900, 70, '气流粉碎 - 比例阀压力控制', 32, True),
    # 使能与模式
    T('tMode', 40, 120, 300, 40, '使能与模式', 22, True),
    BTN('btnJetEnable', 40, 170, 150, 55, '使能'),
    BTN('btnJetDisable', 200, 170, 150, 55, '禁用'),
    BTN('btnJetAuto', 360, 170, 150, 55, '自动 PI'),
    BTN('btnJetManual', 520, 170, 150, 55, '手动输出'),
    T('tJetEnSt', 700, 175, 100, 40, '使能'), IOF('ioJetEnSt', 810, 170, 80, 40),
    T('tJetAutoSt', 900, 175, 100, 40, '自动'), IOF('ioJetAutoSt', 1010, 170, 80, 40),
    # 进料回路
    T('tLoopF', 40, 260, 400, 45, '进料压力回路 (Bar)', 22, True),
    T('tSpF', 40, 320, 160, 40, '设定 SP'), IOF('ioSpF', 210, 320, 140, 45),
    T('tPvF', 420, 320, 160, 40, '实际 PV'), IOF('ioPvF', 590, 320, 140, 45),
    T('tOutF', 800, 320, 160, 40, '阀输出'), IOF('ioOutF', 970, 320, 140, 45),
    T('tErrF', 1180, 320, 160, 40, '偏差'), IOF('ioErrF', 1350, 320, 140, 45),
    # 粉碎回路
    T('tLoopG', 40, 400, 400, 45, '粉碎压力回路 (Bar)', 22, True),
    T('tSpG', 40, 460, 160, 40, '设定 SP'), IOF('ioSpG', 210, 460, 140, 45),
    T('tPvG', 420, 460, 160, 40, '实际 PV'), IOF('ioPvG', 590, 460, 140, 45),
    T('tOutG', 800, 460, 160, 40, '阀输出'), IOF('ioOutG', 970, 460, 140, 45),
    T('tErrG', 1180, 460, 160, 40, '偏差'), IOF('ioErrG', 1350, 460, 140, 45),
    # 手动输出
    T('tMan', 40, 540, 400, 45, '手动输出 (手动模式下有效)', 22, True),
    T('tManF', 40, 600, 200, 40, '进料阀开度 Bar'), IOF('ioManF', 260, 600, 140, 45),
    T('tManG', 420, 600, 200, 40, '粉碎阀开度 Bar'), IOF('ioManG', 640, 600, 140, 45),
    # 其他监视
    T('tWatch', 40, 680, 400, 45, '其他监视', 22, True),
    T('tP101w', 40, 740, 160, 40, 'P101 主管'), IOF('ioP101w', 210, 740, 140, 40),
    T('tP104w', 420, 740, 160, 40, 'P104 喷吹'), IOF('ioP104w', 590, 740, 140, 40),
    T('tT101w', 800, 740, 160, 40, 'T101 温度'), IOF('ioT101w', 970, 740, 140, 40),
    T('tAlmHiPw', 40, 800, 220, 40, '压力超限报警'), IOF('ioAlmHiPw', 270, 800, 100, 40),
    T('tAlmAIBw', 420, 800, 220, 40, '变送器断线'), IOF('ioAlmAIBw', 660, 800, 100, 40),
    T('tVA101w', 800, 800, 220, 40, '主进气阀状态'), IOF('ioVA101w', 1030, 800, 100, 40),
    BTN('btnBackMain', 40, 950, 260, 70, '返回主画面'),
]

m = MCP()
def c(n, a=None, t=400):
    try:
        return text_of(m.call(n, a or {}, timeout=t))
    except Exception as e:
        return 'ERR ' + str(e)
def cvia(n, a=None, t=400):
    return c('CallTool', {'name': n, 'argumentsJson': json.dumps(a or {})}, t)

try:
    m.initialize()
    print(c('Connect', t=180)[:100])
    screens = [
        ('Screen_J6_Main', main_items),
        ('Screen_J6_Motors', motors_items),
        ('Screen_J6_Valves', valves_items),
        ('Screen_J6_JetMill', jet_items),
    ]
    for name, items in screens:
        r = cvia('EnsureUnifiedHmiScreen', {'hmiSoftwarePath': HMI, 'screenName': name, 'width': W, 'height': H}, t=240)
        print('EnsureScreen', name, '=>', ('OK' if 'ERR' not in r and 'error' not in r.lower()[:80] else r[:200]))
        design = {'screenName': name, 'width': W, 'height': H, 'items': items}
        r2 = cvia('ApplyUnifiedHmiScreenDesignJson', {
            'hmiSoftwarePath': HMI, 'screenName': name,
            'designJson': json.dumps(design, ensure_ascii=False), 'strict': True}, t=600)
        good = 'ERR' not in r2 and '"success":true' in r2.replace(' ', '').replace('\n', '')
        print('ApplyDesign', name, '=>', 'OK' if good else r2[:400])
        print()
finally:
    m.close()
