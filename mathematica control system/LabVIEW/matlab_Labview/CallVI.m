function values = CallVI(vi, names, values)
    if ischar(vi)
        vi = LoadVI(vi);
    end
    len = size(names,2);
    arg1 = NET.createArray('System.String', len);
    for i=1:len
        arg1(i) = names{i};
    end
    arg2 = NET.createArray('System.Object', len);
    for i=1:len
        arg2(i) = values{i};
    end
    [~,arg2] = vi.Call(arg1,arg2);
    values = {}
    for i=1:len
        values{i} = arg2(i);
    end
end