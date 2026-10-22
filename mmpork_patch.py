#!/usr/bin/env python3
"""
Muchi Muchi Pork (Cave CV1000) - patch build 15
Timer + boss health display, ARCADE / HARAHARA / MANPUKU / V1.01+ title menu,
V1.01+ mode (lard changes, three loops, extends in every loop), new warning screen.

Usage:
    python3 mmpork_patch.py mmpork.zip          -> writes u4 next to the zip
    python3 mmpork_patch.py u4                  -> writes u4_patched next to it
    python3 mmpork_patch.py mmpork.zip -o OUT   -> writes the patched u4 to OUT
    python3 mmpork_patch.py mmpork.zip --zip    -> also writes mmpork_patched.zip
                                                   (same set, u4 replaced)

The original u4 must have CRC32 d06cfa42; the result is checked to be 6b8efe38.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x6B8EFE38
U4_SIZE = 0x200000

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "BtRGYRghBolGZUZmEmJQMveL9q9iIQLQK0AJAB+AmAoGDNADAeAD0QIhA9ECIQPQK0AJAEgMrCRO"
    "DECsBgxwEBzREmMzZRzSIGADYgHIA4n/cxFDAIkA4yNgAsgEiQFzA+AHMwCLA+MyIQDiGdYzYAOI"
    "AYsB4hjWFdAiIADiIRAW0GIgFtBiIDA1AokM0AtAJeQK2gfREmABiASJAogFiQjQK0AJAAjQK0AJ"
    "AAfQK0AJAAkABAwk+EgMPB9IDPweCAzAjAYMHM8GDCDXBgxw1wQMKPgODLgnH4DkAAcMSIYHDBiI"
    "DgoADBYQBwcAUAAAAgECARLREmMVxwNlEdIS1wDkIOAwNACLPuB7IAIiIOB7IAESI2YIdgjhVGB7"
    "IAImEEH6jwR2iHIBdENgBIjoiwbSAeACIgISBBILAAYSCQAEDCT4SAzERDBgAIBODDCtUkFBQ0VE"
    "ICBBSEFSQUhBUkFNUE5LVSBVMVYwLisxICAI0AJgCCAAiQFxAXFo4AMxA4kRLATQK0AJAANhESwD"
    "0CtACQAEDCj4CQw0CAkMUAgc0iJiKCIMizJiKCIGixvUQGIoIgKLGtIrQgkAGdIrQgkAFdZiYACI"
    "CokBiA2JAOAZ0gIiGdIAIhnSACLurwkAAeACJjJlCqABdQLgAiYB4BHSAiIR0gAiEdIAIgDlCtT/"
    "4QjnCdZyJgnQC0BSJAnQK0AJAAQMKPgEDCz4UQxMXAcM2GoHDPBqSAwcIEgMmPUHDLABBwz6ak4M"
    "PKxIDH8iUQzcbwrTMmM4IwaLCtMwYigiCosJ0ytDCQAG0zJjAuIiMwKJB9MrQwkABdMrQwkABAwo"
    "+AQMLPhRDExcCQzIZQkM4GUJDORlD9ACYAggGIke4A4lGgFsMQhBDNIcMg/HA2ML1wjhNGB7IAIi"
    "EEH6jwRyU2AIQAwwBtIMMgHgCwACIgXQK0AJAAQMKPhIDFA6MGAAgE4MmKwHDNB7MVYwLisxICAA"
    "4ArRAiEiT0YvVi9mL3YvBdALQAkA9mf2ZvZl9mQmTwPQK0AJAAkAH4AYAwQMJPgGDHAQhi+WL6Yv"
    "ti8iT5XaAOAIGpHZYOu8O5JgCCAJiZFRj9iCYigiBIkQMimJSHj4rwkAZOAMMAw5EEvti4naqFAI"
    "IACLBBoA4Acao1AIIAGL2aAJAADgAxog4RNiE2MTZBNlgtaD1+WwCQAg4RNiE2MTZBNlgNaA19yw"
    "CQDDoAkAeNqkUIAwAYsB4AgagoUNYJ4Gn4QDYoOFnAODYQxxEYUNZVglDIkQYP+IAYkgMASLEYT/"
    "iAaJMDAEiQxx768JALevCQBn2hYahIUIIAqJZNpt0AJnpFCAMAGJhBp1GqVQc2YINlNhaDERQQOJ"
    "hIUIIJ+JAOFc0A4hGgEpQQlBE2SIsAkAA2eFsAkAA2aCsAkAA2JDYzDgOCMCiQwzAaAJACDjIOEQ"
    "MwGLKCICiQwyAaAJACDiDDYMNzNhY2Mu5HNlS9ZL13awCQBG2qZXBHeCYgDjAOFB1GDlXDVCYAgg"
    "F4lBUCAwFItPhANmc2mUYP+IDolgMPqLhYUNYAggAolCZggmBYkBcUTgTQARQACLDDNk4AwwDDQQ"
    "Rd+LGCEOi6ZQp1IAMgyJIOETYhNjE2QTZTHWMdc+sAkAIqAJAKZQBxozZCewCQADZiSwCQADZTDg"
    "SCQDiUNiDDIBoAkAIOJIJAGLWCUCiQw1AaAJACDlDDZTY2NkIOEg5R/WH9casAkAGNoB4AMaJk/2"
    "a/Zq9mn2aAsACQAV0UNiHiIaASlBCUEBQRNgCEAcMAwwQ2IIMhNkCwAjYBPQCyESJgsiIRYLIzIW"
    "CyRDFgslVBYB4AsAAifAAMgAtABEAAkASwycfB+AoAUEDAD4AACrqgAAzcxIDGBLTgy4rUgM6EpO"
    "DLCtAAAAgICAAIBIDMRXCgwg35gAtAAAAAAA/wAQDv8N////////AAAAAP//////////AAAAAP//"
    "////////AAAAAP//////////AAAAAP//////////CwzwEpgAtAAAAAAA/wAQDv8A////////AAAA"
    "AP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////Cwzwn5gAtAAAAAAA"
    "AQAwKv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////"
    "////Cwww01QAtAAAAAAAAQCkHzMy////////AwAwKiMiJST/////BQAgHP8F////////AAAAAP//"
    "////////AAAAAP//////////DAywHJgAtAAAAAAAAQAwKv8A////////AQEgHP8B////////AAAA"
    "AP//////////AAAAAP//////////AAAAAP//////////DAywZ1QAtAAAAAAAAQCkH/8+////////"
    "AwAwKv8w////////BQAgHP8A////////AAAAAP//////////AAAAAP//////////DAyguZgAtAAA"
    "AAAAAQAQDv84////////AwAwKv8a////////BQAwKv8A////////AiowKv8q////////AAAAAP//"
    "////////CgzA+ZgAtAABAAAAAQAFDP8A////////AAAAAP//////////AAAAAP//////////AAAA"
    "AP//////////AAAAAP//////////CwxwL5gAtAABAACAAQASDP8A////////AAAAAP//////////"
    "AAAAAP//////////AAAAAP//////////AAAAAP//////////CwxQS5gAtAABAAAAAQBQCv8A////"
    "////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////CwxQgJgA"
    "twABAAAAAQAeD/8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAA"
    "AP//////////CwyQaJgAtAABAAAAAQAmFv8A////////AAAAAP//////////AAAAAP//////////"
    "AAAAAP//////////AAAAAP//////////AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABw"
    "IACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAgAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAcCAAgFVNSEMgSVVNSEMgSU9QS1IgIU9SUFBLQQBVAABwIACAICAgICAgQUNFVk8gTlch"
    "UyEhICAgICAgAAAAACBwABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcCAAgAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAABwIACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAgAIAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcCAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AABwIACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAgAIAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAcCAAgDAyNjIxLy8wNDEAAE9SUFBLQQBVBgxM/AYMcBAfgOQCBgyc0gYMcBAfgCQA"
    "BgxE0AcM0HsfgPQABgwEzxOLTtoTiwHQBgwIz6BgM8krQAkABgwMzwGIAo8fgEAACQwoCBB/AXEQ"
    "fwfQCQwsCB1gaIgrQAkACQxICAkACQAfgHABBwzIajJiKCId1CtEBwzMahCP827zbgkABwxAa1EM"
    "TFwfgKABCQzAZQzTMGIM0ytDCQzEZSgiC4sJAAuLCQz0ZVEMTFwfgEQCBwyEAQcM0HsfgIgCBgyo"
    "eg4MpAkfgAQJBgy0eg0MWPYfgIQKBgzEeg4MJAsfgJAKBgzUeTbYBeY22AbmBgwgeijUEOYo1BHm"
    "AAAAAA=="
    )),
]


def find_u4(zf):
    for name in zf.namelist():
        if os.path.basename(name).lower() == "u4":
            return name
    return None


def apply_patch(data):
    if len(data) != U4_SIZE:
        raise ValueError("u4 is %d bytes, expected %d" % (len(data), U4_SIZE))
    crc = zlib.crc32(data) & 0xFFFFFFFF
    if crc == PATCHED_CRC:
        raise ValueError("this u4 is already patched (CRC %08x)" % crc)
    if crc != ORIG_CRC:
        raise ValueError("u4 CRC is %08x, expected the original %08x" % (crc, ORIG_CRC))
    out = bytearray(data)
    for off, blob in PATCHES:
        out[off:off + len(blob)] = blob
    out = bytes(out)
    crc = zlib.crc32(out) & 0xFFFFFFFF
    if crc != PATCHED_CRC:
        raise ValueError("patched CRC is %08x, expected %08x" % (crc, PATCHED_CRC))
    return out


def main():
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 (build 15)")
    ap.add_argument("input", help="mmpork.zip or a loose u4 file")
    ap.add_argument("-o", "--output", help="where to write the patched u4")
    ap.add_argument("--zip", action="store_true", help="also write mmpork_patched.zip (input must be a zip)")
    a = ap.parse_args()

    is_zip = zipfile.is_zipfile(a.input)
    if is_zip:
        with zipfile.ZipFile(a.input) as zf:
            name = find_u4(zf)
            if not name:
                sys.exit("error: no u4 inside %s" % a.input)
            data = zf.read(name)
    else:
        with open(a.input, "rb") as f:
            data = f.read()

    try:
        patched = apply_patch(data)
    except ValueError as e:
        sys.exit("error: %s" % e)

    folder = os.path.dirname(os.path.abspath(a.input))
    out = a.output or os.path.join(folder, "u4" if is_zip else os.path.basename(a.input) + "_patched")
    with open(out, "wb") as f:
        f.write(patched)
    print("original u4 CRC %08x OK" % ORIG_CRC)
    print("wrote %s (CRC %08x)" % (out, PATCHED_CRC))

    if a.zip:
        if not is_zip:
            sys.exit("error: --zip needs a zip as input")
        zout = os.path.join(folder, "mmpork_patched.zip")
        with zipfile.ZipFile(a.input) as zi, zipfile.ZipFile(zout, "w", zipfile.ZIP_DEFLATED) as zo:
            for info in zi.infolist():
                body = patched if info.filename == name else zi.read(info.filename)
                zo.writestr(info.filename, body)
        print("wrote %s" % zout)
    print("Back up your original u4 before flashing real hardware.")


if __name__ == "__main__":
    main()
