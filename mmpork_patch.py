#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 43

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 6761cfa3.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x6761CFA3
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "vDuSYAggCYmRUY/YgmIoIgSJEDIpiUh4+K8JAGTgDDAMORBL7YuJ2qhQCCAAiwQaAOAHGqNQCCAB"
    "i9mgCQAA4AMaIOETYhNjE2QTZYLWg9flsAkAIOETYhNjE2QTZYDWgNfcsAkAw6AJAHjapFCAMAGL"
    "AeAIGoKFDWCeBp+EA2KDhZwDg2EMcRGFDWVYJQyJEGD/iAGJIDAEixGE/4gGiTAwBIkMce+vCQC3"
    "rwkAZ9oWGoSFCCAKiWTabdACZ6RQgDABiYQadRqlUHNmCDZTYWgxEUEDiYSFCCCfiQDhXNAOIRoB"
    "KUEJQRNkiLAJAANnhbAJAANmgrAJAANiQ2Mw4DgjAokMMwGgCQAg4yDhEDMBiygiAokMMgGgCQAg"
    "4gw2DDczYWNjLuRzZUvWS9d2sAkARtqmVwR3gmIA4wDhQdRg5Vw1QmAIIBeJQVAgMBSLT4QDZnNp"
    "lGD/iA6JYDD6i4WFDWAIIAKJQmYIJgWJAXFE4E0AEUAAiwwzZOAMMAw0EEXfixghDoumUKdSADIM"
    "iSDhE2ITYxNkE2Ux1jHXPrAJACKgCQCmUAcaM2QnsAkAA2YksAkAA2Uw4EgkA4lDYgwyAaAJACDi"
    "SCQBi1glAokMNQGgCQAg5Qw2U2NjZCDhIOUf1h/XGrAJABjaAeADGiZP9mv2avZp9mgLAAkAFdFD"
    "Yh4iGgEpQQlBAUETYAhAHDAMMENiCDITZAsAI2AT0AshEiYLIiEWCyMyFgskQxYLJVQWAeALAAIn"
    "wADIALQARAAJAEsMnHwfgNAPBAwA+AAAq6oAAM3MSAxgS04MuK1IDOhKTgywrQAAAICAgACASAzE"
    "VwoMIN+YALQAAAAAAP8AEA7/Df///////wAAAAD//////////wAAAAD//////////wAAAAD/////"
    "/////wAAAAD//////////wsM8BKYALQAAAAAAP8AEA7/AP///////wAAAAD//////////wAAAAD/"
    "/////////wAAAAD//////////wAAAAD//////////wsM8J+YALQAAAAAAAEAMCr/AP///////wAA"
    "AAD//////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsMMNNUALQAAAAA"
    "AAEApB8zMv///////wMAMCojIiUk/////wUAIBz/Bf///////wAAAAD//////////wAAAAD/////"
    "/////wwMsByYALQAAAAAAAEAMCr/AP///////wEBIBz/Af///////wAAAAD//////////wAAAAD/"
    "/////////wAAAAD//////////wwMsGdUALQAAAAAAAEApB//Pv///////wMAMCr/MP///////wUA"
    "IBz/AP///////wAAAAD//////////wAAAAD//////////wwMoLmYALQAAAAAAAEAEA7/OP//////"
    "/wMAMCr/Gv///////wUAMCr/AP///////wIqMCr/Kv///////wAAAAD//////////woMwPmYALQA"
    "AQAAAAEABQz/AP///////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD/"
    "/////////wsMcC+YALQAAQAAgAEAEgz/AP///////wAAAAD//////////wAAAAD//////////wAA"
    "AAD//////////wAAAAD//////////wsMUEuYALQAAQAAAAEAUAr/AP///////wAAAAD/////////"
    "/wAAAAD//////////wAAAAD//////////wAAAAD//////////wsMUICYALcAAQAAAAEAHg//AP//"
    "/////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsMkGiY"
    "ALQAAQAAAAEAJhb/AP///////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAA"
    "AAD//////////wAAAABIVFNJUCBPUkVKVENJIABTAAAAAAAAAAAAAAAAcCAAgE5VRk9JRklDTEFB"
    "IEROSSAgU09OAFQAAAAAAABwIACARkFJRklMVEFERVcgVEksSEUgRE5ST0VTAEQAAHAgAIBZQiAs"
    "Uk9BIFRVT0hJUkVaIERZQgAAAAAAAAAAcCAAgEFDRVYgLkxBIExJUkhHU1RUICBPSFQARQAAAABw"
    "IACAUk9HSU5JTEFHIE1BIEVOQSBEVEkAUwAAAAAAAHAgAIBTQU9TSUNUQURFSSBUTkxFRUxUQ0FV"
    "AEwAAAAAcCAAgFJQUE9SRVlUUiBNRUlBIE5JV0hUAAAAAAAAAABwIACASFRJRSBSRVJQU0NFSVRF"
    "VlIgR0lUSABTAAAAAHAgAIBPSERMUkUuUwAAAAAAAAAAAAAAAAAAAAAAAAAAcCAAgAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAABwIACAICAgICAgQUhFVkYgTlUhISAhICAgICAgAAAAACBwABAw"
    "MjYyMS8vMDMyAABNU0tPREVCIENBTk8AAAAAT04gVE9GIFJBU0VMAAAAAAYMTPwGDHAQH4DsAwYM"
    "nNIGDHAQH4AkAAYMRNAHDNB7H4A0AQYMBM8Ti07aE4sB0AYMCM+gYDPJK0AJAAYMDM8BiAKPH4BA"
    "AAkMKAgQfwFxEH8H0AkMLAgdYGiIK0AJAAkMSAgJAAkAH4C4AQcMyGoyYigiHdQrRAcMzGoQj/Nu"
    "824JAAcMQGtRDExcH4CQAgkMwGUM0zBiDNMrQwkMxGUoIguLCQALiwkM9GVRDExcH4A0AwcMhAEH"
    "DNB7H4B4AwYMqHoODKQJH4A0EwYMtHoNDFj2H4C0FAYMxHoODCQLH4DAFAYM1Hk22AXmNtgE5gYM"
    "IHoo1BDmKNQP5gYMONAODKgPH4DQFAcMqIVMARNgTAFz0wcMrIUgyQggK0MTYAcMeIcJAAkAH4Do"
    "AQ4MJCsIDOD4H4A0Ag4MRCsIDAD8H4A6Ag4MZCsIDMD8H4BAAg4MhCsIDCD/H4BGAg4MxCsJDAAA"
    "H4A0BwcMAINzYEDJc2Aq0AcMBIMIIEmJK0BzYAcMrIMJAAkAH4DoBgYMlPlyYP+IuNArQAYMmPlr"
    "jQDqCQAA6gcMmEUHDPDdH4CQBgcM/EgHDPDdH4CQBgYMePwJAAkAH4BEBQAAAAA=")),
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
        <part name="bacon_u4" crc="6761cfa3"/>
        <part name="bacon_u4" crc="6761cfa3"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 43)")
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
