#!/usr/bin/env python3
"""
Muchi Muchi Pork! Iberico Secreto (Cave CV1000) - patch build 60

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes iberico_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkibc.zip (the set with u4 replaced by iberico_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Iberico Secreto.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched iberico_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 861939e8.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x861939E8
U4_SIZE = 0x200000
OUT_NAME = "iberico_u4"
SET_NAME = "mmporkibc.zip"
MRA_NAME = "Muchi Muchi Pork! Iberico Secreto.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "iQxx768JALevCQBn2hYahIUIIAqJZNpt0AJnpFCAMAGJhBp1GqVQc2YINlNhaDERQQOJhIUIIJ+J"
    "AOFc0A4hGgEpQQlBE2SIsAkAA2eFsAkAA2aCsAkAA2JDYzDgOCMCiQwzAaAJACDjIOEQMwGLKCIC"
    "iQwyAaAJACDiDDYMNzNhY2Mu5HNlS9ZL13awCQBG2qZXBHeCYgDjAOFB1GDlXDVCYAggF4lBUCAw"
    "FItPhANmc2mUYP+IDolgMPqLhYUNYAggAolCZggmBYkBcUTgTQARQACLDDNk4AwwDDQQRd+LGCEO"
    "i6ZQp1IAMgyJIOETYhNjE2QTZTHWMdc+sAkAIqAJAKZQBxozZCewCQADZiSwCQADZTDgSCQDiUNi"
    "DDIBoAkAIOJIJAGLWCUCiQw1AaAJACDlDDZTY2NkIOEg5R/WH9casAkAGNoB4AMaJk/2a/Zq9mn2"
    "aAsACQAV0UNiHiIaASlBCUEBQRNgCEAcMAwwQ2IIMhNkCwAjYBPQCyESJgsiIRYLIzIWCyRDFgsl"
    "VBYB4AsAAifAAMgAtABEAAkASwycfAQMhNIEDAD4AACrqgAAzcxIDGBLTgy4rUgM6EpODLCtAAAA"
    "gICAAIBIDMRXCgwg35gAtAAAAAAA/wAQDv8N////////AAAAAP//////////AAAAAP//////////"
    "AAAAAP//////////AAAAAP//////////CwzwEpgAtAAAAAAA/wAQDv8A////////AAAAAP//////"
    "////AAAAAP//////////AAAAAP//////////AAAAAP//////////Cwzwn5gAtAAAAAAAAQAwKv8A"
    "////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////Cwww"
    "01QAtAAAAAAAAQCkHzMy////////AwAwKiMiJST/////BQAgHP8F////////AAAAAP//////////"
    "AAAAAP//////////DAywHJgAtAAAAAAAAQAwKv8A////////AQEgHP8B////////AAAAAP//////"
    "////AAAAAP//////////AAAAAP//////////DAywZ1QAtAAAAAAAAQCkH/8+////////AwAwKv8w"
    "////////BQAgHP8A////////AAAAAP//////////AAAAAP//////////DAyguZgAtAAAAAAAAQAQ"
    "Dv84////////AwAwKv8a////////BQAwKv8A////////AiowKv8q////////AAAAAP//////////"
    "CgzA+ZgAtAABAAAAAQAFDP8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////"
    "////AAAAAP//////////CwxwL5gAtAABAACAAQASDP8A////////AAAAAP//////////AAAAAP//"
    "////////AAAAAP//////////AAAAAP//////////CwxQS5gAtAABAAAAAQBQCv8A////////AAAA"
    "AP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////CwxQgJgAtwABAAAA"
    "AQAeD/8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////"
    "////CwyQaJgAtAABAAAAAQAmFv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//"
    "////////AAAAAP//////////AAAAAEhUU0lQIE9SRUpUQ0kgAFMAAAAAAAAAAAAAAABwIACATlVG"
    "T0lGSUNMQUEgRE5JICBTT04AVAAAAAAAAHAgAIBGQUlGSUxUQURFVyBUSSxIRSBETlJPRVMARAAA"
    "cCAAgFlCICxST0EgVFVPSElSRVogRFlCAAAAAAAAAABwIACAQUNFViAuTEEgTElSSEdTVFQgIE9I"
    "VABFAAAAAHAgAIBST0dJTklMQUcgTUEgRU5BIERUSQBTAAAAAAAAcCAAgFNBT1NJQ1RBREVJIFRO"
    "TEVFTFRDQVUATAAAAABwIACAUlBQT1JFWVRSIE1FSUEgTklXSFQAAAAAAAAAAHAgAIBIVElFIFJF"
    "UlBTQ0VJVEVWUiBHSVRIAFMAAAAAcCAAgE9IRExSRS5TAAAAAAAAAAAAAAAAAAAAAAAAAABwIACA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAgAIAgICAgICBBSEVWRiBOVSEhICEgICAgICAA"
    "AAAAIHAAEDAyNjIxLy8wNDJJIEVCSVJPQ1MgQ0VFUk9UAAAAAAAAT04gVE9GIFJBU0VMAAAAAAYM"
    "TPwGDHAQBAxExAYMnNIGDHAQBAxkwAYMRNAHDNB7BAx0wQYMBM8Ti07aE4sB0AYMCM+gYDPJK0AJ"
    "AAYMDM8BiAKPBAyAwAkMKAgQfwFxEH8H0AkMLAgdYGiIK0AJAAkMSAgJAAkABAz4wQcMyGoyYigi"
    "HdQrRAcMzGoQj/Nu824JAAcMQGtRDExcBAzQwgkMwGUM0zBiDNMrQwkMxGUoIguLCQALiwkM9GVR"
    "DExcBAyAwwcMhAEHDNB7BAzQwwYMqHoODKQJBAzo1QYMtHoNDFj2BAxo1wYM1Hk22AXmNtgC5gYM"
    "xHoODCQLBAyE1wYM1Hk22AXmNtgE5gYMIHoo1BDmKNQP5gYMONAODKgPBAyI1wcMqIVMARNgTAFz"
    "0wcMrIUgyQggK0MTYAcMeIcJAAkABAwowg4MJCsIDOD4BAx0wg4MRCsIDAD8BAx6wg4MZCsIDMD8"
    "BAyAwg4MhCsIDCD/BAyGwg4MxCsJDAAABAwwyAcMAINzYEDJc2Aq0AcMBIMIIEmJK0BzYAcMrIMJ"
    "AAkABAzkxwYMlPlyYP+IuNArQAYMmPlrjQDqCQAA6gcMmEUHDPDdBAyMxwcM/EgHDPDdBAyMxwYM"
    "ePwJAAkABAwIxg0MKHVODDysBAyI+AAAAAA=")),
]


# MiSTer MRA (the iberico_u4 CRC is filled in from PATCHED_CRC when written)
MRA_TEMPLATE = """<!--
  ikacore_CV1k MRA - Muchi Muchi Pork! Iberico Secreto (2026/10/24 IBERICO).
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
    <name>Muchi Muchi Pork! Iberico Secreto (2026/10/24 IBERICO)</name>
    <setname>mmporkibc</setname>
    <year>2007</year>
    <manufacturer>Cave</manufacturer>
    <category>Shooter</category>
    <rbf>ikacore_CV1k</rbf>

    <rom index="1" address="0x34400000" zip="mmporkibc.zip" md5="none">
        <part name="u2" crc="1ee961b8"/>
    </rom>

    <rom index="2" address="0x3C800000" zip="mmporkibc.zip" md5="none">
        <part name="u23" crc="4a4b36df"/>
        <part repeat="0x400000">00</part>
        <part name="u24" crc="ce83d07b"/>
        <part repeat="0x400000">00</part>
    </rom>

    <nvram index="3" size="135680"/>

    <rom index="0" zip="mmporkibc.zip" md5="none">
        <part name="iberico_u4" crc="861939e8"/>
        <part name="iberico_u4" crc="861939e8"/>
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
    return re.sub(r'(<part name="iberico_u4" crc=")[0-9a-fA-F]{8}', lambda m: m.group(1) + "%08x" % PATCHED_CRC, MRA_TEMPLATE)


def main():
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into iberico_u4 (Iberico Secreto, build 60)")
    ap.add_argument("input", help="mmpork.zip or a loose original u4 file")
    ap.add_argument("-o", "--output", help="where to write iberico_u4")
    ap.add_argument("--zip", action="store_true", help="also write mmporkibc.zip (input must be a zip)")
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
