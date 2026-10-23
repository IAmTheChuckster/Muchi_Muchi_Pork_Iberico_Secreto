#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 48

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be fa503266.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0xFA503266
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "YgwyAaAJACDiSCQBi1glAokMNQGgCQAg5Qw2U2NjZCDhIOUf1h/XGrAJABjaAeADGiZP9mv2avZp"
    "9mgLAAkAFdFDYh4iGgEpQQlBAUETYAhAHDAMMENiCDITZAsAI2AT0AshEiYLIiEWCyMyFgskQxYL"
    "JVQWAeALAAInwADIALQARAAJAEsMnHwfgGgRBAwA+AAAq6oAAM3MSAxgS04MuK1IDOhKTgywrQAA"
    "AICAgACASAzEVwoMIN+YALQAAAAAAP8AEA7/Df///////wAAAAD//////////wAAAAD/////////"
    "/wAAAAD//////////wAAAAD//////////wsM8BKYALQAAAAAAP8AEA7/AP///////wAAAAD/////"
    "/////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsM8J+YALQAAAAAAAEAMCr/"
    "AP///////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsM"
    "MNNUALQAAAAAAAEApB8zMv///////wMAMCojIiUk/////wUAIBz/Bf///////wAAAAD/////////"
    "/wAAAAD//////////wwMsByYALQAAAAAAAEAMCr/AP///////wEBIBz/Af///////wAAAAD/////"
    "/////wAAAAD//////////wAAAAD//////////wwMsGdUALQAAAAAAAEApB//Pv///////wMAMCr/"
    "MP///////wUAIBz/AP///////wAAAAD//////////wAAAAD//////////wwMoLmYALQAAAAAAAEA"
    "EA7/OP///////wMAMCr/Gv///////wUAMCr/AP///////wIqMCr/Kv///////wAAAAD/////////"
    "/woMwPmYALQAAQAAAAEABQz/AP///////wAAAAD//////////wAAAAD//////////wAAAAD/////"
    "/////wAAAAD//////////wsMcC+YALQAAQAAgAEAEgz/AP///////wAAAAD//////////wAAAAD/"
    "/////////wAAAAD//////////wAAAAD//////////wsMUEuYALQAAQAAAAEAUAr/AP///////wAA"
    "AAD//////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsMUICYALcAAQAA"
    "AAEAHg//AP///////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD/////"
    "/////wsMkGiYALQAAQAAAAEAJhb/AP///////wAAAAD//////////wAAAAD//////////wAAAAD/"
    "/////////wAAAAD//////////wAAAABIVFNJUCBPUkVKVENJIABTAAAAAAAAAAAAAAAAcCAAgE5V"
    "Rk9JRklDTEFBIEROSSAgU09OAFQAAAAAAABwIACARkFJRklMVEFERVcgVEksSEUgRE5ST0VTAEQA"
    "AHAgAIBZQiAsUk9BIFRVT0hJUkVaIERZQgAAAAAAAAAAcCAAgEFDRVYgLkxBIExJUkhHU1RUICBP"
    "SFQARQAAAABwIACAUk9HSU5JTEFHIE1BIEVOQSBEVEkAUwAAAAAAAHAgAIBTQU9TSUNUQURFSSBU"
    "TkxFRUxUQ0FVAEwAAAAAcCAAgFJQUE9SRVlUUiBNRUlBIE5JV0hUAAAAAAAAAABwIACASFRJRSBS"
    "RVJQU0NFSVRFVlIgR0lUSABTAAAAAHAgAIBPSERMUkUuUwAAAAAAAAAAAAAAAAAAAAAAAAAAcCAA"
    "gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwIACAICAgICAgQUhFVkYgTlUhISAhICAgICAg"
    "AAAAACBwABAwMjYyMS8vMDMyAABNU0tPREVCIENBTk8AAAAAT04gVE9GIFJBU0VMAAAAAAYMTPwG"
    "DHAQH4AcBAYMnNIGDHAQH4A8AAYMRNAHDNB7H4BMAQYMBM8Ti07aE4sB0AYMCM+gYDPJK0AJAAYM"
    "DM8BiAKPH4BYAAkMKAgQfwFxEH8H0AkMLAgdYGiIK0AJAAkMSAgJAAkAH4DQAQcMyGoyYigiHdQr"
    "RAcMzGoQj/Nu824JAAcMQGtRDExcH4CoAgkMwGUM0zBiDNMrQwkMxGUoIguLCQALiwkM9GVRDExc"
    "H4BYAwcMhAEHDNB7H4CoAwYMqHoODKQJH4DMFAYMtHoNDFj2H4BMFgYMxHoODCQLH4BYFgYM1Hk2"
    "2AXmNtgE5gYMIHoo1BDmKNQP5gYMONAODKgPH4BoFgcMqIVMARNgTAFz0wcMrIUgyQggK0MTYAcM"
    "eIcJAAkAH4AAAg4MJCsIDOD4H4BMAg4MRCsIDAD8H4BSAg4MZCsIDMD8H4BYAg4MhCsIDCD/H4Be"
    "Ag4MxCsJDAAAH4DkBwcMAINzYEDJc2Aq0AcMBIMIIEmJK0BzYAcMrIMJAAkAH4CYBwYMlPlyYP+I"
    "uNArQAYMmPlrjQDqCQAA6gcMmEUHDPDdH4BABwcM/EgHDPDdH4BABwYMePwJAAkAH4DgBQ0MKHVO"
    "DDysBAyI+AAAAAA=")),
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
        <part name="bacon_u4" crc="fa503266"/>
        <part name="bacon_u4" crc="fa503266"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 48)")
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
