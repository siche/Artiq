function CtrlEventHandler(ctrl,path)
    [path,name,ext] = fileparts(path);
    old = cd(path);
    func = eval('@name');
    func(ctrl);
    cd(old);
end