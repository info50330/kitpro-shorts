#!/bin/bash
# Usage : finaliser.sh <video_sans_son.mp4> <sortie.mp4> [graine_musique]
# Ajoute la musique de fond originale (modeles/musique.py) à une vidéo rendue.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
IN="$1"; OUT="$2"; SEED="${3:-1}"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
python3 "$DIR/musique.py" /tmp/_musique.wav "$DUR" "$SEED" >/dev/null
ffmpeg -y -loglevel error -i "$IN" -i /tmp/_musique.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -shortest -movflags +faststart "$OUT.tmp.mp4"
mv "$OUT.tmp.mp4" "$OUT"
echo "ok $OUT"
