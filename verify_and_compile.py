# -*- coding: utf-8 -*-
"""验证 4 画面绑定/导航回读 + 正确编译 HMI。"""
import sys, os, json
sys.path.insert(0, r'D:\系统\桌面\workbuddy\TIA_Tools')
os.environ['TIA_MCP_ATTACH_TIMEOUT_MS'] = '120000'
from mcp_client import MCP, text_of
HMI='HMI_RT_1'
m=MCP()
def c(n,a=None,t=600):
    try: return text_of(m.call(n,a or {},timeout=t))
    except Exception as e: return 'ERR '+str(e)
def cvia(n,a=None,t=600): return c('CallTool',{'name':n,'argumentsJson':json.dumps(a or {},ensure_ascii=False)},t)
def gp(scr,item,prop):
    return cvia('GetObjectProperty',{'objectKind':'HmiScreenItem','objectPath':'%s:%s:%s'%(HMI,scr,item),'propertyPath':prop},180)
def has_dyn(scr,item):
    r=gp(scr,item,'Dynamizations')
    return 'TagDynamization' in r and '"value":[]' not in r
def has_evt(scr,item):
    r=gp(scr,item,'EventHandlers')
    return 'HmiButtonEventHandler' in r and '"value":[]' not in r
try:
    m.initialize(); print('Connect:',c('Connect',t=240)[:80])
    checks=[('Screen_J6_Main','ioP101','St_P101'),('Screen_J6_Main','ioEMOk','St_EMOk'),
            ('Screen_J6_Motors','ioSpMO201','Prm_MO201_Speed'),('Screen_J6_Motors','ioRunMO201','St_MO201_Run'),
            ('Screen_J6_Valves','ioVA101w' if False else 'tVA101',''),('Screen_J6_JetMill','ioSpF','Prm_SP_Feed'),
            ('Screen_J6_JetMill','ioPvG','St_P103')]
    print('\n--- IO域 ProcessValue(TagDynamization) 回读 ---')
    for scr,item,tag in checks:
        if not tag: continue
        print('%-14s %-12s dyn=%s'%(scr,item,has_dyn(scr,item)))
    nav=[('Screen_J6_Main','btnGoMotors'),('Screen_J6_Main','btnGoValves'),('Screen_J6_Main','btnGoJetMill'),
         ('Screen_J6_Motors','btnBackMain'),('Screen_J6_Valves','btnBackMain'),('Screen_J6_JetMill','btnBackMain')]
    print('\n--- 导航按钮 EventHandlers(Tapped) 回读 ---')
    for scr,item in nav:
        print('%-14s %-14s evt=%s'%(scr,item,has_evt(scr,item)))
    # 命令按钮抽查 (PressedStateTags / 事件)
    print('\n--- 命令按钮 抽查 ---')
    for scr,item in [('Screen_J6_Motors','btnStartMO201'),('Screen_J6_Valves','btnVA101Open'),('Screen_J6_JetMill','btnJetEnable')]:
        print('%-14s %-16s evt=%s'%(scr,item,has_evt(scr,item)))
    # 正确编译
    print('\n--- 编译 HMI ---')
    r=cvia('CompileAndDiagnoseHmi',{'softwarePath':HMI},600)
    print('Compile:', 'OK' if '"success":true' in r.replace(' ','') else r[:400])
finally:
    m.close()
