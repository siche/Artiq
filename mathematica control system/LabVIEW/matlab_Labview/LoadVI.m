function vi = LoadVI(varargin)
    persistent mdir lvdir appcls vis
    if isa(appcls,'double')
        matlab.engine.shareEngine;
        enableservice('AutomationServer', true);
        %regmatlabserver;
        mdir = [fileparts(mfilename('fullpath')) '\'];
        addpath(mdir);
        lvdir = [mdir '..\LabVIEW\'];
        NET.addAssembly([lvdir, 'LabVIEW.dll']);
        appcls = LabVIEW.ApplicationClass();
        vis = containers.Map();
    end
    if nargin > 0
        name = varargin{1};
    else
        name = '';
    end
    if nargin > 1
        option = varargin{2};
    else
        option = 16;
    end
    if name
        if isKey(vis,{name})
            vi = vis(name);
        else
            vi = appcls.GetVIReference([lvdir,name,'.vi'],'',false,option);
            vis(name) = vi;
        end
    end
end