#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 41

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 01b0d854.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x01B0D854
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "qFAIIACLBBoA4Acao1AIIAGL2aAJAADgAxog4RNiE2MTZBNlgtaD1+WwCQAg4RNiE2MTZBNlgNaA"
    "19ywCQDDoAkAeNqkUIAwAYsB4AgagoUNYJ4Gn4QDYoOFnAODYQxxEYUNZVglDIkQYP+IAYkgMASL"
    "EYT/iAaJMDAEiQxx768JALevCQBn2hYahIUIIAqJZNpt0AJnpFCAMAGJhBp1GqVQc2YINlNhaDER"
    "QQOJhIUIIJ+JAOFc0A4hGgEpQQlBE2SIsAkAA2eFsAkAA2aCsAkAA2JDYzDgOCMCiQwzAaAJACDj"
    "IOEQMwGLKCICiQwyAaAJACDiDDYMNzNhY2Mu5HNlS9ZL13awCQBG2qZXBHeCYgDjAOFB1GDlXDVC"
    "YAggF4lBUCAwFItPhANmc2mUYP+IDolgMPqLhYUNYAggAolCZggmBYkBcUTgTQARQACLDDNk4Aww"
    "DDQQRd+LGCEOi6ZQp1IAMgyJIOETYhNjE2QTZTHWMdc+sAkAIqAJAKZQBxozZCewCQADZiSwCQAD"
    "ZTDgSCQDiUNiDDIBoAkAIOJIJAGLWCUCiQw1AaAJACDlDDZTY2NkIOEg5R/WH9casAkAGNoB4AMa"
    "Jk/2a/Zq9mn2aAsACQAV0UNiHiIaASlBCUEBQRNgCEAcMAwwQ2IIMhNkCwAjYBPQCyESJgsiIRYL"
    "IzIWCyRDFgslVBYB4AsAAifAAMgAtABEAAkASwycfB+AqA8EDAD4AACrqgAAzcxIDGBLTgy4rUgM"
    "6EpODLCtAAAAgICAAIBIDMRXCgwg35gAtAAAAAAA/wAQDv8N////////AAAAAP//////////AAAA"
    "AP//////////AAAAAP//////////AAAAAP//////////CwzwEpgAtAAAAAAA/wAQDv8A////////"
    "AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////Cwzwn5gAtAAA"
    "AAAAAQAwKv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//"
    "////////Cwww01QAtAAAAAAAAQCkHzMy////////AwAwKiMiJST/////BQAgHP8F////////AAAA"
    "AP//////////AAAAAP//////////DAywHJgAtAAAAAAAAQAwKv8A////////AQEgHP8B////////"
    "AAAAAP//////////AAAAAP//////////AAAAAP//////////DAywZ1QAtAAAAAAAAQCkH/8+////"
    "////AwAwKv8w////////BQAgHP8A////////AAAAAP//////////AAAAAP//////////DAyguZgA"
    "tAAAAAAAAQAQDv84////////AwAwKv8a////////BQAwKv8A////////AiowKv8q////////AAAA"
    "AP//////////CgzA+ZgAtAABAAAAAQAFDP8A////////AAAAAP//////////AAAAAP//////////"
    "AAAAAP//////////AAAAAP//////////CwxwL5gAtAABAACAAQASDP8A////////AAAAAP//////"
    "////AAAAAP//////////AAAAAP//////////AAAAAP//////////CwxQS5gAtAABAAAAAQBQCv8A"
    "////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////CwxQ"
    "gJgAtwABAAAAAQAeD/8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////"
    "AAAAAP//////////CwyQaJgAtAABAAAAAQAmFv8A////////AAAAAP//////////AAAAAP//////"
    "////AAAAAP//////////AAAAAP//////////AAAAAEhUU0lQIE9SRUpUQ0kgAFMAAAAAAAAAAAAA"
    "AABwIACATlVGT0lGSUNMQUEgRE5JICBTT04AVAAAAAAAAHAgAIBGQUlGSUxUQURFVyBUSSxIRSBE"
    "TlJPRVMARAAAcCAAgFlCICxST0EgVFVPSElSRVogRFlCAAAAAAAAAABwIACAQUNFViAuTEEgTElS"
    "SEdTVFQgIE9IVABFAAAAAHAgAIBST0dJTklMQUcgTUEgRU5BIERUSQBTAAAAAAAAcCAAgFNBT1NJ"
    "Q1RBREVJIFROTEVFTFRDQVUATAAAAABwIACAUlBQT1JFWVRSIE1FSUEgTklXSFQAAAAAAAAAAHAg"
    "AIBIVElFIFJFUlBTQ0VJVEVWUiBHSVRIAFMAAAAAcCAAgE9IRExSRS5TAAAAAAAAAAAAAAAAAAAA"
    "AAAAAABwIACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAgAIAgICAgICBBSEVWRiBOVSEh"
    "ICEgICAgICAAAAAAIHAAEDAyNjIxLy8wMzIAAE1TS09ERUIgQ0FOTwAAAABPTiBUT0YgUkFTRUwA"
    "AAAABgxM/AYMcBAfgNgDBgyc0gYMcBAfgCQABgxE0AcM0HsfgCABBgwEzxOLTtoTiwHQBgwIz6Bg"
    "M8krQAkABgwMzwGIAo8fgEAACQwoCBB/AXEQfwfQCQwsCB1gaIgrQAkACQxICAkACQAfgKQBBwzI"
    "ajJiKCId1CtEBwzMahCP827zbgkABwxAa1EMTFwfgHwCCQzAZQzTMGIM0ytDCQzEZSgiC4sJAAuL"
    "CQz0ZVEMTFwfgCADBwyEAQcM0HsfgGQDBgyoeg4MpAkfgAwTBgy0eg0MWPYfgIwUBgzEeg4MJAsf"
    "gJgUBgzUeTbYBeY22ATmBgwgeijUEOYo1A/mBgw40A4MqA8fgKgUBwyohUwBE2BMAXPTBwyshSDJ"
    "CCArQxNgBwx4hwkACQAfgNQBDgwkKwgM4PgfgCACDgxEKwgMAPwfgCYCDgxkKwgMwPwfgCwCDgyE"
    "KwgMIP8fgDICDgzEKwkMAAAfgCAHBwwAg3NgQMlzYCrQBwwEgwggSYkrQHNgBwysgwkACQAfgNQG"
    "BgyU+XJg/4i40CtABgyY+WuNAOoJAADqBwyYRQcM8N0fgHwGBwz8SAcM8N0fgHwGBgx4/AkACQAf"
    "gDAFAAAAAA==")),
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
        <part name="bacon_u4" crc="01b0d854"/>
        <part name="bacon_u4" crc="01b0d854"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 41)")
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
