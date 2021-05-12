import sys,clr,os

#__dir__ = os.path.abspath(inspect.stack()[0][1])
__dir__ = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(__dir__,'./dll'))
LabVIEWInterop = clr.AddReference('LabVIEW')
from LabVIEW import ApplicationClass,VirtualInstrument

AppCls = ApplicationClass()
VIDir = os.path.normcase(os.path.join(__dir__,'./vi/'))
_LoadVI = {}
def LoadVI(name, option=16, resv=False):
    if name in _LoadVI:
        return _LoadVI[name]
    path = os.path.normcase(name) if name[-3:] == '.vi' or '\\' in name or '/' in name else VIDir + name + '.vi'
    _LoadVI[name] = vi = VirtualInstrument(AppCls.GetVIReference(path,'',resv,option))
    return vi

from System import Object
def FromObject(obj):
    if isinstance(obj,Object):
        t = obj.GetType()
        if t.IsArray:
            return [FromObject(i) for i in obj]
    return obj
    
def CallVI(vi, names, vals):
    if type(vi) is str:
        vi = LoadVI(vi)
    r = vi.Call(names,vals)[2]
    return FromObject(r)

def CurrentTimeString():
    return CallVI('CurrentTimeString',['date/time string'],[0])[0]

def CtrlGetValue(ctrl):
    return CallVI('CtrlGetValue',['reference','variant'],[ctrl,0])[-1]

def CtrlSetValue(ctrl, value):
    CallVI('CtrlSetValue',['reference','variant'],[ctrl,value])

def CtrlSignalValue(ctrl, value):
    CallVI('CtrlSignalValue',['reference','variant'],[ctrl,value])

def GetAllCtrls(vi, prefix=''):
    if type(vi) is str:
        vi = LoadVI(vi)
    r = CallVI('GetAllCtrls',['VI','Prefix','Ctrls'],[vi,prefix,0])[-1]
    dict = {}
    for i in r:
        dict[i[0]] = i[1]
    return dict

def FindCtrl(vi, name):
    if type(vi) is str:
        vi = LoadVI(vi)
    return CallVI('FindCtrl',['VI','Name','Ctrl'],[vi,name,0])[-1]
    
def GetAllGObjs(vi, prefix=''):
    if type(vi) is str:
        vi = LoadVI(vi)
    r = CallVI('GetAllGObjs',['VI','Prefix','GObjs'],[vi,prefix,0])[-1]
    dict = {}
    for i in r:
        dict[i[0]] = i[1]
    return dict

def FindGObj(vi, name):
    if type(vi) is str:
        vi = LoadVI(vi)
    return CallVI('FindGObj',['VI','Name','GObj'],[vi,name,0])[-1]

def CtrlHandlerDiagram(structure, ctrl, event):
    return CallVI('CtrlHandlerDiagram',['Structure','Ctrl','Type','Diagram'],[structure,ctrl,event,0])[-1]
    
def CtrlHandlerNode(diagram, name, ctrl, event):
    CallVI('CtrlHandlerNode.Python',['Diagram','Name','Ctrl','Type'],[diagram,name,ctrl,event])

# Add Variant Delete Attribute?
def Env(name, value=None):
    if value == None:
        value,names,values = CallVI('Env',['Name','Value Out','names','values'],[name,0,0,0])[1:-1]
        return [value,[i for i in names],[j for j in values]]
    CallVI('Env',['Name','Value In'],[name,value])
    
def Console(string):
    CallVI('Console',['print string'],[string])
    
#from win32gui import *
import time
def ChartTest():
    vi = LoadVI('Chart',8)
    vi.FPWinOpen = True
    #SetWindowText(vi._FPWinOSWindow,'hehe')
    ctrl = FindCtrl(vi, 'Waveform Chart')
    print(ctrl)
    for i in xrange(100):
        time.sleep(0.1)
        CtrlSetValue(ctrl,i)

def GraphTest():
    vi = LoadVI('Graph',8)
    vi.FPWinOpen = True
    #SetWindowText(vi._FPWinOSWindow,'hehe')
    ctrl = FindCtrl(vi, 'Waveform Graph')
    print(ctrl)
    CtrlSetValue(ctrl,range(100))

def XYTest():
    vi = LoadVI('XY',8)
    vi.FPWinOpen = True
    vi.Call(['X','Y'],[range(100),range(100)])
    print(CtrlGetValue(FindCtrl('XY','XY Graph')))
                
if __name__ == '__main__':
    Console('main\n')
    ChartTest()
    GraphTest()
    XYTest()
    