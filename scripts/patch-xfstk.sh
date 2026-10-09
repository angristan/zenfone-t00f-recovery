#!/bin/bash
# Patches for xfstk-dldr-solo (edison-fw/xFSTK) that make the FW->OS
# handoff succeed on a ZenFone 5. Apply inside the xFSTK source tree,
# before cmake.
#
# 1. The stock tool gives up reconnecting after ~25 s. The phone
#    re-enumerates ~45 s after the firmware stage completes, after its
#    first boot of the downloaded IFWI. Extend patience to 150 attempts.
# 2. Poll for the re-enumerated device every 250 ms instead of every 5 s,
#    so the OS download starts while the device is still waiting for it.

set -e
F="xfstk-sources/core/downloader-solo/xfstkdownloader.cpp"

grep -q "counter > 20" "$F" || { echo "pattern 1 not found in $F" >&2; exit 1; }
sed -i '' 's/counter > 20/counter > 150/' "$F"

# outer wait: sleep(5) -> sleep(1) (the non-Windows branch of the
# UpdateTarget loop); inner poll: sleep(1) -> usleep(250000)
sed -i '' 's/^                sleep(5);$/                sleep(1);/' "$F"
sed -i '' 's/^                sleep(1);$/                usleep(250000);/' "$F"

echo "patched: counter limit 150, poll interval 250ms"
echo "verify with: git diff if the tree is a checkout"
