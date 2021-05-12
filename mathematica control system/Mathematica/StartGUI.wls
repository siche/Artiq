#!/usr/bin/env wolframscript
(* ::Package:: *)

(* ::Input::Initialization:: *)
(*Needs["JLink`"]; 
$FrontEndLaunchCommand="C:\\Program Files\\Wolfram Research\\Mathematica\\11.3\\Mathematica.exe";
If[ConnectToFrontEnd[],UseFrontEnd[
FrontEndTokenExecute[
NotebookOpen["D:\\Data\\Mathematica\\StartGUI.m", Visible -> False],"EvaluateInitialization"]]]*)
Needs["JLink`"]; 
$FrontEndLaunchCommand = "C:\\Program Files\\Wolfram Research\\Mathematica\\11.3\\Mathematica.exe";
ConnectToFrontEnd[]; 
UseFrontEnd[Module[{}, file = "D:\\Data\\Mathematica\\StartGUI.m"; 
targetnotebook = NotebookOpen[file, Visible -> True]; 
SelectionMove[targetnotebook, Next, Cell]; 
SelectionEvaluate[targetnotebook];]];
