# Diagnosing a locked ZenFone 5 with a dead bootloader

## The device

ASUS ZenFone 5 A500CG (codenames `T00F` for the 3G model, `T00J` for the LTE
variant). Intel Atom Z2520, Cloverview+ platform, kernel cmdline identifies
as `androidboot.hardware=redhookbay`. Android 4.4–5.0 stock, unofficial
CyanogenMod/LineageOS builds after that.

## Boot chain

```
IFWI (pre-boot firmware, written to dnx/ifwi partitions)
  └─ OSIP image list, stored inside a 128 MiB "reserved" GPT partition
       └─ fastboot partition (droidboot, the Intel bootloader)
            └─ boot partition (kernel + ramdisk + cmdline)
                 └─ Android
```

Two things are unusual:

- `fastboot`, `recovery` and `boot` are **OSIP images inside the `reserved`
  partition**, not GPT partitions of their own. `fastboot flash boot` works
  because droidboot knows the OSIP names.
- LBA0 of the eMMC contains the OSIP header, not a valid protective MBR.
  The GPT (header at LBA1, entries from LBA2) is valid and CRC-correct, but
  stock Linux will not parse it without the `gpt` kernel cmdline flag. See
  `boot-image.md` for the consequences.

## Symptoms and what they mean

| Symptom | Meaning |
|---|---|
| Phone boots Android, lockscreen password forgotten | data intact, access blocked by adbd authorization (the RSA dialog can only be accepted from an unlocked screen on Android 6+) |
| `adb devices` shows `unauthorized` | same as above; the dialog cannot be accepted |
| `Vol Up + Power` shows a battery icon with `?`, never reaches a menu | the `fastboot` (droidboot) partition is corrupted; the boot attempt fails and the phone drops to the charging screen |
| Selecting Recovery mode in droidboot reboots back to droidboot | droidboot boots the recovery OSIP image; a broken one fails silently |
| Battery icon with `?` while powered off | the bootloader could not read battery state; on this model it also appears when a boot attempt fails |

## Confirming the diagnosis from a Mac

```sh
# 1. Is the phone seen at all while it boots Android?
ioreg -p IOUSB -w 0 | grep -i ASUS_T00F

# 2. Does Vol Up + Power ever enumerate anything?
watch ioreg for a fastboot-class USB device after the ASUS logo;
a phone that falls back to the battery screen enumerates nothing.

# 3. Is the pre-boot firmware alive? Enter Cloverview mode:
#    power off fully, hold Vol Down, plug USB (no power button).
ioreg -p IOUSB -w 0 | grep -i CLOVERVIEW
# expected: CLOVERVIEW@...  (Intel 0x8086:0x09EE)
```

If step 3 shows `CLOVERVIEW`, the IFWI and the pre-boot download mode are
healthy and the repair in `repair.md` will work. If not, the phone is in a
deeper state than this repo covers (see the XDA "Hard Bricked Zenfone
Unbrick" thread for the xFSTK + iSocUSB Windows route).

## Why not just use TWRP?

TWRP for this phone exists and flashes fine once fastboot is repaired. But
the TWRP kernel has unreliable eMMC reads for large blocks at high offsets
(see `data-recovery.md`), so it is a stepping stone here, not the recovery
environment. The final data pull happens from the running ROM.
