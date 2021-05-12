function val = CtrlGetValue(ctrl)
    values = CallVI('CtrlGetValue',{'reference','variant'},{ctrl,''});
    val = values{2};
end