# -*- coding: utf-8 -*-
"""主画面端到端测试：布局 + 绑定 + 导航，并回读验证。"""
import sys, os, json
sys.path.insert(0, r'D:\系统\桌面\workbuddy\TIA_Tools')
os.environ['TIA_MCP_ATTACH_TIMEOUT_MS'] = '120000'
from mcp_client import MCP, text_of
HMI='HMI_RT_1'; W,H=1280,800
def T(n,l,t,w,h,text,size=16,bold=False):
    d={'name':n,'type':'Text','left':l,'top':t,'width':w,'height':h,'text':text,'font':{'Size':size,'Weight':'Bold' if bold else 'Normal'}}
    return d
def BTN(n,l,t,w,h,text): return {'name':n,'type':'Button','left':l,'top':t,'width':w,'height':h,'text':text}
def IOF(n,l,t,w,h): return {'name':n,'type':'IOField','left':l,'top':t,'width':w,'height':h}
items=[T('tTitle',20,12,760,44,'陕西天宇 J6 气流粉碎系统',26,True),
       T('tAlarm',20,72,180,28,'报警状态',18,True)]
al=[('ioAlmEM','急停动作'),('ioAlmFault','设备故障'),('ioAlmHiP','压力超限'),('ioAlmVfb','阀反馈异常'),('ioAlmAIB','变送器断线'),('ioEMOk','急停回路正常')]
for i,(io,lab) in enumerate(al):
    col=i%3;row=i//3;x=20+col*420;y=112+row*46
    items.append(T('t'+io,x,y,150,34,lab,15)); items.append(IOF(io,x+155,y,70,34))
items+=[T('tPress',20,218,220,28,'压力总览 (Bar)',18,True)]
pr=[('ioP101','P101 主管'),('ioP102','P102 进料'),('ioP103','P103 粉碎'),('ioP104','P104 喷吹'),('ioT101','T101 温度')]
for i,(io,lab) in enumerate(pr):
    x=20+i*250;y=258; items.append(T('t'+io,x,y,100,34,lab,15)); items.append(IOF(io,x+105,y,95,34))
items+=[T('tMotor',20,318,220,28,'电机运行状态',18,True)]
mo=[('ioM201run','MO201 给料'),('ioM601run','MO601 排风'),('ioM601Brun','MO601B 散热'),('ioM101run','MO101 喷吹')]
for i,(io,lab) in enumerate(mo):
    x=20+i*310;y=358; items.append(T('t'+io,x,y,150,34,lab,15)); items.append(IOF(io,x+155,y,80,34))
items+=[BTN('btnGoMotors',20,700,250,70,'电机控制'),BTN('btnGoValves',300,700,250,70,'阀门控制'),BTN('btnGoJetMill',580,700,250,70,'气流粉碎')]
m=MCP()
def c(n,a=None,t=600):
    try: return text_of(m.call(n,a or {},timeout=t))
    except Exception as e: return 'ERR '+str(e)
def cvia(n,a=None,t=600): return c('CallTool',{'name':n,'argumentsJson':json.dumps(a or {},ensure_ascii=False)},t)
def gp(scr,item,prop):
    return cvia('GetObjectProperty',{'objectKind':'HmiScreenItem','objectPath':'%s:%s:%s'%(HMI,scr,item),'propertyPath':prop},180)
try:
    m.initialize(); print('Connect:',c('Connect',t=240)[:100])
    cvia('EnsureUnifiedHmiScreen',{'hmiSoftwarePath':HMI,'screenName':'Screen_J6_Main','width':W,'height':H},240)
    r=cvia('ApplyUnifiedHmiScreenDesignJson',{'hmiSoftwarePath':HMI,'screenName':'Screen_J6_Main','designJson':json.dumps({'screenName':'Screen_J6_Main','width':W,'height':H,'items':items},ensure_ascii=False),'strict':True},600)
    print('Design:', 'OK' if '"success":true' in r.replace(' ','') else r[:400])
    # 绑定 ioP101 (Float St_P101) 与 ioAlmEM (Bool St_AlmEM)
    for it,dt,tag in [('ioP101','Float','St_P101'),('ioAlmEM','Bool','St_AlmEM'),('ioM201run','Bool','St_MO201_Run')]:
        r=cvia('BindUnifiedHmiTagDynamization',{'hmiSoftwarePath':HMI,'screenName':'Screen_J6_Main','itemName':it,'propertyName':'ProcessValue','tagName':tag,'dataType':dt},180)
        print('DYN %s->%s :'%(it,tag), 'OK' if '"success":true' in r.replace(' ','') else r[:200])
    # 回读 ProcessValue 与 dynamization
    for it in ['ioP101','ioAlmEM','ioM201run']:
        print('  回读',it,'ProcessValue =', gp('Screen_J6_Main',it,'ProcessValue')[:200])
        print('  回读',it,'Dynamizations =', gp('Screen_J6_Main',it,'Dynamizations')[:300])
    # 导航按钮
    cvia('EnsureUnifiedHmiButtonEventHandler',{'hmiSoftwarePath':HMI,'screenName':'Screen_J6_Main','buttonName':'btnGoMotors','eventType':'Tapped'},180)
    r=cvia('SetUnifiedHmiButtonEventScriptCode',{'hmiSoftwarePath':HMI,'screenName':'Screen_J6_Main','buttonName':'btnGoMotors','eventType':'Tapped','scriptCode':'ActivateScreen("Screen_J6_Motors");','globalDefinitionAreaScriptCode':'','async':False,'syntaxCheck':False},180)
    print('NAV btnGoMotors:', 'OK' if '"success":true' in r.replace(' ','') else r[:300])
    print('  回读 btnGoMotors EventHandlers:', gp('Screen_J6_Main','btnGoMotors','EventHandlers')[:400])
finally:
    m.close()
