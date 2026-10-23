#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 26

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 0d46e765.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x0D46E765
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "AANnhbAJAANmgrAJAANiQ2Mw4DgjAokMMwGgCQAg4yDhEDMBiygiAokMMgGgCQAg4gw2DDczYWNj"
    "LuRzZUvWS9d2sAkARtqmVwR3gmIA4wDhQdRg5Vw1QmAIIBeJQVAgMBSLT4QDZnNplGD/iA6JYDD6"
    "i4WFDWAIIAKJQmYIJgWJAXFE4E0AEUAAiwwzZOAMMAw0EEXfixghDoumUKdSADIMiSDhE2ITYxNk"
    "E2Ux1jHXPrAJACKgCQCmUAcaM2QnsAkAA2YksAkAA2Uw4EgkA4lDYgwyAaAJACDiSCQBi1glAokM"
    "NQGgCQAg5Qw2U2NjZCDhIOUf1h/XGrAJABjaAeADGiZP9mv2avZp9mgLAAkAFdFDYh4iGgEpQQlB"
    "AUETYAhAHDAMMENiCDITZAsAI2AT0AshEiYLIiEWCyMyFgskQxYLJVQWAeALAAInwADIALQARAAJ"
    "AEsMnHwfgIwLBAwA+AAAq6oAAM3MSAxgS04MuK1IDOhKTgywrQAAAICAgACASAzEVwoMIN+YALQA"
    "AAAAAP8AEA7/Df///////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD/"
    "/////////wsM8BKYALQAAAAAAP8AEA7/AP///////wAAAAD//////////wAAAAD//////////wAA"
    "AAD//////////wAAAAD//////////wsM8J+YALQAAAAAAAEAMCr/AP///////wAAAAD/////////"
    "/wAAAAD//////////wAAAAD//////////wAAAAD//////////wsMMNNUALQAAAAAAAEApB8zMv//"
    "/////wMAMCojIiUk/////wUAIBz/Bf///////wAAAAD//////////wAAAAD//////////wwMsByY"
    "ALQAAAAAAAEAMCr/AP///////wEBIBz/Af///////wAAAAD//////////wAAAAD//////////wAA"
    "AAD//////////wwMsGdUALQAAAAAAAEApB//Pv///////wMAMCr/MP///////wUAIBz/AP//////"
    "/wAAAAD//////////wAAAAD//////////wwMoLmYALQAAAAAAAEAEA7/OP///////wMAMCr/Gv//"
    "/////wUAMCr/AP///////wIqMCr/Kv///////wAAAAD//////////woMwPmYALQAAQAAAAEABQz/"
    "AP///////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsM"
    "cC+YALQAAQAAgAEAEgz/AP///////wAAAAD//////////wAAAAD//////////wAAAAD/////////"
    "/wAAAAD//////////wsMUEuYALQAAQAAAAEAUAr/AP///////wAAAAD//////////wAAAAD/////"
    "/////wAAAAD//////////wAAAAD//////////wsMUICYALcAAQAAAAEAHg//AP///////wAAAAD/"
    "/////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsMkGiYALQAAQAAAAEA"
    "Jhb/AP///////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD/////////"
    "/wAAAABIVFNJUCBPUkVKVENJIABTAAAAAAAAAAAAAAAAcCAAgE5VRk9JRklDTEFBIEROSSAgU09O"
    "AFQAAAAAAABwIACARkFJRklMVEFERVcgVEksSEUgRE5ST0VTAEQAAHAgAIBZQiAsUk9BIFRVT0hJ"
    "UkVaIERZQgAAAAAAAAAAcCAAgEFDRVYgLkxBIExJUkhHU1RUICBPSFQARQAAAABwIACAUk9HSU5J"
    "TEFHIE1BIEVOQSBEVEkAUwAAAAAAAHAgAIBTQU9TSUNUQURFSSBUTkxFRUxUQ0FVAEwAAAAAcCAA"
    "gFJQUE9SRVlUUiBNRUlBIE5JV0hUAAAAAAAAAABwIACASFRJRSBSRVJQU0NFSVRFVlIgR0lUSABT"
    "AAAAAHAgAIBPSERMUkUuUwAAAAAAAAAAAAAAAAAAAAAAAAAAcCAAgAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAABwIACAICAgICAgQUhFVkYgTlUhISAhICAgICAgAAAAACBwABAwMjYyMS8vMDMy"
    "AABNU0tPREVCIENBTk8AAAAAT04gVE9GIFJBU0VMAAAAAAYMTPwGDHAQH4DYAwYMnNIGDHAQH4Ak"
    "AAYMRNAHDNB7H4AgAQYMBM8Ti07aE4sB0AYMCM+gYDPJK0AJAAYMDM8BiAKPH4BAAAkMKAgQfwFx"
    "EH8H0AkMLAgdYGiIK0AJAAkMSAgJAAkAH4CkAQcMyGoyYigiHdQrRAcMzGoQj/Nu824JAAcMQGtR"
    "DExcH4B8AgkMwGUM0zBiDNMrQwkMxGUoIguLCQALiwkM9GVRDExcH4AgAwcMhAEHDNB7H4BkAwYM"
    "qHoODKQJH4DwDgYMtHoNDFj2H4BwEAYMxHoODCQLH4B8EAYM1Hk22AXmNtgE5gYMIHoo1BDmKNQP"
    "5gYMONAODKgPH4CMEAcMqIVMARNgTAFz0wcMrIUgyQggK0MTYAcMeIcJAAkAH4DUAQ4MJCsIDOD4"
    "H4AgAg4MRCsIDAD8H4AmAg4MZCsIDMD8H4AsAg4MhCsIDCD/H4AyAg4MxCsJDAAAH4CEBQAAAAA=")),
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
        <part name="bacon_u4" crc="0d46e765"/>
        <part name="bacon_u4" crc="0d46e765"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 26)")
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
