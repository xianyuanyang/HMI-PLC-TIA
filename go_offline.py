# -*- coding: utf-8 -*-
"""先把博图切回离线模式（PLC 和 HMI 都离线）。"""
import sys, os
sys.path.insert(0, r'D:\系统\桌面\workbuddy\TIA_Tools')
os.environ['TIA_MCP_ATTACH_TIMEOUT_MS'] = '90000'
from mcp_client import MCP, text_of

m = MCP()
try:
    m.initialize()
    def c(n, a=None, t=300):
        try:
            return text_of(m.call(n, a or {}, timeout=t))
        except Exception as e:
            return 'ERR ' + str(e)

    print('===== Connect ====='); print(c('Connect', t=180)[:150])
    print('===== GoOffline G2_PLC_1 =====')
    print(c('GoOffline', {'softwarePath': 'G2_PLC_1'}, t=300)[:300])
finally:
    m.close()
