# Repairing the boot chain

This repairs the broken `fastboot` partition and ends with the phone
booting LineageOS with root adb. It assumes the diagnosis in `diagnosis.md`
confirmed Cloverview mode works.

Everything below runs on macOS. Total time: about an hour, most of it
transfers.

## 0. Tools

```sh
brew install adb-platform-tools  # or: brew install --cask android-platform-tools
brew install cmake boost libusb libusb-compat qt@5 doxygen
```

Build Intel's xFSTK downloader:

```sh
git clone https://github.com/edison-fw/xFSTK.git
cd xFSTK && mkdir build && cd build
BUILD_VERSION=1.8.6 DISTRIBUTION_NAME=ubuntu20.04 \
  cmake '-DCMAKE_PREFIX_PATH=/opt/homebrew/opt/qt@5;/opt/homebrew' \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  -DBoost_INCLUDE_DIR=/opt/homebrew/include \
  -DBoost_LIBRARY_DIRS=/opt/homebrew/lib ..
CPLUS_INCLUDE_PATH=/opt/homebrew/include \
LIBRARY_PATH=/opt/homebrew/lib make -j8 xfstk-dldr-solo
# binary: ancillary/configure/core/downloader-solo/xfstk-dldr-solo
```

Only `xfstk-dldr-solo` is needed; the GUI targets fail to link and can be
ignored. Apply `scripts/patch-xfstk.sh` before building — it extends the
reconnect patience and speeds up the reconnect poll, without which the
FW→OS handoff fails on every attempt (the phone re-enumerates ~45 s after
the firmware stage; stock xfstk gives up after ~25 s).

Get the loader files (see `files/MANIFEST.md` for checksums and sources):

| xfstk argument | file | what it is |
|---|---|---|
| `--fwdnx` | `dnx.bin` | firmware DnX loader |
| `--fwimage` | `ifwi.bin` | IFWI image (RAM only) |
| `--osdnx` | `dnx_osr.bin` | OS DnX loader |
| `--osimage` | `fastboot-2.19.img.pos.bin` | temporary droidboot pushed to RAM |
| `--softfuse` | `soft_fuse.bin` | soft fuses, from ASUS RAW firmware |

## 1. Push a temporary droidboot into RAM

Enter Cloverview mode: phone fully off, hold `Vol Down`, plug USB, keep
holding ~10 s. The screen stays off; the Mac sees `CLOVERVIEW` on the bus.

```sh
xfstk-dldr-solo -v \
  --fwdnx dnx.bin --fwimage ifwi.bin \
  --osdnx dnx_osr.bin --osimage fastboot-2.19.img.pos.bin \
  --softfuse soft_fuse.bin \
  --gpflags 0x80000001
```

Expected log: `Soft fusing is in progress ...` then
`Firmware download completed. Continuing to OS...`, a reconnect burst
(~45 s), `POS download is in progress ...` and finally
`Firmware and OS download completed.`

Failure modes seen in practice:

- `Softfuses Binary absent. Please provide binary.` — the device requested
  soft fuses (`RSUPHS` ack). The soft-fuse payload must come from the RAW
  firmware **of the same SKU** (T00F). A soft fuse from the wrong image
  fails with a signature error. The 880-byte `soft_fuse.bin` can be
  extracted from [ASUS's RAW firmware zip](https://www.mediafire.com/file/b8fpeu26puk6l1d/Zenfone+5+_1.17.40.16_20140811_0963-user-fastboot-user.raw/file)
  with HTTP range requests into the
  zip's central directory, without downloading the 800 MB file
  (see [Andrew Benedictus' guide](https://andrewbenedictus.wordpress.com/2016/02/15/how-to-unbrick-asus-zenfone-5-stuck-on-intel-logo/)).
- Reconnect never succeeds — apply `scripts/patch-xfstk.sh` and retry.
- Tool exits, phone shows `Intel Inside` then dies: the OS image signature
  check failed; use the exact `fastboot-2.19.img.pos.bin` from the debrick
  package, not a repacked droidboot.

When it succeeds the screen shows the droidboot menu (Android with a
yellow helmet) and `fastboot devices` lists the phone with serial
`0123456789ABCDEF` (RAM-boot placeholder serial).

## 2. Repair the fastboot partition permanently

From the temporary fastboot:

```sh
fastboot flash fastboot files/root/fastboot.img   # unlocked droidboot, WW 2.22.40.54
fastboot reboot-bootloader
```

The permanent droidboot comes from [sigo's `asus-zenfone-5-root`](https://github.com/sigo/asus-zenfone-5-root)
repo (see manifest). After the reboot `fastboot devices` shows the real serial.

## 3. Unlock the bootloader

The bootloader lock state lives in the IFWI, not in the fastboot image.
With the phone unlocked in 2016 but the *vanilla* (locked) IFWI restored by
later rooting flows, `fastboot flash recovery` fails with
`not allowed to update unsigned image on secure device`. The documented
unlock sequence from sigo's `root.sh`:

```sh
fastboot flash dnx   files/vanilla/dnx_fwr_ctp_a500cg.bin
fastboot flash ifwi  files/root/ifwi_ctp_a500cg.bin
fastboot reboot-bootloader   # wait up to 3 minutes
```

After this, unsigned images (TWRP) flash normally. This is the riskiest
step of the repair: wrong-SKU images here can hard-brick the phone.

## 4. Flash TWRP

```sh
fastboot flash recovery files/twrp/recovery.img   # TWRP 3.0.M5 for T00F
fastboot reboot recovery   # or select RECOVERY MODE in the droidboot menu
```

TWRP's adb runs as root without authorization, but see `data-recovery.md`
for why not to trust its eMMC reads. Reboot to droidboot when done.

The TWRP build for T00F is unofficial — [X AnwarMov's XDA thread](https://xdaforums.com/t/recovery-unofficial-twrp-3-0-2-0-asus-zenfone-5-a500cg-a600cg.3355749/)
for sources and updates.

## 5. Patch the boot image

Follow `boot-image.md`: unpack the current boot image, patch the ramdisk's
`default.prop` (`ro.secure=0`, `ro.adb.secure=0`,
`persist.sys.usb.config=mtp,adb`), append ` gpt` to the cmdline, repack,
flash:

```sh
fastboot flash boot patched_boot.img
fastboot reboot
```

The phone boots the ROM with root adb and no authorization prompt. The
lockscreen password never comes into play again.
