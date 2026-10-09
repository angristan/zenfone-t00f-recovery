# File manifest

Every binary used in the repair, with checksums and public sources. All of
these are ASUS/Intel firmware images that already circulate publicly;
they are redistributed here so the repair is reproducible offline. If you
publish this repository, consider keeping only this manifest and dropping
the binaries.

| file | md5 | size (bytes) | source |
|---|---|---|---|
| `files/debrick/dnx.bin` | `d149857177c9fa7b5db4b5ec5959824e` | 99296 | MediaFire folder [7qapfy4zqvxf6 / ZenFone5](https://www.mediafire.com/folder/kwch443xdu3ja/ZenFone5), from XDA thread [Hard Bricked Zenfone Unbrick](https://xdaforums.com/t/hard-bricked-zenfone-unbrick-last-method-to-try.3131911/) (rishav754); [SourceForge mirror](https://sourceforge.net/projects/unbrick-asus-zenfone-5/) — [direct](https://www.mediafire.com/file/eqvyy2q2x7wfdkz/dnx.bin/file) |
| `files/debrick/dnx_osr.bin` | `2611c9aa06ac97772ca4478a25a73b1f` | 99296 | [same package](https://www.mediafire.com/folder/kwch443xdu3ja/ZenFone5) — [direct](https://www.mediafire.com/file/le4klu095ws4dxx/dnx_osr.bin/file) |
| `files/debrick/fastboot-2.19.img.pos.bin` | `069796162be55551387757863b1cdb3d` | 13587456 | [same package](https://www.mediafire.com/folder/kwch443xdu3ja/ZenFone5) — [direct](https://www.mediafire.com/file/6idwhvrzfhmrmz3/fastboot-2.19.img.pos.bin/file) |
| `files/debrick/ifwi.bin` | `bd0634d0781d2579a95c48e2c4359b2d` | 2031600 | [same package](https://www.mediafire.com/folder/kwch443xdu3ja/ZenFone5) — [direct](https://www.mediafire.com/file/za84hj4lk4q27ub/ifwi.bin/file) |
| `files/debrick/partition.tbl` | `ae4148ec80d68315b75c5cf361e0cf60` | 1267 | [same package](https://www.mediafire.com/folder/kwch443xdu3ja/ZenFone5) — [direct](https://www.mediafire.com/file/52l3u1obg4gqgdj/partition.tbl/file) |
| `files/raw-jb/boot_sign.bin` | `0d482fe2637fd5aaf0039fadaf7cd46b` | 9414144 | stock boot image from the same RAW firmware; used as the `$OS$` header template when repacking — [same zip](https://www.mediafire.com/file/b8fpeu26puk6l1d/Zenfone+5+_1.17.40.16_20140811_0963-user-fastboot-user.raw/file), entry `boot_sign.bin` |
| `files/raw-jb/soft_fuse.bin` | `9057a7ebfe9702870b8301ebeca7e654` | 880 | extracted from ASUS RAW firmware zip ["Zenfone 5 _1.17.40.16_20140811_0963-user-fastboot-user.raw"](https://www.mediafire.com/file/b8fpeu26puk6l1d/Zenfone+5+_1.17.40.16_20140811_0963-user-fastboot-user.raw/file) (MediaFire, via [Andrew Benedictus' debrick guide](https://andrewbenedictus.wordpress.com/2016/02/15/how-to-unbrick-asus-zenfone-5-stuck-on-intel-logo/)); the zip can be read with HTTP range requests to avoid the 800 MB download |
| `files/root/fastboot.img` | `0292b1021091fe09826d59fe142d47ad` | 13804544 | unlocked droidboot, from [sigo/asus-zenfone-5-root](https://github.com/sigo/asus-zenfone-5-root) ([`files/root`](https://github.com/sigo/asus-zenfone-5-root/tree/master/files/root)), extracted from official WW 2.22.40.54 firmware |
| `files/root/ifwi_ctp_a500cg.bin` | `e2f67a8c00ab3863f6663fe5ab943d18` | 2031600 | unlocked IFWI, same repo ([`files/root`](https://github.com/sigo/asus-zenfone-5-root/tree/master/files/root)) |
| `files/twrp/recovery.img` | `2961f43ca90076fec6267e7591f2d359` | 12540416 | TWRP 3.0.M5 for T00F, extracted from [TWRP-3.0-M-5.0-20160725-T00F.zip](https://www.mediafire.com/file/oho3s32vlopkc7e/TWRP-3.0-M-5.0-20160725-T00F.zip) (XDA threads: [TWRP 3.x by X AnwarMov](https://xdaforums.com/t/recovery-unofficial-twrp-3-0-2-0-asus-zenfone-5-a500cg-a600cg.3355749/), [noobinvoker guide](https://noobinvoker.blogspot.com/2017/03/install-twrp-custom-recovery-305-0-on.html)) |
| `files/vanilla/dnx_fwr_ctp_a500cg.bin` | `d149857177c9fa7b5db4b5ec5959824e` | 99296 | vanilla DnX, same repo ([`files/vanilla`](https://github.com/sigo/asus-zenfone-5-root/tree/master/files/vanilla)); byte-identical to `sec-dnx_fwr.bin` in the ASUS RAW firmware |
