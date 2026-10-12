#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
JAR=${1:-"$ROOT/tools/KickAss.jar"}
if [ ! -f "$JAR" ]; then
    echo 'KickAss.jar non trovato. Scaricalo da https://theweb.dk/KickAssembler/' >&2
    echo 'Uso: sh build.sh /percorso/KickAss.jar' >&2
    exit 1
fi
java -jar "$JAR" "$ROOT/src/main.asm" -o "$ROOT/balloon64.prg" -symbolfile
