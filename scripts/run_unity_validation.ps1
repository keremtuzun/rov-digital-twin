param(
    [string]$UnityEditor = 'C:\Program Files\Unity\Hub\Editor\6000.5.9f1\Editor\Unity.exe',
    [string]$OutputDirectory = 'tmp\unity-validation'
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$sourceProject = Join-Path $repoRoot 'unity'
$outputRoot = Join-Path $repoRoot $OutputDirectory
$temporaryBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$temporaryProject = Join-Path $temporaryBase ('oceansense-unity-' + [guid]::NewGuid().ToString('N'))
$temporaryProjectName = Split-Path -Leaf $temporaryProject
$locationPushed = $false

function Invoke-UnityEditor {
    param([string[]]$Arguments)
    $quotedArguments = foreach ($argument in $Arguments) {
        if ($argument -match '\s') { '"' + $argument.Replace('"', '\"') + '"' } else { $argument }
    }
    $process = Start-Process -FilePath $UnityEditor -ArgumentList $quotedArguments `
        -Wait -PassThru -WindowStyle Hidden
    return $process.ExitCode
}

if (-not (Test-Path -LiteralPath $UnityEditor -PathType Leaf)) {
    throw "Unity editor not found: $UnityEditor"
}
New-Item -ItemType Directory -Path $temporaryProject -Force | Out-Null
New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null
foreach ($staleResult in @('compile.log', 'editmode.log', 'editmode.xml', 'playmode.log', 'playmode.xml', 'summary.json')) {
    $stalePath = Join-Path $outputRoot $staleResult
    if (Test-Path -LiteralPath $stalePath -PathType Leaf) {
        Remove-Item -LiteralPath $stalePath -Force
    }
}

try {
    foreach ($directory in @('Assets', 'Packages', 'ProjectSettings')) {
        Copy-Item -LiteralPath (Join-Path $sourceProject $directory) -Destination $temporaryProject -Recurse
    }

    # Unity 6 can incorrectly prepend a OneDrive/reparse-point working directory to
    # an otherwise absolute -projectPath. Invoke it from TEMP with the verified leaf.
    Push-Location $temporaryBase
    $locationPushed = $true

    $compileLog = Join-Path $outputRoot 'compile.log'
    $exitCode = Invoke-UnityEditor @('-batchmode', '-nographics', '-quit', '-projectPath',
        $temporaryProjectName, '-logFile', $compileLog)
    if ($exitCode -ne 0) { throw "Unity compilation failed with exit code $exitCode" }
    if (Select-String -Path $compileLog -Pattern 'error CS\d+|Scripts have compiler errors' -Quiet) {
        throw 'Unity compilation log contains compiler errors'
    }

    $editXml = Join-Path $outputRoot 'editmode.xml'
    $editLog = Join-Path $outputRoot 'editmode.log'
    $exitCode = Invoke-UnityEditor @('-batchmode', '-nographics', '-projectPath', $temporaryProjectName,
        '-runTests', '-testPlatform', 'EditMode', '-testResults', $editXml, '-logFile', $editLog)
    if ($exitCode -ne 0) { throw "Unity EditMode tests failed with exit code $exitCode" }

    $playXml = Join-Path $outputRoot 'playmode.xml'
    $playLog = Join-Path $outputRoot 'playmode.log'
    $exitCode = Invoke-UnityEditor @('-batchmode', '-projectPath', $temporaryProjectName,
        '-runTests', '-testPlatform', 'PlayMode', '-testResults', $playXml, '-logFile', $playLog)
    if ($exitCode -ne 0) { throw "Unity PlayMode tests failed with exit code $exitCode" }

    $results = foreach ($entry in @(
        @{ Name = 'EditMode'; Path = $editXml },
        @{ Name = 'PlayMode'; Path = $playXml }
    )) {
        if (-not (Test-Path -LiteralPath $entry.Path -PathType Leaf)) {
            throw "$($entry.Name) test result XML was not created"
        }
        [xml]$document = Get-Content -LiteralPath $entry.Path -Raw
        $run = $document.'test-run'
        $total = [int]$run.total
        $passed = [int]$run.passed
        $failed = [int]$run.failed
        $skipped = [int]$run.skipped
        $inconclusive = [int]$run.inconclusive
        if ($total -lt 1 -or $failed -ne 0 -or $skipped -ne 0 -or $inconclusive -ne 0) {
            throw "$($entry.Name) result is not clean: total=$total passed=$passed failed=$failed skipped=$skipped inconclusive=$inconclusive"
        }
        [pscustomobject]@{
            suite = $entry.Name
            total = $total
            passed = $passed
            failed = $failed
            skipped = $skipped
            inconclusive = $inconclusive
        }
    }
    $results | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $outputRoot 'summary.json') -Encoding utf8
    $results | Format-Table -AutoSize
}
finally {
    if ($locationPushed) { Pop-Location }
    $resolvedTarget = [System.IO.Path]::GetFullPath($temporaryProject)
    $safePrefix = $temporaryBase.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    $safeLeaf = Split-Path -Leaf $resolvedTarget
    if (-not $resolvedTarget.StartsWith($safePrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
        -not $safeLeaf.StartsWith('oceansense-unity-', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove unverified temporary path: $resolvedTarget"
    }
    if (Test-Path -LiteralPath $resolvedTarget) {
        # PackageCache may contain paths beyond PowerShell's legacy Remove-Item limit.
        $extendedTarget = '\\?\' + $resolvedTarget
        [System.IO.Directory]::Delete($extendedTarget, $true)
    }
}
