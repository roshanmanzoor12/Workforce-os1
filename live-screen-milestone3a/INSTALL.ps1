#Requires -Version 5.1
param([string]$Root = 'C:\workforce-os')
$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot 'CHECK.ps1'
& $script -Root $Root
if (-not $?) { throw 'Milestone 3A preflight failed.' }
