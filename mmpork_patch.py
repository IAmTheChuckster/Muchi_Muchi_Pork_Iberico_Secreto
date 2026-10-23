#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 53

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 2e86b604.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x2E86B604
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "MgGgCQAg4gw2DDczYWNjLuRzZUvWS9d2sAkARtqmVwR3gmIA4wDhQdRg5Vw1QmAIIBeJQVAgMBSL"
    "T4QDZnNplGD/iA6JYDD6i4WFDWAIIAKJQmYIJgWJAXFE4E0AEUAAiwwzZOAMMAw0EEXfixghDoum"
    "UKdSADIMiSDhE2ITYxNkE2Ux1jHXPrAJACKgCQCmUAcaM2QnsAkAA2YksAkAA2Uw4EgkA4lDYgwy"
    "AaAJACDiSCQBi1glAokMNQGgCQAg5Qw2U2NjZCDhIOUf1h/XGrAJABjaAeADGiZP9mv2avZp9mgL"
    "AAkAFdFDYh4iGgEpQQlBAUETYAhAHDAMMENiCDITZAsAI2AT0AshEiYLIiEWCyMyFgskQxYLJVQW"
    "AeALAAInwADIALQARAAJAEsMnHwEDBDSBAwA+AAAq6oAAM3MSAxgS04MuK1IDOhKTgywrQAAAICA"
    "gACASAzEVwoMIN+YALQAAAAAAP8AEA7/Df///////wAAAAD//////////wAAAAD//////////wAA"
    "AAD//////////wAAAAD//////////wsM8BKYALQAAAAAAP8AEA7/AP///////wAAAAD/////////"
    "/wAAAAD//////////wAAAAD//////////wAAAAD//////////wsM8J+YALQAAAAAAAEAMCr/AP//"
    "/////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsMMNNU"
    "ALQAAAAAAAEApB8zMv///////wMAMCojIiUk/////wUAIBz/Bf///////wAAAAD//////////wAA"
    "AAD//////////wwMsByYALQAAAAAAAEAMCr/AP///////wEBIBz/Af///////wAAAAD/////////"
    "/wAAAAD//////////wAAAAD//////////wwMsGdUALQAAAAAAAEApB//Pv///////wMAMCr/MP//"
    "/////wUAIBz/AP///////wAAAAD//////////wAAAAD//////////wwMoLmYALQAAAAAAAEAEA7/"
    "OP///////wMAMCr/Gv///////wUAMCr/AP///////wIqMCr/Kv///////wAAAAD//////////woM"
    "wPmYALQAAQAAAAEABQz/AP///////wAAAAD//////////wAAAAD//////////wAAAAD/////////"
    "/wAAAAD//////////wsMcC+YALQAAQAAgAEAEgz/AP///////wAAAAD//////////wAAAAD/////"
    "/////wAAAAD//////////wAAAAD//////////wsMUEuYALQAAQAAAAEAUAr/AP///////wAAAAD/"
    "/////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsMUICYALcAAQAAAAEA"
    "Hg//AP///////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD/////////"
    "/wsMkGiYALQAAQAAAAEAJhb/AP///////wAAAAD//////////wAAAAD//////////wAAAAD/////"
    "/////wAAAAD//////////wAAAABIVFNJUCBPUkVKVENJIABTAAAAAAAAAAAAAAAAcCAAgE5VRk9J"
    "RklDTEFBIEROSSAgU09OAFQAAAAAAABwIACARkFJRklMVEFERVcgVEksSEUgRE5ST0VTAEQAAHAg"
    "AIBZQiAsUk9BIFRVT0hJUkVaIERZQgAAAAAAAAAAcCAAgEFDRVYgLkxBIExJUkhHU1RUICBPSFQA"
    "RQAAAABwIACAUk9HSU5JTEFHIE1BIEVOQSBEVEkAUwAAAAAAAHAgAIBTQU9TSUNUQURFSSBUTkxF"
    "RUxUQ0FVAEwAAAAAcCAAgFJQUE9SRVlUUiBNRUlBIE5JV0hUAAAAAAAAAABwIACASFRJRSBSRVJQ"
    "U0NFSVRFVlIgR0lUSABTAAAAAHAgAIBPSERMUkUuUwAAAAAAAAAAAAAAAAAAAAAAAAAAcCAAgAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwIACAICAgICAgQUhFVkYgTlUhISAhICAgICAgAAAA"
    "ACBwABAwMjYyMS8vMDMyAABNU0tPREVCIENBTk8AAAAAT04gVE9GIFJBU0VMAAAAAAYMTPwGDHAQ"
    "BAxExAYMnNIGDHAQBAxkwAYMRNAHDNB7BAx0wQYMBM8Ti07aE4sB0AYMCM+gYDPJK0AJAAYMDM8B"
    "iAKPBAyAwAkMKAgQfwFxEH8H0AkMLAgdYGiIK0AJAAkMSAgJAAkABAz4wQcMyGoyYigiHdQrRAcM"
    "zGoQj/Nu824JAAcMQGtRDExcBAzQwgkMwGUM0zBiDNMrQwkMxGUoIguLCQALiwkM9GVRDExcBAyA"
    "wwcMhAEHDNB7BAzQwwYMqHoODKQJBAx01QYMtHoNDFj2BAz01gYMxHoODCQLBAwA1wYM1Hk22AXm"
    "NtgE5gYMIHoo1BDmKNQP5gYMONAODKgPBAwQ1wcMqIVMARNgTAFz0wcMrIUgyQggK0MTYAcMeIcJ"
    "AAkABAwowg4MJCsIDOD4BAx0wg4MRCsIDAD8BAx6wg4MZCsIDMD8BAyAwg4MhCsIDCD/BAyGwg4M"
    "xCsJDAAABAzQxwcMAINzYEDJc2Aq0AcMBIMIIEmJK0BzYAcMrIMJAAkABAyExwYMlPlyYP+IuNAr"
    "QAYMmPlrjQDqCQAA6gcMmEUHDPDdBAwsxwcM/EgHDPDdBAwsxwYMePwJAAkABAyoxQ0MKHVODDys"
    "BAyI+AAAAAA=")),
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
        <part name="bacon_u4" crc="2e86b604"/>
        <part name="bacon_u4" crc="2e86b604"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 53)")
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
