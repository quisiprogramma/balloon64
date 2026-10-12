param([string]$KickAssJar = "$PSScriptRoot/tools/KickAss.jar")
$ErrorActionPreference = 'Stop'
if (!(Test-Path -LiteralPath $KickAssJar)) {
    throw 'Scarica Kick Assembler da https://theweb.dk/KickAssembler/ e copia KickAss.jar nella cartella tools, oppure passa -KickAssJar con il percorso del JAR.'
}
& java -jar $KickAssJar "$PSScriptRoot/src/main.asm" -o "$PSScriptRoot/balloon64.prg" -symbolfile
if ($LASTEXITCODE -ne 0) { throw 'Compilazione fallita' }
