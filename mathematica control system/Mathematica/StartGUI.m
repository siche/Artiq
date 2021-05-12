(* ::Package:: *)

(* ::Input::Initialization:: *)
<<D:\Data\Mathematica\Include.m;
Include/@{"SerialDevices.nb","TCPIPDevices.nb","APP.nb","GUI.nb"};
Laser370Connect[]
Laser399Connect[]
Laser935Connect[]
(*CurrentSource=OpenSerialDevice["COM13"];
Quiet[Close@$redpitaya];
$redpitaya=SocketConnect["192.168.32.110:5000"];
InitializeCCD[]*)
ControlPanel[];
