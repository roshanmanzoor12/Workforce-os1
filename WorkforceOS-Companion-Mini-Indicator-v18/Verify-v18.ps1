param([string]$Root='C:\workforce-os')
$ErrorActionPreference='Stop'
$Program = Get-Content (Join-Path $Root 'agent\WorkforceOS.ScreenCompanion\Program.cs') -Raw
foreach ($marker in @('WFOS_V18_MINI_SHARING_OVERLAY','SetWindowDisplayAffinity','Controls.Add(controlRow)','STOP SHARING','TopMost = true')) {
  if (!$Program.Contains($marker)) {throw "V18 source verification failed: $marker"}
}
if ($Program.Contains('Controls.Add(_preview)')) {throw 'Recursive preview remains attached to Companion window'}
Write-Host 'V18 SOURCE VERIFICATION PASS; native Windows build/runtime verification is separate.' -ForegroundColor Green
