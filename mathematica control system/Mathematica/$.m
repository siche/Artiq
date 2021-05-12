(* ::Package:: *)

Begin["System`"];
Unprotect[$];
ClearAll[Val,$,New,Free];
End[];

SetAttributes[Val,HoldAll];
Val[$Failed]=$Failed;
Val[sym_Symbol]:=With[{h=HoldComplete[sym]},If[#===h,$Failed,#[[1]]]&@(h/. (OwnValues[sym]/. $Failed->{h->$Failed}))];
Val[head_[body__]]:=With[{$head=head,$body=body},If[Hold[#]===Hold[$head[$body]],$Failed,#]&@$head[$body]];
Val[head_[]]:=With[{$head=head},If[Hold[#]===Hold[$head[]],$Failed,#]&@$head[]];
Val[exprs__]:=If[#==={},$Failed,#[[1]]]&@
Select[Val/@Unevaluated[{exprs}],#=!=$Failed&,1];
(*Select[List@@(Val/@Hold[exprs]),#=!=$Failed&,1];*)

$[obj_Symbol,$obj_Symbol:$Failed]:=(If[$obj=!=$Failed,obj["$"]=$obj];
((Evaluate@obj)/:obj.name_?AtomQ:=Block[{$=obj,$$=obj},
While[$$=!=$Failed,If[#=!=$Failed,Return[#],$$=Val@$$@"$"]&@Val[$$@ToString@Unevaluated@name]]]);
((Evaluate@obj)/:obj.((name_?AtomQ)[params___]):=Block[{$=obj,$$=obj},
While[$$=!=$Failed,
If[#=!=$Failed,Return[#],$$=Val@$$@"$"]&@Val[($$@ToString@Unevaluated@name)[params]]]]);obj);
Protect[$];

SetAttributes[New,HoldAll];
New[class_?AtomQ[params___]]:=Block[{$=New[class]},class[params];$];
New[class_?AtomQ]:=$[Symbol[ToString@class<>(*"`"<>*)ToString@Unique[]],Symbol@ToString@class];

SetAttributes[Free,HoldAll];
Free[objs__Symbol]:=(Dot@@{Unevaluated@#,Symbol["$"<>ToString[#.$]][]}&/@{objs};
Off[Remove::remal];Remove[Evaluate@objs];Remove[objs];On[Remove::remal]);

SetAttributes[Dot,HoldRest];
Unprotect[Dot];
(*ClearAll[Dot];*)
Dot[x_,y_?ValueQ]:=x.Evaluate@y;
Dot/:HoldPattern[sym_Symbol.name_?AtomQ=value_]:=With[{obj=sym},(obj@Evaluate@ToString@Unevaluated@name)=value];
Dot/:HoldPattern[sym_Symbol.(name_?AtomQ[params___]=value_)]:=With[{obj=sym},(obj@Evaluate@ToString@Unevaluated@name)[params]=value];
Dot/:HoldPattern[sym_Symbol.name_?AtomQ:=value_]:=With[{obj=sym},obj@Evaluate@ToString@Unevaluated@name:=value];
Dot/:HoldPattern[sym_Symbol.(name_?AtomQ[params___]):=value_]:=With[{obj=sym},(obj@Evaluate@ToString@Unevaluated@name)[params]:=value];
Protect[Dot];
