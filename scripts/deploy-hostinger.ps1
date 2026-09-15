<#
.SYNOPSIS
  Sube la landing de SWIFTYALATINO a Hostinger vía SFTP.

.DESCRIPTION
  Requiere el módulo "Posh-SSH" (o WinSCP .NET assembly) instalado, y las credenciales
  SFTP de Hostinger (hPanel > Avanzado > SFTP/FTP). NUNCA se deben pegar credenciales
  reales dentro de este repo; se solicitan de forma interactiva o vía variables de entorno.

.PARAMETER HostName
  Host SFTP de Hostinger, ej: xx.xx.xx.xx o ftp.tudominio.com

.PARAMETER UserName
  Usuario SFTP.

.PARAMETER RemotePath
  Carpeta destino, normalmente: /public_html o /public_html/dominio (si es addon domain).

.EXAMPLE
  ./deploy-hostinger.ps1 -HostName "xx.xx.xx.xx" -UserName "u123456789" -RemotePath "/public_html"
#>

param(
  [Parameter(Mandatory=$true)][string]$HostName,
  [Parameter(Mandatory=$true)][string]$UserName,
  [string]$RemotePath = "/public_html",
  [int]$Port = 65002
)

if (-not (Get-Module -ListAvailable -Name Posh-SSH)) {
  Write-Host "Instalando módulo Posh-SSH..." -ForegroundColor Yellow
  Install-Module -Name Posh-SSH -Scope CurrentUser -Force
}
Import-Module Posh-SSH

$SecurePassword = Read-Host "Password SFTP de Hostinger" -AsSecureString
$Credential = New-Object System.Management.Automation.PSCredential ($UserName, $SecurePassword)

$Session = New-SFTPSession -ComputerName $HostName -Credential $Credential -Port $Port -AcceptKey

$LocalRoot = Split-Path -Parent $PSScriptRoot
$FilesToUpload = @(
  "index.html", "robots.txt", "sitemap.xml", ".htaccess"
)

foreach ($file in $FilesToUpload) {
  $localFile = Join-Path $LocalRoot $file
  if (Test-Path $localFile) {
    Set-SFTPFile -SessionId $Session.SessionId -LocalFile $localFile -RemotePath $RemotePath -Overwrite
    Write-Host "Subido: $file" -ForegroundColor Green
  }
}

# Subir carpetas completas
Set-SFTPFolder -SessionId $Session.SessionId -LocalFolder (Join-Path $LocalRoot "assets") -RemotePath "$RemotePath/assets" -Overwrite
Set-SFTPFolder -SessionId $Session.SessionId -LocalFolder (Join-Path $LocalRoot "blog") -RemotePath "$RemotePath/blog" -Overwrite

Remove-SFTPSession -SessionId $Session.SessionId
Write-Host "Despliegue completado en $HostName$RemotePath" -ForegroundColor Cyan
