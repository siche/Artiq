local com = require 'com'

local callmods = ParameterModifier(2)
callmods[0] = false
callmods[1] = true
callmods = luanet.make_array(ParameterModifier,{callmods})
local function vi_call(vi, args, values)
	local names
	if values == nil then
		names = {}
		values = {}
		for k,v in pairs(args) do
			names[#names + 1] = k
			values[#values + 1] = v
		end
	else
		names = args
	end
	names = luanet.make_array(Object, names)
	values = luanet.make_array(Object, values)
	args = luanet.make_array(Object, {names,values})
	local res,ok = com.invoke(vi, 'Call', args, callmods)
	return (res or args[1]),ok
end

__dir = debug.getinfo(1).source:gsub('/','\\'):match'@(.*)\\.*$' or io.popen'cd':read'*l'
VIDir = __dir..'\\.\\vi\\'

pcall(function()
require'lfs'
local dir = lfs.currentdir()
lfs.chdir(__dir..'\\.\\dll')
import 'LabVIEW.dll'
lfs.chdir(dir)
end)

import 'LabVIEW.dll'
AppCls = ApplicationClass()
_LoadVI = {}
function LoadVI(path, option, resv)
	if _LoadVI[path] then return _LoadVI[path] end
	if path:sub(-3) ~= '.vi' then path = VIDir..path..'.vi' end
	option = option or 16
	if resv == nil then resv = false end
	local vi = setmetatable({vi=AppCls:GetVIReference(path,'',resv,option)},{
	__index = function (self,key)
		return com.get(self.vi,key)
	end,
	__newindex = function (self,key,value)
		return com.set(self.vi,key,value)
	end,
	__call = function (self, ...)
		return vi_call(self.vi, ...)
	end
	})
	_LoadVI[path] = vi
	return vi
end

function CallVI(vi, args, values)
	if type(vi) == 'string' then
		vi = LoadVI(vi)
	end
	return vi(args, values)
end

function CurrentTimeString()
	return CallVI('CurrentTimeString', {'date/time string'}, {0})[0]
end

function CtrlGetValue(ctrl)
    return CallVI('CtrlGetValue', {'reference','variant'}, {ctrl,0})[1]
end

function CtrlSetValue(ctrl, value)
    local res,ok = CallVI('CtrlSetValue', {'reference','variant'}, {ctrl,value})
    return ok,res
end

function CtrlSignalValue(ctrl, value)
    local res,ok = CallVI('CtrlSignalValue', {'reference','variant'}, {ctrl,value})
    return ok,res
end

function GetAllCtrls(vi, prefix)
	prefix = prefix or ''
	if type(vi) == 'string' then
		vi = LoadVI(vi)
	end
	local r = CallVI('GetAllCtrls',{'VI','Prefix','Ctrls'},{vi.vi,prefix,0})[2]
	local dict = {}
	for i in luanet.each(r) do
		dict[i[0]] = i[1]
	end
	return dict
end

function Console(text)
	local vi = LoadVI('Console')
	vi{['print string'] = text}
	vi.FPWinOpen = true
end

function Queue(name, value)
	if value == nil then
        return CallVI('Queue',{'Name','Mode','Value In','Value Out'},{name,1,'',''})[3]
	else
        CallVI('Queue',{'Name','Mode','Value In','Value Out'},{name,0,val,''})
    end
end

if not pcall(debug.getlocal, 4, 1) then
Console(CurrentTimeString()..'\n')
ctrls = GetAllCtrls('Console')
table.foreach(ctrls,print)
--Console(CurrentTimeString()..'\n')
CtrlSetValue(ctrls.console,CurrentTimeString()..'\n')
LoadVI('Console').FPWinOpen = true
print(CtrlGetValue(ctrls.console))
end