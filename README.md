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
   (`block/partitions/efi.c` in
   [Zenfone-Dev/android_kernel_asus_T00F](https://github.com/Zenfone-Dev/android_kernel_asus_T00F))
   refuses to even read the GPT unless the boot cmdline contains `gpt` (sets
   `force_gpt`). The stock boot chain supplies
   this; the replacement droidboot we flash does not. Without it the kernel
   reports `unknown partition table`, init falls back to a tmpfs `/data`,
   and nothing mounts. Appending ` gpt` to the boot image's cmdline fixes
   the whole chain.

3. **The stock boot image can be patched in place.** The boot image format
   (`$OS$` header, parsed by `unpack_intel`/`pack_intel` from
   [shakalaca's ZenFone-boot-tools](https://github.com/shakalaca/ZenFone-boot-tools))
   carries the kernel, a gzip cpio ramdisk,
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

## Credits and sources

- Intel xFSTK Downloader — [edison-fw/xFSTK](https://github.com/edison-fw/xFSTK) (patches to Intel's [SourceForge release](https://sourceforge.net/projects/xfstk/))
- Debrick guides and the loader package — [Hard Bricked Zenfone Unbrick](https://xdaforums.com/t/hard-bricked-zenfone-unbrick-last-method-to-try.3131911/) (rishav754), [Debrick Asus Zenfone 5 with no fastboot, no recovery](https://xdaforums.com/t/debrick-asus-zenfoen-5-with-no-fastboot-no-recovery-and-ruined-partitions.3377455/) (a8962383), [MediaFire debrick folder](https://www.mediafire.com/folder/7qapfy4zqvxf6) ([SourceForge mirror](https://sourceforge.net/projects/unbrick-asus-zenfone-5/))
- RAW firmware and soft-fuse extraction — [How to unbrick Asus Zenfone 5 stuck on Intel logo](https://andrewbenedictus.wordpress.com/2016/02/15/how-to-unbrick-asus-zenfone-5-stuck-on-intel-logo/) (Andrew Benedictus)
- Unlock/root files — [sigo/asus-zenfone-5-root](https://github.com/sigo/asus-zenfone-5-root)
- Boot image tools — [shakalaca/ZenFone-boot-tools](https://github.com/shakalaca/ZenFone-boot-tools)
- TWRP for T00F — [TWRP 3.x for A500CG/A600CG](https://xdaforums.com/t/recovery-unofficial-twrp-3-0-2-0-asus-zenfone-5-a500cg-a600cg.3355749/) (X AnwarMov), [TWRP 3.1.1](https://xdaforums.com/t/recovery-unofficial-twrp-3-1-1-0-asus-zenfone-5.3657781/) (hungximbexx)
- Platform source — [Zenfone-Dev](https://github.com/Zenfone-Dev) org, in particular [android_kernel_asus_T00F](https://github.com/Zenfone-Dev/android_kernel_asus_T00F)
