#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 50

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 8a417a33.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x8A417A33
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "UAcaM2QnsAkAA2YksAkAA2Uw4EgkA4lDYgwyAaAJACDiSCQBi1glAokMNQGgCQAg5Qw2U2NjZCDh"
    "IOUf1h/XGrAJABjaAeADGiZP9mv2avZp9mgLAAkAFdFDYh4iGgEpQQlBAUETYAhAHDAMMENiCDIT"
    "ZAsAI2AT0AshEiYLIiEWCyMyFgskQxYLJVQWAeALAAInwADIALQARAAJAEsMnHwfgIARBAwA+AAA"
    "q6oAAM3MSAxgS04MuK1IDOhKTgywrQAAAICAgACASAzEVwoMIN+YALQAAAAAAP8AEA7/Df//////"
    "/wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsM8BKYALQA"
    "AAAAAP8AEA7/AP///////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD/"
    "/////////wsM8J+YALQAAAAAAAEAMCr/AP///////wAAAAD//////////wAAAAD//////////wAA"
    "AAD//////////wAAAAD//////////wsMMNNUALQAAAAAAAEApB8zMv///////wMAMCojIiUk////"
    "/wUAIBz/Bf///////wAAAAD//////////wAAAAD//////////wwMsByYALQAAAAAAAEAMCr/AP//"
    "/////wEBIBz/Af///////wAAAAD//////////wAAAAD//////////wAAAAD//////////wwMsGdU"
    "ALQAAAAAAAEApB//Pv///////wMAMCr/MP///////wUAIBz/AP///////wAAAAD//////////wAA"
    "AAD//////////wwMoLmYALQAAAAAAAEAEA7/OP///////wMAMCr/Gv///////wUAMCr/AP//////"
    "/wIqMCr/Kv///////wAAAAD//////////woMwPmYALQAAQAAAAEABQz/AP///////wAAAAD/////"
    "/////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsMcC+YALQAAQAAgAEAEgz/"
    "AP///////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsM"
    "UEuYALQAAQAAAAEAUAr/AP///////wAAAAD//////////wAAAAD//////////wAAAAD/////////"
    "/wAAAAD//////////wsMUICYALcAAQAAAAEAHg//AP///////wAAAAD//////////wAAAAD/////"
    "/////wAAAAD//////////wAAAAD//////////wsMkGiYALQAAQAAAAEAJhb/AP///////wAAAAD/"
    "/////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAABIVFNJUCBPUkVK"
    "VENJIABTAAAAAAAAAAAAAAAAcCAAgE5VRk9JRklDTEFBIEROSSAgU09OAFQAAAAAAABwIACARkFJ"
    "RklMVEFERVcgVEksSEUgRE5ST0VTAEQAAHAgAIBZQiAsUk9BIFRVT0hJUkVaIERZQgAAAAAAAAAA"
    "cCAAgEFDRVYgLkxBIExJUkhHU1RUICBPSFQARQAAAABwIACAUk9HSU5JTEFHIE1BIEVOQSBEVEkA"
    "UwAAAAAAAHAgAIBTQU9TSUNUQURFSSBUTkxFRUxUQ0FVAEwAAAAAcCAAgFJQUE9SRVlUUiBNRUlB"
    "IE5JV0hUAAAAAAAAAABwIACASFRJRSBSRVJQU0NFSVRFVlIgR0lUSABTAAAAAHAgAIBPSERMUkUu"
    "UwAAAAAAAAAAAAAAAAAAAAAAAAAAcCAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwIACA"
    "ICAgICAgQUhFVkYgTlUhISAhICAgICAgAAAAACBwABAwMjYyMS8vMDMyAABNU0tPREVCIENBTk8A"
    "AAAAT04gVE9GIFJBU0VMAAAAAAYMTPwGDHAQH4AcBAYMnNIGDHAQH4A8AAYMRNAHDNB7H4BMAQYM"
    "BM8Ti07aE4sB0AYMCM+gYDPJK0AJAAYMDM8BiAKPH4BYAAkMKAgQfwFxEH8H0AkMLAgdYGiIK0AJ"
    "AAkMSAgJAAkAH4DQAQcMyGoyYigiHdQrRAcMzGoQj/Nu824JAAcMQGtRDExcH4CoAgkMwGUM0zBi"
    "DNMrQwkMxGUoIguLCQALiwkM9GVRDExcH4BYAwcMhAEHDNB7H4CoAwYMqHoODKQJH4DkFAYMtHoN"
    "DFj2H4BkFgYMxHoODCQLH4BwFgYM1Hk22AXmNtgE5gYMIHoo1BDmKNQP5gYMONAODKgPH4CAFgcM"
    "qIVMARNgTAFz0wcMrIUgyQggK0MTYAcMeIcJAAkAH4AAAg4MJCsIDOD4H4BMAg4MRCsIDAD8H4BS"
    "Ag4MZCsIDMD8H4BYAg4MhCsIDCD/H4BeAg4MxCsJDAAAH4CIBwcMAINzYEDJc2Aq0AcMBIMIIEmJ"
    "K0BzYAcMrIMJAAkAH4A8BwYMlPlyYP+IuNArQAYMmPlrjQDqCQAA6gcMmEUHDPDdH4DkBgcM/EgH"
    "DPDdH4DkBgYMePwJAAkAH4CEBQ0MKHVODDysBAyI+AAAAAA=")),
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
        <part name="bacon_u4" crc="8a417a33"/>
        <part name="bacon_u4" crc="8a417a33"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 50)")
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
