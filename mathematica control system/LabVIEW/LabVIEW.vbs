Sub Include(sInstFile)  
    Dim oFSO, f, s  
    Set oFSO = CreateObject("Scripting.FileSystemObject")  
    Set f = oFSO.OpenTextFile(sInstFile)  
    s = f.ReadAll  
    f.Close  
    ExecuteGlobal s  
End Sub  

Set lv = CreateObject("LabVIEW.Application")
'MsgBox lv.ApplicationDirectory

'VIDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
VIDir = "D:\Laf\LabVIEW\vi"
Set VIs = CreateObject("scripting.dictionary")

Function LoadVI(sPath)
	If Right(sPath,3) <> ".vi" Then
		sPath = VIDir & "\" & sPath & ".vi"
	End If
	If Not VIs.Exists(sPath) Then	
		VIs.Add sPath,lv.GetVIReference(sPath,"",False,16)
	End If
	Set LoadVI = VIs(sPath)
End Function

Function CallVI(vi,names,vals)
	If TypeName(vi) <> "IVI" Then
		Set vi = LoadVI(vi)
	End If
	vi.Call names,vals
	CallVI = vals
End Function

Function GetAllCtrls(vi)
	If TypeName(vi) <> "IVI" Then
		Set vi = LoadVI(vi)
	End If
	ctrls = CallVI("GetAllCtrls",Array("VI","Prefix","Ctrls"),Array(vi,"",Null))(2)
	Set GetAllCtrls = CreateObject("scripting.dictionary")
	For Each ctrl In ctrls
		GetAllCtrls.Add ctrl(0),ctrl(1)
	Next
End Function

Function CtrlGetValue(ctrl)
    CtrlGetValue = CallVI("CtrlGetValue",Array("reference","variant"),Array(ctrl,0))(1)
End Function

Sub CtrlSetValue(ctrl,value)
    res = CallVI("CtrlSetValue",Array("reference","variant"),Array(ctrl,value))
End Sub

Sub CtrlSignalValue(ctrl, value)
    res = CallVI("CtrlSignalValue",Array("reference","variant"),Array(ctrl,value))
End Sub

Sub RunVI(vi)
	If TypeName(vi) <> "IVI" Then
		Set vi = LoadVI(vi)
	End If
	If vi.ExecState <> lv.ExecStateNum.eRunTopLevel Then
        FPWinOpen vi, True
    Else
        vi.Run
    End If
End Sub

Sub AbortVI(vi)
	If TypeName(vi) <> "IVI" Then
		Set vi = LoadVI(vi)
	End If
	vi.Abort
End Sub

Sub FPWinOpen(vi,val)
	If TypeName(vi) <> "IVI" Then
		Set vi = LoadVI(vi)
	End If
	vi.FPWinOpen = val
End Sub

Sub Console(sText)
	Set vi = LoadVI("Console")
	FPWinOpen vi, True
	res = CallVI(vi,Array("print string"),Array(sText))
End Sub

Console lv.ApplicationDirectory