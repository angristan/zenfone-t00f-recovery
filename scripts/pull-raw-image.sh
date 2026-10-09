#!/bin/bash
# Stream a raw partition or disk image over adb exec-out with md5 spot
# checks. Works from the running ROM (reliable stack). For TWRP use the
# chunked variant instead - see pull-data-verified-chunks.sh notes.
#
# usage: pull-raw-image.sh <device|partition> <out.img>
set -e
DEV="$1"; OUT="$2"
SIZE=$(adb shell "blockdev --getsize64 $DEV" | tr -d '\r')
echo "pulling $DEV ($SIZE bytes)"
adb exec-out "dd if=$DEV bs=1048576 2>/dev/null" > "$OUT"
GOT=$(stat -f %z "$OUT")
[ "$GOT" = "$SIZE" ] || { echo "size mismatch: $GOT != $SIZE" >&2; exit 1; }
# spot-verify two 10 MB windows against phone-side md5
for OFF in 1000 8000; do
  P=$(adb shell "dd if=$DEV bs=1048576 skip=$OFF count=10 2>/dev/null | md5sum" | awk '{print $1}')
  L=$(dd if="$OUT" bs=1048576 skip=$OFF count=10 2>/dev/null | md5 -q)
  [ "$P" = "$L" ] && echo "offset ${OFF}MiB: md5 match" || { echo "md5 mismatch at ${OFF}MiB" >&2; exit 1; }
done
echo "OK: $OUT"
