#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 40

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 13dc786f.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x13DC786F
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "E2MTZBNlgNaA19ywCQDDoAkAeNqkUIAwAYsB4AgagoUNYJ4Gn4QDYoOFnAODYQxxEYUNZVglDIkQ"
    "YP+IAYkgMASLEYT/iAaJMDAEiQxx768JALevCQBn2hYahIUIIAqJZNpt0AJnpFCAMAGJhBp1GqVQ"
    "c2YINlNhaDERQQOJhIUIIJ+JAOFc0A4hGgEpQQlBE2SIsAkAA2eFsAkAA2aCsAkAA2JDYzDgOCMC"
    "iQwzAaAJACDjIOEQMwGLKCICiQwyAaAJACDiDDYMNzNhY2Mu5HNlS9ZL13awCQBG2qZXBHeCYgDj"
    "AOFB1GDlXDVCYAggF4lBUCAwFItPhANmc2mUYP+IDolgMPqLhYUNYAggAolCZggmBYkBcUTgTQAR"
    "QACLDDNk4AwwDDQQRd+LGCEOi6ZQp1IAMgyJIOETYhNjE2QTZTHWMdc+sAkAIqAJAKZQBxozZCew"
    "CQADZiSwCQADZTDgSCQDiUNiDDIBoAkAIOJIJAGLWCUCiQw1AaAJACDlDDZTY2NkIOEg5R/WH9ca"
    "sAkAGNoB4AMaJk/2a/Zq9mn2aAsACQAV0UNiHiIaASlBCUEBQRNgCEAcMAwwQ2IIMhNkCwAjYBPQ"
    "CyESJgsiIRYLIzIWCyRDFgslVBYB4AsAAifAAMgAtABEAAkASwycfB+AeA8EDAD4AACrqgAAzcxI"
    "DGBLTgy4rUgM6EpODLCtAAAAgICAAIBIDMRXCgwg35gAtAAAAAAA/wAQDv8N////////AAAAAP//"
    "////////AAAAAP//////////AAAAAP//////////AAAAAP//////////CwzwEpgAtAAAAAAA/wAQ"
    "Dv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////"
    "Cwzwn5gAtAAAAAAAAQAwKv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////"
    "////AAAAAP//////////Cwww01QAtAAAAAAAAQCkHzMy////////AwAwKiMiJST/////BQAgHP8F"
    "////////AAAAAP//////////AAAAAP//////////DAywHJgAtAAAAAAAAQAwKv8A////////AQEg"
    "HP8B////////AAAAAP//////////AAAAAP//////////AAAAAP//////////DAywZ1QAtAAAAAAA"
    "AQCkH/8+////////AwAwKv8w////////BQAgHP8A////////AAAAAP//////////AAAAAP//////"
    "////DAyguZgAtAAAAAAAAQAQDv84////////AwAwKv8a////////BQAwKv8A////////AiowKv8q"
    "////////AAAAAP//////////CgzA+ZgAtAABAAAAAQAFDP8A////////AAAAAP//////////AAAA"
    "AP//////////AAAAAP//////////AAAAAP//////////CwxwL5gAtAABAACAAQASDP8A////////"
    "AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////CwxQS5gAtAAB"
    "AAAAAQBQCv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//"
    "////////CwxQgJgAtwABAAAAAQAeD/8A////////AAAAAP//////////AAAAAP//////////AAAA"
    "AP//////////AAAAAP//////////CwyQaJgAtAABAAAAAQAmFv8A////////AAAAAP//////////"
    "AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAEhUU0lQIE9SRUpUQ0kgAFMA"
    "AAAAAAAAAAAAAABwIACATlVGT0lGSUNMQUEgRE5JICBTT04AVAAAAAAAAHAgAIBGQUlGSUxUQURF"
    "VyBUSSxIRSBETlJPRVMARAAAcCAAgFlCICxST0EgVFVPSElSRVogRFlCAAAAAAAAAABwIACAQUNF"
    "ViAuTEEgTElSSEdTVFQgIE9IVABFAAAAAHAgAIBST0dJTklMQUcgTUEgRU5BIERUSQBTAAAAAAAA"
    "cCAAgFNBT1NJQ1RBREVJIFROTEVFTFRDQVUATAAAAABwIACAUlBQT1JFWVRSIE1FSUEgTklXSFQA"
    "AAAAAAAAAHAgAIBIVElFIFJFUlBTQ0VJVEVWUiBHSVRIAFMAAAAAcCAAgE9IRExSRS5TAAAAAAAA"
    "AAAAAAAAAAAAAAAAAABwIACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAgAIAgICAgICBB"
    "SEVWRiBOVSEhICEgICAgICAAAAAAIHAAEDAyNjIxLy8wMzIAAE1TS09ERUIgQ0FOTwAAAABPTiBU"
    "T0YgUkFTRUwAAAAABgxM/AYMcBAfgNgDBgyc0gYMcBAfgCQABgxE0AcM0HsfgCABBgwEzxOLTtoT"
    "iwHQBgwIz6BgM8krQAkABgwMzwGIAo8fgEAACQwoCBB/AXEQfwfQCQwsCB1gaIgrQAkACQxICAkA"
    "CQAfgKQBBwzIajJiKCId1CtEBwzMahCP827zbgkABwxAa1EMTFwfgHwCCQzAZQzTMGIM0ytDCQzE"
    "ZSgiC4sJAAuLCQz0ZVEMTFwfgCADBwyEAQcM0HsfgGQDBgyoeg4MpAkfgNwSBgy0eg0MWPYfgFwU"
    "BgzEeg4MJAsfgGgUBgzUeTbYBeY22ATmBgwgeijUEOYo1A/mBgw40A4MqA8fgHgUBwyohUwBE2BM"
    "AXPTBwyshSDJCCArQxNgBwx4hwkACQAfgNQBDgwkKwgM4PgfgCACDgxEKwgMAPwfgCYCDgxkKwgM"
    "wPwfgCwCDgyEKwgMIP8fgDICDgzEKwkMAAAfgPAGBwwAg3NgQMlzYCrQBwwEgwggSYkrQHNgBwys"
    "gwkACQAfgKQGBgyU+XJg/4i40CtABgyY+WuNAOoJAADqBwyYRQcM8N0fgEwGBwz8SAcM8N0fgEwG"
    "Bgx4/AkACQAfgDAFAAAAAA==")),
]


# MiSTer MRA (the bacon_u4 CRC is filled in from PATCHED_CRC when written)
MRA_TEMPLATE = """<!--
  ikacore_CV1k MRA - Muchi Muchi Pork! (Japan, 2007/ 4/17 MASTER VER.).
  Converted from the community MRA (same set, zip names, CRCs and
  <about>) to the DDR3-direct delivery format, 2026-09-17.

  DELIVERY: the NAND and YMZ images do not stream over the ioctl/SPI
  lane.  Both roms carry an `address=` attribute, so Main_MiSTer
  assembles them and memcpys them straight into DDR3; the fabric sees
  only a download pulse for those two.  Only u4 streams, so the ioctl
  lane carries 4 MiB instead of the old 152 MiB.  Needs a Main_MiSTer
  that parses `address` (2021 or later).  Rationale and evidence:
  docs/mra_ddr3_direct_upload_plan.md.

  Rom order is deliberate - DDR3 first, index 0 LAST.  Index 0's download
  is what finally releases the CPU, so every image is in place before the
  core runs, and any spurious run in an inter-rom gap is wiped by the u4
  download's own reset hold.

    <rom index="1">  DDR3 0x34400000  u2  NAND dump incl. spare (132 MiB,
                                          exact size)
    <rom index="2">  DDR3 0x3C800000  u23 YMZ chip 0, zero-padded to the
                                          8 MiB slot
                     DDR3 0x3D000000  u24 YMZ chip 1, zero-padded to the
                                          8 MiB slot
    <rom index="0">  ioctl stream     u4  program NOR x2 (2 MiB file listed
                                          twice = the undecoded-A21 mirror
                                          the boot ROM expects)
-->
<misterromdescription>
    <about author="ika-musume" source="https://github.com/ika-musume/ikacore_CV1k"/>
    <name>Muchi Muchi Pork! (Japan, 2007/ 4/17 MASTER VER.)</name>
    <setname>mmporkbcn</setname>
    <year>2007</year>
    <manufacturer>Cave</manufacturer>
    <category>Shooter</category>
    <rbf>ikacore_CV1k</rbf>

    <rom index="1" address="0x34400000" zip="mmporkbcn.zip" md5="none">
        <part name="u2" crc="1ee961b8"/>
    </rom>

    <rom index="2" address="0x3C800000" zip="mmporkbcn.zip" md5="none">
        <part name="u23" crc="4a4b36df"/>
        <part repeat="0x400000">00</part>
        <part name="u24" crc="ce83d07b"/>
        <part repeat="0x400000">00</part>
    </rom>

    <nvram index="3" size="135680"/>

    <rom index="0" zip="mmporkbcn.zip" md5="none">
        <part name="bacon_u4" crc="13dc786f"/>
        <part name="bacon_u4" crc="13dc786f"/>
    </rom>

    <buttons names="B1,B2,B3,B4,Start,Coin,Test,Service,Save State" default="A,B,X,Y,Start,R,L,Select"/>
</misterromdescription>
"""


def find_u4(zf):
    for name in zf.namelist():
        if os.path.basename(name).lower() in ("u4", OUT_NAME):
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


def mra_text():
    import re
    return re.sub(r'(<part name="bacon_u4" crc=")[0-9a-fA-F]{8}', lambda m: m.group(1) + "%08x" % PATCHED_CRC, MRA_TEMPLATE)


def main():
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 40)")
    ap.add_argument("input", help="mmpork.zip or a loose original u4 file")
    ap.add_argument("-o", "--output", help="where to write bacon_u4")
    ap.add_argument("--zip", action="store_true", help="also write mmporkbcn.zip (input must be a zip)")
    ap.add_argument("--mra", action="store_true", help="also write the MiSTer .mra")
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
    out = a.output or os.path.join(folder, OUT_NAME)
    with open(out, "wb") as f:
        f.write(patched)
    print("original u4 CRC %08x OK" % ORIG_CRC)
    print("wrote %s (CRC %08x)" % (out, PATCHED_CRC))

    if a.zip:
        if not is_zip:
            sys.exit("error: --zip needs mmpork.zip as input")
        zout = os.path.join(folder, SET_NAME)
        with zipfile.ZipFile(a.input) as zi, zipfile.ZipFile(zout, "w", zipfile.ZIP_DEFLATED) as zo:
            for info in zi.infolist():
                if info.filename == name:
                    zo.writestr(OUT_NAME, patched)
                else:
                    zo.writestr(info.filename, zi.read(info.filename))
        print("wrote %s (u4 replaced by %s)" % (zout, OUT_NAME))
    if a.mra:
        mout = os.path.join(folder, MRA_NAME)
        with open(mout, "w", newline="\n") as f:
            f.write(mra_text())
        print("wrote %s" % mout)
    print("Back up your original u4 before flashing real hardware.")


if __name__ == "__main__":
    main()
