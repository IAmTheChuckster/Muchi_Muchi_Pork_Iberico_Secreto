#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 55

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 82815b76.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x82815B76
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "0AJnpFCAMAGJhBp1GqVQc2YINlNhaDERQQOJhIUIIJ+JAOFc0A4hGgEpQQlBE2SIsAkAA2eFsAkA"
    "A2aCsAkAA2JDYzDgOCMCiQwzAaAJACDjIOEQMwGLKCICiQwyAaAJACDiDDYMNzNhY2Mu5HNlS9ZL"
    "13awCQBG2qZXBHeCYgDjAOFB1GDlXDVCYAggF4lBUCAwFItPhANmc2mUYP+IDolgMPqLhYUNYAgg"
    "AolCZggmBYkBcUTgTQARQACLDDNk4AwwDDQQRd+LGCEOi6ZQp1IAMgyJIOETYhNjE2QTZTHWMdc+"
    "sAkAIqAJAKZQBxozZCewCQADZiSwCQADZTDgSCQDiUNiDDIBoAkAIOJIJAGLWCUCiQw1AaAJACDl"
    "DDZTY2NkIOEg5R/WH9casAkAGNoB4AMaJk/2a/Zq9mn2aAsACQAV0UNiHiIaASlBCUEBQRNgCEAc"
    "MAwwQ2IIMhNkCwAjYBPQCyESJgsiIRYLIzIWCyRDFgslVBYB4AsAAifAAMgAtABEAAkASwycfAQM"
    "bNIEDAD4AACrqgAAzcxIDGBLTgy4rUgM6EpODLCtAAAAgICAAIBIDMRXCgwg35gAtAAAAAAA/wAQ"
    "Dv8N////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////"
    "CwzwEpgAtAAAAAAA/wAQDv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////"
    "////AAAAAP//////////Cwzwn5gAtAAAAAAAAQAwKv8A////////AAAAAP//////////AAAAAP//"
    "////////AAAAAP//////////AAAAAP//////////Cwww01QAtAAAAAAAAQCkHzMy////////AwAw"
    "KiMiJST/////BQAgHP8F////////AAAAAP//////////AAAAAP//////////DAywHJgAtAAAAAAA"
    "AQAwKv8A////////AQEgHP8B////////AAAAAP//////////AAAAAP//////////AAAAAP//////"
    "////DAywZ1QAtAAAAAAAAQCkH/8+////////AwAwKv8w////////BQAgHP8A////////AAAAAP//"
    "////////AAAAAP//////////DAyguZgAtAAAAAAAAQAQDv84////////AwAwKv8a////////BQAw"
    "Kv8A////////AiowKv8q////////AAAAAP//////////CgzA+ZgAtAABAAAAAQAFDP8A////////"
    "AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////CwxwL5gAtAAB"
    "AACAAQASDP8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//"
    "////////CwxQS5gAtAABAAAAAQBQCv8A////////AAAAAP//////////AAAAAP//////////AAAA"
    "AP//////////AAAAAP//////////CwxQgJgAtwABAAAAAQAeD/8A////////AAAAAP//////////"
    "AAAAAP//////////AAAAAP//////////AAAAAP//////////CwyQaJgAtAABAAAAAQAmFv8A////"
    "////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAEhU"
    "U0lQIE9SRUpUQ0kgAFMAAAAAAAAAAAAAAABwIACATlVGT0lGSUNMQUEgRE5JICBTT04AVAAAAAAA"
    "AHAgAIBGQUlGSUxUQURFVyBUSSxIRSBETlJPRVMARAAAcCAAgFlCICxST0EgVFVPSElSRVogRFlC"
    "AAAAAAAAAABwIACAQUNFViAuTEEgTElSSEdTVFQgIE9IVABFAAAAAHAgAIBST0dJTklMQUcgTUEg"
    "RU5BIERUSQBTAAAAAAAAcCAAgFNBT1NJQ1RBREVJIFROTEVFTFRDQVUATAAAAABwIACAUlBQT1JF"
    "WVRSIE1FSUEgTklXSFQAAAAAAAAAAHAgAIBIVElFIFJFUlBTQ0VJVEVWUiBHSVRIAFMAAAAAcCAA"
    "gE9IRExSRS5TAAAAAAAAAAAAAAAAAAAAAAAAAABwIACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAHAgAIAgICAgICBBSEVWRiBOVSEhICEgICAgICAAAAAAIHAAEDAyNjIxLy8wMzIAAE1TS09E"
    "RUIgQ0FOTwAAAABPTiBUT0YgUkFTRUwAAAAABgxM/AYMcBAEDETEBgyc0gYMcBAEDGTABgxE0AcM"
    "0HsEDHTBBgwEzxOLTtoTiwHQBgwIz6BgM8krQAkABgwMzwGIAo8EDIDACQwoCBB/AXEQfwfQCQws"
    "CB1gaIgrQAkACQxICAkACQAEDPjBBwzIajJiKCId1CtEBwzMahCP827zbgkABwxAa1EMTFwEDNDC"
    "CQzAZQzTMGIM0ytDCQzEZSgiC4sJAAuLCQz0ZVEMTFwEDIDDBwyEAQcM0HsEDNDDBgyoeg4MpAkE"
    "DNDVBgy0eg0MWPYEDFDXBgzEeg4MJAsEDFzXBgzUeTbYBeY22ATmBgwgeijUEOYo1A/mBgw40A4M"
    "qA8EDGzXBwyohUwBE2BMAXPTBwyshSDJCCArQxNgBwx4hwkACQAEDCjCDgwkKwgM4PgEDHTCDgxE"
    "KwgMAPwEDHrCDgxkKwgMwPwEDIDCDgyEKwgMIP8EDIbCDgzEKwkMAAAEDCzIBwwAg3NgQMlzYCrQ"
    "BwwEgwggSYkrQHNgBwysgwkACQAEDODHBgyU+XJg/4i40CtABgyY+WuNAOoJAADqBwyYRQcM8N0E"
    "DIjHBwz8SAcM8N0EDIjHBgx4/AkACQAEDATGDQwodU4MPKwEDIj4AAAAAA==")),
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
        <part name="bacon_u4" crc="82815b76"/>
        <part name="bacon_u4" crc="82815b76"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 55)")
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
