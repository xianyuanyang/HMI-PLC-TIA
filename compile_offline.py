# -*- coding: utf-8 -*-
"""HMI 离线后编译，校验布局无误。"""
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
try:
    m.initialize(); print('Connect:',c('Connect',t=240)[:80])
    print('GoOffline:', c('GoOffline',{'softwarePath':HMI},300)[:200])
    r=cvia('CompileAndDiagnoseHmi',{'softwarePath':HMI},600)
    print('Compile HMI:', 'OK' if '"success":true' in r.replace(' ','') else r[:500])
finally:
    m.close()
