(* ::Package:: *)

Begin["System`"];
ClearAll[Include,$Directory,$File];
End[];

Include[path__String]:=Block[{$File=#},
If[FileExtension@#=="nb",Import[#,"Initialization"],Get@#]]&@FileNameJoin@{path};
Include[path_String]:=Include[$Directory,path];
$File=$Input;
(*If[!ValueQ@$File,$File=NotebookFileName[]];*)
$Directory:=If[#==="",NotebookDirectory[],#]&@DirectoryName@$File;
