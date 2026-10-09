# Boot image format and patching

The boot image format is documented by the source of
[`ZenFone-boot-tools`](https://github.com/shakalaca/ZenFone-boot-tools)
(shakalaca; `pack_intel`/`unpack_intel`), not by any
official spec. This note records what the tools do and the on-disk layout
as observed on a T00F, plus the two patches needed for root adb.

## File format ($OS$)

```c
struct bootheader {          // from bootheader.h, abridged
    uint8  magic[7];         // "$OS$" + 00 00 01
    uint8  xor;              // XOR of bytes 0-6 and 8-55
    uint8  id[0x28];         // image identity; includes type bytes
    uint32 sectors;          // total image size / 512 - 1
    uint32 imageType;
    uint8  head_padding[0x1c8];   // 0xFF
    uint8  unknown[0x1e0];
    char   cmdline[0x400];
    uint32 bzImageSize;       // at file offset 0x7E0
    uint32 initrdSize;        // at file offset 0x7E4
    // ... padding, bootstub stack (0x1000)
};                           // bzImage follows, then gzip cpio ramdisk
```

`unpack_intel image out_bzImage out_ramdisk` splits the image at those
boundaries; `pack_intel template_image bzImage ramdisk out_image` rebuilds
one, copying the header (identity, cmdline) from the template and
recomputing sizes and the XOR byte.

## On-disk layout

When droidboot flashes a `$OS$` file to an OSIP slot (fastboot, recovery,
boot), it stores the file **minus its first 0x400 bytes** at a byte offset
inside the 128 MiB `reserved` GPT partition. Consequences:

- No `$OS$` magic exists on disk; scanning for it finds nothing.
- The sizes land at disk offset `0x3E0`/`0x3E4` from the image start.
- Each image's internal kernel offset is packer-specific. The stock ASUS
  packer and the CM/LineageOS packer produce different headers. **Do not
  assume the file-format kernel offset (0x33E0 for the fastboot image)
  applies to a different image.**

The safest way to read an image off the phone is therefore not to parse it
on disk, but to work from a raw region dump and the known-good file pairs.

## Extracting the current boot image from a region dump

The reserved partition is at low disk offsets (LBA 0x28-0x40027), where
eMMC reads are reliable in any block size. Images live at roughly 32 000
sector intervals. Identify them by scanning for the `HdrS` bzImage magic
(`0x53726448`, at bzImage offset 0x202) and by the gzip cpio ramdisk that
follows the kernel. The RAM-boot CM image contains `ro.cm.version` in its
decompressed ramdisk; stock ASUS images carry `ro.build.fingerprint`
strings instead.

To rebuild a flashable file from the on-disk bytes:

1. Build a 0x400-byte header from a known-good stock boot image of the
   same SKU (e.g. `boot_sign.bin` from the [1.17.40.16 RAW firmware](https://www.mediafire.com/file/b8fpeu26puk6l1d/Zenfone+5+_1.17.40.16_20140811_0963-user-fastboot-user.raw/file)).
2. Keep bytes `0x08-0x2F` (identity) untouched — writing anything else
   there makes droidboot reject the flash with `flash_cmds error`.
3. Set `sectors` at offset `0x30` to `filesize/512 - 1`.
4. The 0x28 bytes at file offset `0x3D8` are the head of the cmdline; the
   command string continues on disk at image start. Feed the on-disk bytes
   from image start minus 0x28.
5. Append the original on-disk content. The size fields inside it stay
   valid.
6. Recompute the XOR byte over `0-6` and `8-55`.

## Patch 1: root adb (ramdisk)

Decompress the gzip cpio ramdisk, rewrite `default.prop`:

```diff
-ro.adb.secure=1
+ro.adb.secure=0
-ro.secure=1
+ro.secure=0
-persist.sys.usb.config=none
+persist.sys.usb.config=mtp,adb
```

Rebuild the cpio (newc format, keep modes/owners, `TRAILER!!!` and any
trailing bytes intact), gzip it, and splice it over the old ramdisk in the
image. If the new gzip is larger than the original, the image cannot be
patched in place — recompress at a higher level (level 9 fit in 13 KB less
than the original here). Pad to the original size with NULs; the kernel's
gunzip stops at the end of the stream.

With these properties adbd runs as root from boot and skips the RSA
authorization entirely.

## Patch 2: the `gpt` kernel cmdline flag

Linux 3.10 `block/partitions/efi.c`:

```c
if (!force_gpt) {
        good_pmbr = is_pmbr_valid(legacymbr);
        if (!good_pmbr)
                goto fail;          /* GPT is never even read */
}
```

`force_gpt` is set by the `gpt` kernel cmdline parameter
(`__setup("gpt", force_gpt_fn)`). On this phone LBA0 holds the OSIP header
(no 0xEE protective MBR entry), so without the flag the kernel reports
`unknown partition table`, no `mmcblk0pN` devices appear, and init falls
back to a tmpfs `/data` — the ROM boots to a dead half-state with only
adbd alive. The stock IFWI/droidboot chain supplies the flag when loading
the boot image; a replacement droidboot does not.

Fix: append ` gpt` to the boot image's cmdline string (the field is
0x400 bytes and mostly NUL padding, so the string's end has room). The
kernel then parses the valid GPT, partitions appear as
`mmcblk0p1`-`p10`, `/dev/block/by-name/*` resolves, and `/system` and
`/data` mount normally.

This flag is the single most obscure failure in the whole repair: the
phone "boots" and adbd answers, but every mount fails with the rootfs
still read-only and `/system/bin/sh` missing. Check `adb pull
/proc/partitions` first — if the list ends at `mmcblk0rpmb`, this is it.
