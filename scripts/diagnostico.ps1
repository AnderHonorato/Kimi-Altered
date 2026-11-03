# Diagnostico informativo para Windows: nao baixa nem altera o sistema.
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Write-Host "=== Kimi-Altered | Diagnostico do Windows ===" -ForegroundColor Cyan

try {
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    $os = Get-CimInstance Win32_OperatingSystem
    $discos = @(Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3")
} catch {
    Write-Error "Nao foi possivel consultar o hardware: $_"
    exit 1
}

$ramGiB = [math]::Round(([double]$os.TotalVisibleMemorySize * 1024 / 1GB), 2)
Write-Host ("CPU: {0}" -f $cpu.Name)
Write-Host ("Nucleos fisicos: {0}; processadores logicos: {1}" -f $cpu.NumberOfCores, $cpu.NumberOfLogicalProcessors)
Write-Host ("RAM total: {0} GiB" -f $ramGiB)
Write-Host "AVX2 + FMA: necessario no x86-64; confirmacao automatica nao implementada."
Write-Host ""
Write-Host "Armazenamento local (1,7 TB livres e a referencia do projeto original):"
$temEspaco = $false
foreach ($disco in $discos) {
    $livreTB = [math]::Round(([double]$disco.FreeSpace / 1e12), 2)
    $totalTB = [math]::Round(([double]$disco.Size / 1e12), 2)
    $ok = ([double]$disco.FreeSpace -ge 1700000000000)
    if ($ok) { $temEspaco = $true }
    $sinal = if ($ok) { "possivel" } else { "insuficiente" }
    Write-Host ("  {0}  livre {1} TB / total {2} TB  -> {3}" -f $disco.DeviceID, $livreTB, $totalTB, $sinal)
}

Write-Host ""
foreach ($nome in @("git", "gcc", "make", "python", "bash")) {
    $comando = Get-Command $nome -ErrorAction SilentlyContinue
    $resultado = if ($comando) { "disponivel" } else { "nao encontrado neste terminal" }
    Write-Host ("{0}: {1}" -f $nome, $resultado)
}

Write-Host ""
if ($ramGiB -lt 10) {
    Write-Warning "RAM muito limitada para Windows + modelo. Os 8,24 GB publicados sao pico do processo, nao o sistema inteiro."
} else {
    Write-Host "RAM: capacidade a avaliar; a velocidade depende fortemente de CPU e SSD."
}
if (-not $temEspaco) {
    Write-Warning "Nenhuma unidade local tem 1,7 TB livres; nao baixe o checkpoint completo por enquanto."
}
Write-Host "O diagnostico nao comprova suporte AVX2/FMA, largura de banda do SSD ou inferencia real."
