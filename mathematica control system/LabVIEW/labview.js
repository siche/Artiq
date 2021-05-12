var edge = require('edge');

var LabVIEW = edge.func({source : function() {/*
        using System.Threading.Tasks;
        using LabVIEW;
        using System.Collections.Generic;

        public class Startup
        {   
            static bool Inited = false;
            static string VIDir;
            static Application AppCls;
            static Dictionary<string,VirtualInstrument> VIs;
            public async Task<object> Invoke(object[] input)
            {   
                if (!Inited) {
                    AppCls = new ApplicationClass();
                    VIs = new Dictionary<string,VirtualInstrument>();
                    Inited = true;
                }
                if (input.Length == 1) {
                    VIDir = (string)input[0];
                    return null;
                }
                string path = (string)input[0];
                if (path.IndexOf(':') < 0) path = VIDir + "\\" + path + ".vi";
                VirtualInstrument vi;
                if (!VIs.TryGetValue(path, out vi)) {
                    vi = AppCls.GetVIReference(path,"",false,16);
                    VIs.Add(path,vi);
                }
                switch((int)input[1]) {
                case 0:
                    return "VI@" + path;
                case 1:
                    object[] vals = (object[])input[3];
                    for (var i = 0; i < vals.Length; ++i)
                        if (vals[i] is string && ((string)vals[i]).StartsWith("VI@"))
                            vals[i] = VIs[((string)vals[i]).Substring(3)];
                    object res = vals;
                    vi.Call(input[2],ref res);
                    return res;
                case 2:
                    return typeof(VirtualInstrument).GetProperty((string)input[2]).GetValue(vi,null);
                case 3:
                    typeof(VirtualInstrument).GetProperty((string)input[2]).SetValue(vi,input[3],null);
                    break;
                }
                return null;
            }
        }
*/},
references : [ __dirname + '\\.\\dll\\LabVIEW.dll' ]});

LabVIEW([__dirname + '\\.\\vi'], null);

LabVIEW.Load = function(name,cb) {LabVIEW([name,0],cb);};
LabVIEW.Call = function(name,args,vals,cb) {LabVIEW([name,1,args,vals],cb);};
LabVIEW.Get = function(name,key,cb) {LabVIEW([name,2,key],cb);}
LabVIEW.Set = function(name,key,val,cb) {LabVIEW([name,3,key,val],cb);}
LabVIEW.GetAllCtrls = function (name,cb) {
    LabVIEW.Load(name,function (err,res) {
        LabVIEW.Call('GetAllCtrls',['VI','Prefix','Ctrls'],[res,'',''], function(err,res) {
            var obj = {};
            res[2].forEach(function(v){obj[v[0]]=v[1];});
            cb(err,obj);
        });
    });
};
LabVIEW.CtrlGetValue = function (ctrl,cb) {
    LabVIEW.Call('CtrlGetValue',['reference','variant'],[ctrl,''], function(err,res) {cb(err,res[1]);});
};
LabVIEW.CtrlSetValue = function (ctrl,val,cb) {
    LabVIEW.Call('CtrlSetValue',['reference','variant'],[ctrl,val], function(err,res) {cb && cb(err,null);});
};
LabVIEW.CtrlSignalValue = function (ctrl,val,cb) {
    LabVIEW.Call('CtrlSignalValue',['reference','variant'],[ctrl,val], function(err,res) {cb && cb(err,null);});
};
LabVIEW.Console = function (str,cb) {
    LabVIEW.Set('Console','FPWinOpen',true,function(err,res){
        LabVIEW.Call('Console',['print string'],[str],function(err,res) {cb && cb(err,null);});
    });
};
LabVIEW.CurrentTimeString = function (cb) {
   LabVIEW.Call('CurrentTimeString',['date/time string'],[''],function(err,res) {cb(err,res[0]);});
};
LabVIEW.Queue = function (name,val,cb) {
    if (val == null) {
        LabVIEW.Call('Queue',['Name','Mode','Value In','Value Out'],[name,1,'',''],function(err,res){cb(err,res[3]);});
    } else {
        LabVIEW.Call('Queue',['Name','Mode','Value In','Value Out'],[name,0,val,''],function(err,res) {cb && cb(err,null);});
    }
};
module.exports = LabVIEW;

if (!module.parent) {
var cb = function(err, res){if(err) throw err;console.log(res);};
LabVIEW.Console('hehe',cb);
LabVIEW.CurrentTimeString(cb);
LabVIEW.GetAllCtrls('GetAllCtrls',cb);
}