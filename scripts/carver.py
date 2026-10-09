#!/usr/bin/env python3
"""Carve media and document files from a raw disk image.

Scans for embedded file signatures, extracts complete files where the
format carries enough structure to find the end, and validates results.
"""
import mmap
import os
import re
import struct
import sys
import hashlib

MIN_SIZE = 2048          # ignore tiny fragments
MAX_STREAM = 512 * 1024 * 1024  # sanity cap per file


def carve_jpeg(buf, out_dir, stats):
    # JPEG: FFD8FF start, FFD9 end
    pos = 0
    while True:
        s = buf.find(b"\xff\xd8\xff", pos)
        if s < 0:
            break
        # require a valid SOI followed by a known APPn/JFIF/Exif or SOF marker
        if s + 4 > len(buf):
            break
        m = buf[s + 3]
        e = buf.find(b"\xff\xd9", s + 2)
        if e > 0 and e - s < MAX_STREAM:
            data = buf[s:e + 2]
            if len(data) >= MIN_SIZE and b"\xff\xc0" in data[:4096] or b"\xff\xc2" in data[:4096]:
                _save(out_dir, "jpg", data, stats)
                pos = e + 2
                continue
        pos = s + 3


def carve_png(buf, out_dir, stats):
    pos = 0
    while True:
        s = buf.find(b"\x89PNG\r\n\x1a\n", pos)
        if s < 0:
            break
        e = buf.find(b"IEND", s)
        if e > 0:
            data = buf[s:e + 8]
            if len(data) >= MIN_SIZE:
                _save(out_dir, "png", data, stats)
                pos = e + 8
                continue
        pos = s + 8


def carve_mp4(buf, out_dir, stats):
    # walk ISO base media atoms starting at an 'ftyp'
    pos = 0
    while True:
        s = buf.find(b"ftyp", pos)
        if s < 0:
            break
        start = s - 4
        if start < 0:
            pos = s + 4
            continue
        size = struct.unpack(">I", buf[start:start + 4])[0]
        if 16 <= size <= MAX_STREAM:
            end = start + size
            # walk sibling atoms until moov/mdat chain ends
            off = start
            ok = False
            while off + 8 < min(start + MAX_STREAM, len(buf)):
                sz = struct.unpack(">I", buf[off:off + 4])[0]
                typ = buf[off + 4:off + 8]
                if sz == 0 or sz == 1:
                    ok = False
                    break
                if sz < 8 or off + sz > len(buf):
                    ok = False
                    break
                off += sz
                if typ in (b"moov", b"mdat", b"free", b"uuid"):
                    ok = True
                if typ in (b"mdat", b"moov") and off - start > 65536:
                    ok = True
                if off - start >= MAX_STREAM:
                    break
            if ok and off - start >= MIN_SIZE and start + MAX_STREAM > off:
                data = buf[start:off]
                _save(out_dir, "mp4", data, stats)
                pos = off
                continue
        pos = s + 4


def carve_pdf(buf, out_dir, stats):
    pos = 0
    while True:
        s = buf.find(b"%PDF-", pos)
        if s < 0:
            break
        e = buf.find(b"%%EOF", s)
        if e > 0 and e - s < MAX_STREAM:
            data = buf[s:e + 5]
            if len(data) >= MIN_SIZE:
                _save(out_dir, "pdf", data, stats)
                pos = e + 5
                continue
        pos = s + 5


def carve_sqlite(buf, out_dir, stats):
    pos = 0
    while True:
        s = buf.find(b"SQLite format 3\x00", pos)
        if s < 0:
            break
        try:
            page_size = struct.unpack(">H", buf[s + 16:s + 18])[0]
            if page_size == 1:
                page_size = 65536
            pages = struct.unpack(">I", buf[s + 28:s + 32])[0]
            size = page_size * pages
            if 512 <= page_size <= 65536 and 1 <= pages < 10_000_000 and size <= MAX_STREAM:
                data = buf[s:s + size]
                if len(data) >= MIN_SIZE and len(data) == size:
                    _save(out_dir, "sqlite", data, stats)
                    pos = s + size
                    continue
        except Exception:
            pass
        pos = s + 16


def carve_amr(buf, out_dir, stats):
    pos = 0
    while True:
        s = buf.find(b"#!AMR", pos)
        if s < 0:
            break
        e = buf.find(b"#!AMR", s + 6)
        end = e if e > 0 else min(s + 1024 * 1024, len(buf))
        data = buf[s:end]
        if len(data) >= MIN_SIZE:
            _save(out_dir, "amr", data, stats)
        pos = s + 6
        if e > 0:
            pos = e


def carve_gif(buf, out_dir, stats):
    pos = 0
    while True:
        s = buf.find(b"GIF8", pos)
        if s < 0:
            break
        e = buf.find(b"\x3b", s + 100)
        if e > 0 and e - s < 50 * 1024 * 1024:
            data = buf[s:e + 1]
            if len(data) >= MIN_SIZE:
                _save(out_dir, "gif", data, stats)
                pos = e + 1
                continue
        pos = s + 4


CARVERS = [
    ("jpeg", carve_jpeg), ("png", carve_png), ("mp4", carve_mp4),
    ("pdf", carve_pdf), ("sqlite", carve_sqlite), ("amr", carve_amr),
    ("gif", carve_gif),
]


def _save(out_dir, ext, data, stats):
    h = hashlib.md5(data).hexdigest()[:16]
    path = os.path.join(out_dir, f"{ext}_{h}.{ext}")
    if os.path.exists(path):
        stats[ext] = stats.get(ext, 0)  # dedup
        return
    with open(path, "wb") as f:
        f.write(data)
    stats[ext] = stats.get(ext, 0) + 1


def main():
    src, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    stats = {}
    with open(src, "rb") as f:
        buf = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    total = len(buf)
    print(f"scanning {total/1e9:.1f} GB...")
    for name, fn in CARVERS:
        print(f"carving {name}...", flush=True)
        fn(buf, out_dir, stats)
    buf.close()
    print("done:", stats)


if __name__ == "__main__":
    main()
