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

The original u4 must have CRC32 d06cfa42; the result is checked to be 86b3450d.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x86B3450D
U4_SIZE = 0x200000

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "zcxIDGBLTgy4rUgM6EpODLCtAAAAgICAAIBIDMRXCgwg35gAtAAAAAAA/wAQDv8N////////AAAA"
    "AP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////CwzwEpgAtAAAAAAA"
    "/wAQDv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////"
    "////Cwzwn5gAtAAAAAAAAQAwKv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//"
    "////////AAAAAP//////////Cwww01QAtAAAAAAAAQCkHzMy////////AwAwKiMiJST/////BQAg"
    "HP8F////////AAAAAP//////////AAAAAP//////////DAywHJgAtAAAAAAAAQAwKv8A////////"
    "AQEgHP8B////////AAAAAP//////////AAAAAP//////////AAAAAP//////////DAywZ1QAtAAA"
    "AAAAAQCkH/8+////////AwAwKv8w////////BQAgHP8A////////AAAAAP//////////AAAAAP//"
    "////////DAyguZgAtAAAAAAAAQAQDv84////////AwAwKv8a////////BQAwKv8A////////Aiow"
    "Kv8q////////AAAAAP//////////CgzA+ZgAtAABAAAAAQAFDP8A////////AAAAAP//////////"
    "AAAAAP//////////AAAAAP//////////AAAAAP//////////CwxwL5gAtAABAACAAQASDP8A////"
    "////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////CwxQS5gA"
    "tAABAAAAAQBQCv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAA"
    "AP//////////CwxQgJgAtwABAAAAAQAeD/8A////////AAAAAP//////////AAAAAP//////////"
    "AAAAAP//////////AAAAAP//////////CwyQaJgAtAABAAAAAQAmFv8A////////AAAAAP//////"
    "////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAEhUU0lQIE9SRUpUQ0kg"
    "AFMAAAAAAAAAAAAAAABwIACATlVGT0lGSUNMQUEgRE5JICBTT04AVAAAAAAAAHAgAIBGQUlGSUxU"
    "QURFVyBUSSxIRSBETlJPRVMARAAAcCAAgFlCICxST0EgVFVPSElSRVogRFlCAAAAAAAAAABwIACA"
    "QUNFViAuTEEgTElSSEdTVFQgIE9IVABFAAAAAHAgAIBST0dJTklMQUcgTUEgRU5BIERUSQBTAAAA"
    "AAAAcCAAgFNBT1NJQ1RBREVJIFROTEVFTFRDQVUATAAAAABwIACAUlBQT1JFWVRSIE1FSUEgTklX"
    "SFQAAAAAAAAAAHAgAIBIVElFIFJFUlBTQ0VJVEVWUiBHSVRIAFMAAAAAcCAAgE9IRExSRS5TAAAA"
    "AAAAAAAAAAAAAAAAAAAAAABwIACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAgAIAgICAg"
    "ICBBSEVWRiBOVSEhICEgICAgICAAAAAAIHAAEDAyNjIxLy8wMzIAAE1TS09ERUIgQ0FOTwAAAABP"
    "TiBUT0YgUkFTRUwAAAAABgxM/AYMcBAfgBAEBgyc0gYMcBAfgCQABgxE0AcM0HsfgDwBBgwEzxOL"
    "TtoTiwHQBgwIz6BgM8krQAkABgwMzwGIAo8fgEAACQwoCBB/AXEQfwfQCQwsCB1gaIgrQAkACQxI"
    "CAkACQAfgMABBwzIajJiKCId1CtEBwzMahCP827zbgkABwxAa1EMTFwfgMwCCQzAZQzTMGIM0ytD"
    "CQzEZSgiC4sJAAuLCQz0ZVEMTFwfgHADBwyEAQcM0HsfgLQDBgyoeg4MpAkfgDAKBgy0eg0MWPYf"
    "gLALBgzEeg4MJAsfgLwLBgzUeTbYBeY22ATmBgwgeijUEOYo1A/mBgw40A4MqA8fgMwLBwwIhwA3"
    "Ao0ANxrSBwwMh4NgRa8rQoNgBwx0hwkACQAfgPABBwyohUwBE2BMAXPTBwyshSDJCCArQxNgBwx4"
    "hwkACQAfgDACDgwkKwgM4PgfgHICDgxEKwgMAPwfgHgCDgxkKwgMwPwfgH4CDgyEKwgMIP8fgIQC"
    "AAAAAA==")),
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
