# Pulling and carving user data

Once the ROM boots with the patched ramdisk (`boot-image.md`), the data is
one adb pull away. The parts worth documenting are the transfer paths
that work and the ones that silently corrupt, plus the carving pass for
data deleted before the last wipe.

## Transfer reliability, ranked

| Path | Trust |
|---|---|
| adb pull / adb push (sync protocol) from the running ROM | binary-safe, ~18 MB/s |
| `adb exec-out` streaming from the running ROM | binary-safe; verify with md5 spot checks anyway |
| adb pull through TWRP | binary-safe per file, but see below |
| TWRP `exec-out` streams, loop mounts, large-block eMMC reads | **corrupt** |

The TWRP 3.0.M5 kernel reads the eMMC unreliably for large blocks at high
offsets: `bs=4096` reads return data from the wrong location or zeros,
single `bs=512` reads are stable. This is invisible to md5 comparisons
done phone-side (the checksums match whatever garbage was read). Rules
learned the hard way:

- Verify every phone-side read against a second read at a different block
  size before trusting it.
- Prefer low offsets (the 128 MiB `reserved` partition read fine at any
  block size).
- For bulk data, do not bother with TWRP: repair the boot chain and pull
  from the running ROM.

## Pulling the live filesystem

```sh
adb pull /data/media/0/ recovered/sdcard/     # user files
adb shell "tar -czf /data/media/0/data.tar.gz -C /data data"
adb pull /data/media/0/data.tar.gz            # app data, with phone-side md5
adb pull /data/app/ recovered/app/            # installed APKs
```

## Raw disk image

For deleted data and for carving, image the whole eMMC (14.7 GB), not just
the data partition — partition layouts changed across firmware generations
and pre-reinstall data can sit anywhere:

```sh
adb shell "blockdev --getsize64 /dev/block/mmcblk0"   # expected size
adb exec-out "dd if=/dev/block/mmcblk0 bs=1048576" > full_disk.img
# spot-verify at a few offsets against phone-side reads
adb shell "dd if=/dev/block/mmcblk0 bs=1048576 skip=1000 count=10 | md5sum"
dd if=full_disk.img bs=1048576 skip=1000 count=10 | md5 -q
```

## Carving deleted files

`debugfs -R "lsdel"` on the ext4 image finds nothing on a phone that was
wiped (the wipe resets the inode tables). The deleted data blocks
themselves survive until overwritten, so signature carving over the raw
image is the only route. [PhotoRec](https://www.cgsecurity.org/wiki/PhotoRec)
7.2 refuses to run without a terminal
and its `/cmd` non-interactive mode aborts without writing files;
`scripts/carver.py` covers the common formats instead (JPEG, PNG, MP4
family via ISO atom walking, PDF, SQLite, AMR, GIF), deduplicates by md5,
and validates with Pillow afterwards:

```sh
python3 carver.py full_disk.img carved/
python3 - <<'EOF'    # keep only decodable images
import os
from PIL import Image
for f in os.listdir("carved"):
    try:
        Image.open(f"carved/{f}").load()
    except Exception:
        os.remove(f"carved/{f}")
EOF
```

Expect the majority of carved JPEGs to be truncated or misassociated
fragments; on the reference phone ~11 MB of fragments reduced to 91 valid
images. Filesystem timestamps survive in the image and are readable with
`debugfs -R "stats"` and `debugfs -R "ls -l <dir>"`, which is how the
phone's last-wipe date was established — directory mtimes change when
files are deleted from them.
