function CtrlSetValue(ctrl,val)
    CallVI('CtrlSetValue',{'reference','variant'},{ctrl,val});
end