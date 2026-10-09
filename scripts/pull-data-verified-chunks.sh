#!/bin/bash
# Verified chunked transfer for unreliable read stacks (TWRP on this
# phone): pull N sectors into phone-side tmpfs with bs=512, adb pull the
# chunk, md5-verify both sides, append, repeat. Slow (~80 MB/min) - only
# use when the running ROM is not available.
# Verified chunked transfer of ZenFone data partition via tmpfs + adb pull
cd "$(dirname "$0")/.."   # workspace root; chunks land in ./data.img
START=4599016
TOTAL=26157848
CHUNK=409600   # 200 MiB in sectors
N=$(( (TOTAL + CHUNK - 1) / CHUNK ))
LOG=transfer.log
: > $LOG
echo "total sectors $TOTAL, chunks $N" >> $LOG
prev=""; fail=0
for ((i=0; i<N; i++)); do
  skip=$((START + i*CHUNK))
  count=$CHUNK
  [ $((i*CHUNK + CHUNK)) -gt $TOTAL ] && count=$((TOTAL - i*CHUNK))
  cur=/tmp/c_$i.img
  # read chunk (foreground; pipelined pull of previous below)
  adb shell "dd if=/dev/block/mmcblk0 bs=512 skip=$skip count=$count 2>/dev/null > $cur && md5sum $cur" > m_ph_$i
  [ -s m_ph_$i ] || { echo "chunk $i dd FAILED" >> $LOG; exit 1; }
  # pull and verify
  ok=0
  for try in 1 2 3; do
    adb pull $cur chunk_$i > /dev/null 2>&1
    mloc=$(md5 -q chunk_$i)
    mph=$(awk '{print $1}' m_ph_$i)
    if [ "$mloc" = "$mph" ]; then ok=1; break; fi
    echo "chunk $i md5 mismatch try $try (phone $mph local $mloc)" >> $LOG
  done
  if [ $ok -eq 1 ]; then
    cat chunk_$i >> data.img; rm -f chunk_$i m_ph_$i
    echo "chunk $i OK ($count sectors) total=$(stat -f %z data.img)" >> $LOG
  else
    fail=$((fail+1)); rm -f chunk_$i; mv m_ph_$i bad_m_ph_$i
    echo "chunk $i FAILED after retries - saved marker, continuing" >> $LOG
  fi
  adb shell "rm -f $cur"
done
echo "DONE. failed chunks: $fail" >> $LOG
