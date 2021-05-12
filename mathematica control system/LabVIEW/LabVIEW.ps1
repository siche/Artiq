#Add-Type -Path 'D:\Laf\LabVIEW\LabVIEW.dll'
#$lv = New-Object LabVIEW.ApplicationClass
#$lv = New-Object -ComObject LabVIEW.Application
#echo $lv.ApplicationDirectory
#$lv.GetVIReference('D:\Laf\LabVIEW\Console.vi','',$False,16)

Add-Type -Path 'D:\Laf\LabVIEW\Wolfram.NETLink.dll'
$mma = New-Object Wolfram.NETLink.MathKernel
#$mma.Connect()

$mma.LinkArguments = "-linkmode connect -linkname LabVIEW"
$mma.AutoCloseLink = $true
$mma.ResultFormat = "InputForm"

$mma.Compute('100!')
echo $mma.Result

cd (Split-Path -Path $($global:MyInvocation.MyCommand.Path))
$vbs = New-Object -ComObject MSScriptControl.ScriptControl
$vbs.Language = "VBScript"
$vbs.AddCode([string]::Join("`n", (Get-Content .\LabVIEW.vbs)))
$vbs = $vbs.CodeObject

function Load-VbsCode {
  param($vbsCode = $(throw "No VBS code specified."))
  $vbs = New-Object -ComObject MSScriptControl.ScriptControl
  #$vbs = New-Object -ComObject ScriptControl
  $vbs.Language = "VBScript"
  $vbs.AddCode([string]::Join("`n", $vbsCode))
  return $vbs
}

function GetAllCtrls {
    param($path)
    $dict = $vbs.GetAllCtrls($path)
    $ctrls = @{}
    foreach ($key in $dict.Keys()) {
        $ctrls[$key] = $dict.Item($key)
    }
    return $ctrls
}

function CtrlGetValue {
    param($ctrl)
    return $vbs.CtrlGetValue($ctrl)
}

function CtrlSetValue {
    param($ctrl,$val)
    return $vbs.CtrlSetValue($ctrl,$val)
}

function CtrlSignalValue {
    param($ctrl,$val)
    return $vbs.CtrlSignalValue($ctrl,$val)
}

# get contents of the vbs file
#$vbsCode = Get-Content .\LabVIEW.vbs

#$vbs = Load-VbsCode('Sub MessageBox(Byval s) MsgBox s End Sub')
#$vbs.CodeObject.MessageBox(3)

#$vbsCode = "Function Celsius(Byval GradF) Celsius = (GradF - 32) * 5 / 9 End Function"

# pass the vbs code to Load-VbsCode
#$vbs = Load-VbsCode($vbsCode)

$vbs.Console($mma.Result)
$ctrls =GetAllCtrls('Console')
echo (CtrlGetValue($ctrls['console']))

$mma.Dispose()

# Ready to use the Celsius function...
#$f = 70
#$c = $vbs.CodeObject.Celsius($f)
#Write-Host "$f Fahrenheit are $c Celsius."

#$vbs = Load-VbsCode('Function COMObject(Byval s) COMObject = CreateObject(s) End Function')
#$lv = $vbs.CodeObject.COMObject('LabVIEW.Application')
#echo $lv.ApplicationDirectory

#$a = new-object -comobject MSScriptControl.ScriptControl
#$a.language = “vbscript”
#$a.addcode("function getInput() getInput = inputbox(`"Message box prompt`",`"Message Box Title`") end function")
#$b = $a.eval("getInput")