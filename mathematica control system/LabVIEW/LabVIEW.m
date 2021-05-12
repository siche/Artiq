(* ::Package:: *)

If[$VersionNumber < 10,
System`Association[list:{__Rule}][key_]:=key/.list;
System`Association/:System`ReplaceAll[key_,System`Association[list:{__Rule}]]:=key/.list;
]

Needs["NETLink`"];
Off[NET::netexcptn];
Off[LoadNETAssembly::noload];
LoadNETAssembly@FileNameJoin@{DirectoryName@$InputFileName,"dll","LabVIEW.dll"};
On[NET::netexcptn];
Off[LoadNETAssembly::noload];

System`Each[lst_,expr_]:=(expr@@#)&/@lst;
System`Invert[assoc_Association]:=Association@Each[{Values@assoc,Keys@assoc}\[Transpose],Rule];

ClearAll[AppCls,LVLink,Inited];
VIDir=FileNameJoin[{DirectoryName@$InputFileName,"vi"}]<>"\\";

ClearAll[LoadVI,RunVI,AbortVI,MakeAndCastNETObject,CallVI,CtrlGetValue,CtrlSetValue,CtrlSignalValue,
GetAllCtrls,FindCtrl,Env,Queue,LinkLV,Init]

(*resv default to be True for LabVIEW 2011*)
LoadVI[viname_String,option_Integer:16,resv_Symbol:False]:=Module[{vipath,r},
vipath=If[StringLength@viname>3&&StringTake[viname,-3]==".vi"&&!StringFreeQ[viname,"\\"|"/"],viname,VIDir<>viname<>".vi"];
r=AppCls@GetVIReference[vipath,"",resv,option];
If[r=!=$Failed,LoadVI[viname]=r];
r
];
(* ReleaseNETObject/@DownValues[LoadVI][[1;;-2,2]] *)

RunVI[viname_String]:=Module[{vi=LoadVI[viname]},
If[vi@ExecState=!=LabVIEW`ExecStateEnum`eRunTopLevel,
vi@FPWinOpen=True;vi@Run[True]]];

AbortVI[viname_String]:=Module[{vi=LoadVI[viname]},
If[vi@ExecState===LabVIEW`ExecStateEnum`eRunTopLevel,vi@Abort[]]];

MakeAndCastNETObject[obj_Integer,type_]:=NETLink`CastNETObject[
NETLink`MakeNETObject[obj,"System.UInt32"],type];

MakeAndCastNETObject[obj_,type_]:=Module[{r=obj},
If[!NETLink`NETObjectQ[r],r=NETLink`MakeNETObject[r]];
If[r===$Failed,obj,
If[NETLink`InstanceOf[r,"System.__ComObject"],r,NETLink`CastNETObject[r,type]]]
];

CallVI[vi_?NETLink`NETObjectQ,paramNames_List,paramVals_List]:=Module[{param1,param2,r},
NETLink`BeginNETBlock[];
param1=NETLink`CastNETObject[NETLink`MakeNETObject[paramNames],"object"];
param2=NETLink`ReturnAsNETObject[MakeAndCastNETObject[MakeAndCastNETObject[#,"object"]&/@ paramVals,"object"]];
vi@Call[param1,param2];
r=NETLink`NETObjectToExpression[param2];
NETLink`EndNETBlock[];
r
];
CallVI[viname_String,paramNames_List,paramVals_List]:=CallVI[LoadVI[viname],paramNames,paramVals];

CtrlGetValue[ctrl_Integer]:=CallVI["CtrlGetValue",{"reference","variant"},{ctrl,""}][[-1]];

CtrlSetValue[ctrl_Integer,variant_]:=CallVI["CtrlSetValue",{"reference","variant"},{ctrl,variant}][[-1]];

CtrlSignalValue[ctrl_Integer,variant_]:=CallVI["CtrlSignalValue",{"reference","variant"},{ctrl,variant}][[-1]];

GetAllCtrls[vi_?NETLink`NETObjectQ,prefix_:""]:=Association[Rule@@#&/@(CallVI["GetAllCtrls",{"VI","Prefix","Ctrls"},{vi,prefix,""}][[-1]])];
GetAllCtrls[viname_String,prefix_:""]:=GetAllCtrls[LoadVI[viname],prefix];

FindCtrl[vi_?NETLink`NETObjectQ,name_String]:=CallVI["FindCtrl",{"VI","Name","Ctrl"},{vi,name,""}][[-1]];
FindCtrl[viname_String,name_String]:=FindCtrl[LoadVI[viname],name];

Env[name_String]:=Module[{value,names,values},
{value,names,values}=CallVI["Env",{"Name","Value Out","names","values"},{name,"","",""}][[2;;-1]];
If[Length[names]==0,value,
{value,Rule@@#&/@Transpose[{names,values}]}
]
];

Env[name_String,value_]:=(CallVI["Env",{"Name","Value In"},{name,value}];);

(*Peak[data_List, fitfunc_String] := 
  CallVI["Peak", {"2d Data", "Fitting Function", "Peak Center", 
     "Peak Width", "Peak Height"}, {Transpose[data], fitfunc, 0, 0, 
     0}][[-3 ;; -1]];*)

Queue[name_String,value_:""]:=CallVI["Queue",{"Name","Mode","Value In","Value Out"},{name,Boole[value===""],value,""}][[-1]];

Console[str_String]:=(CallVI["Console",{"print string"},{str}];);

LinkLV[name_String:"LabVIEW"]:=(
If[Head@LVLink===LinkObject,
Off[LinkObject::linkv,LinkObject::linkn];
MathLink`SetDaemon[LVLink,False];
MathLink`LinkRemoveInterruptMessageHandler[LVLink];
MathLink`RemoveSharingLink[LVLink];
LinkClose[LVLink];
On[LinkObject::linkv,LinkObject::linkn];
];
LVLink=LinkCreate[name,LinkProtocol->"SharedMemory"];
MathLink`AddSharingLink[LVLink,MathLink`AllowPreemptive->True,MathLink`ImmediateStart->True];
MathLink`LinkAddInterruptMessageHandler[LVLink];
MathLink`SetDaemon[LVLink,True];
);

InitLV[]:=(
Quiet[
NETLink`ReleaseNETObject[AppCls]; 
ClearAll[AppCls];
];
AppCls=NETLink`NETNew["LabVIEW.ApplicationClass"];
);

InitLV[];
