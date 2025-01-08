param (
    [Parameter(Mandatory=$true)][string]$pythoninstcacheprefix,
    [Parameter(Mandatory=$true)][string]$pythoninstexe,
    [Parameter(Mandatory=$true)][string]$pythoninsturl
)
if (!(Test-Path "./downloaded/${pythoninstcacheprefix}/${pythoninstexe}")) {
    New-Item -Type Directory -Force ./downloaded/${pythoninstcacheprefix}
    Invoke-WebRequest -Uri "${pythoninsturl}/${pythoninstexe}" -OutFile "./downloaded/${pythoninstcacheprefix}/${pythoninstexe}"
}
#run exe and wauit for its completion
& "downloaded/${pythoninstcacheprefix}/${pythoninstexe}" /quiet AssociateFiles=0 Include_doc=0 Include_dev=0 Include_launcher=0 Include_pip=0 Include_test=0 Shortcuts=0 "DefaultJustForMeTargetDir=${PSScriptRoot}\expanded" | Out-Default