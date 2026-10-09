# ZenFone 5 (T00F/A500CG) data recovery

Tools and notes for recovering data from an ASUS ZenFone 5 A500CG (Intel
Cloverview+ platform, codename `redhookbay`) when:

- the lockscreen password is forgotten,
- the `fastboot` (droidboot) partition is corrupted, so `Vol Up + Power`
  never reaches fastboot,
- the phone otherwise boots Android normally.

The method never unlocks the screen. It repairs the boot chain from below,
boots with a patched ramdisk that disables adbd's authorization requirement,
and pulls the data with root adb. It was written for macOS; the same steps
work on Linux with less friction (no Cloverview driver issues there either
way, since libusb talks to the phone directly).

## How it fits together

```
repair flow                      doc
---------------------------      -------------------------
identify what is broken          docs/diagnosis.md
push a temporary bootloader      docs/repair.md
  over USB (Cloverview mode)
repair the fastboot partition,   docs/repair.md
unlock, flash TWRP
patch the boot image             docs/boot-image.md
  (gpt cmdline flag + root adbd)
pull and carve user data         docs/data-recovery.md
```

## The three findings that made it work

1. **Cloverview mode survives a broken droidboot.** Holding `Vol Down` while
   plugging USB from power-off makes the pre-boot firmware enumerate as
   Intel `0x8086:0x09EE` ("CLOVERVIEW"). Intel's xFSTK tool can then push a
   droidboot image into RAM over USB. No Windows needed: `xfstk-dldr-solo`
   builds on macOS.

2. **The kernel needs the `gpt` cmdline flag.** On this platform the eMMC's
   LBA0 holds Intel OSIP data, not a protective MBR. Linux 3.10's GPT parser
   (`block/partitions/efi.c`) refuses to even read the GPT unless the boot
   cmdline contains `gpt` (sets `force_gpt`). The stock boot chain supplies
   this; the replacement droidboot we flash does not. Without it the kernel
   reports `unknown partition table`, init falls back to a tmpfs `/data`,
   and nothing mounts. Appending ` gpt` to the boot image's cmdline fixes
   the whole chain.

3. **The stock boot image can be patched in place.** The boot image format
   (`$OS$` header, parsed by `unpack_intel`/`pack_intel` from
   shakalaca's ZenFone-boot-tools) carries the kernel, a gzip cpio ramdisk,
   and the cmdline. Changing `ro.secure=0`, `ro.adb.secure=0` and
   `persist.sys.usb.config=mtp,adb` in the ramdisk's `default.prop` gives
   root adb on boot with no authorization prompt, so the lockscreen never
   matters again.

## Files

`files/` holds every firmware image used in the repair. `files/MANIFEST.md`
lists each file with its checksum and public source. The images are
redistributions of ASUS/Intel firmware that circulates on XDA and SourceForge;
if you publish this repo, consider dropping them from the tree and keeping
only the manifest.

## Safety notes

- The xFSTK download itself only writes RAM. Everything permanent happens
  through explicit `fastboot flash` commands afterwards.
- Flashing `dnx` and `ifwi` partitions is the riskiest step: a wrong image
  there can hard-brick the phone. Use files for the exact SKU (T00F, WW).
- `/data` is never written by any step in this repo.

## Credits

The repair flow is an adaptation of guides by rishav754, a8962383 (XDA
debrick threads) and sigo's `asus-zenfone-5-root` scripts, reworked so that
every step runs on macOS against a locked, half-bricked phone.
