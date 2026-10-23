#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 56

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 77f63093.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x77F63093
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "iRBg/4gBiSAwBIsRhP+IBokwMASJDHHvrwkAt68JAGfaFhqEhQggColk2m3QAmekUIAwAYmEGnUa"
    "pVBzZgg2U2FoMRFBA4mEhQggn4kA4VzQDiEaASlBCUETZIiwCQADZ4WwCQADZoKwCQADYkNjMOA4"
    "IwKJDDMBoAkAIOMg4RAzAYsoIgKJDDIBoAkAIOIMNgw3M2FjYy7kc2VL1kvXdrAJAEbaplcEd4Ji"
    "AOMA4UHUYOVcNUJgCCAXiUFQIDAUi0+EA2ZzaZRg/4gOiWAw+ouFhQ1gCCACiUJmCCYFiQFxROBN"
    "ABFAAIsMM2TgDDAMNBBF34sYIQ6LplCnUgAyDIkg4RNiE2MTZBNlMdYx1z6wCQAioAkAplAHGjNk"
    "J7AJAANmJLAJAANlMOBIJAOJQ2IMMgGgCQAg4kgkAYtYJQKJDDUBoAkAIOUMNlNjY2Qg4SDlH9Yf"
    "1xqwCQAY2gHgAxomT/Zr9mr2afZoCwAJABXRQ2IeIhoBKUEJQQFBE2AIQBwwDDBDYggyE2QLACNg"
    "E9ALIRImCyIhFgsjMhYLJEMWCyVUFgHgCwACJ8AAyAC0AEQACQBLDJx8BAyY0gQMAPgAAKuqAADN"
    "zEgMYEtODLitSAzoSk4MsK0AAACAgIAAgEgMxFcKDCDfmAC0AAAAAAD/ABAO/w3///////8AAAAA"
    "//////////8AAAAA//////////8AAAAA//////////8AAAAA//////////8LDPASmAC0AAAAAAD/"
    "ABAO/wD///////8AAAAA//////////8AAAAA//////////8AAAAA//////////8AAAAA////////"
    "//8LDPCfmAC0AAAAAAABADAq/wD///////8AAAAA//////////8AAAAA//////////8AAAAA////"
    "//////8AAAAA//////////8LDDDTVAC0AAAAAAABAKQfMzL///////8DADAqIyIlJP////8FACAc"
    "/wX///////8AAAAA//////////8AAAAA//////////8MDLAcmAC0AAAAAAABADAq/wD///////8B"
    "ASAc/wH///////8AAAAA//////////8AAAAA//////////8AAAAA//////////8MDLBnVAC0AAAA"
    "AAABAKQf/z7///////8DADAq/zD///////8FACAc/wD///////8AAAAA//////////8AAAAA////"
    "//////8MDKC5mAC0AAAAAAABABAO/zj///////8DADAq/xr///////8FADAq/wD///////8CKjAq"
    "/yr///////8AAAAA//////////8KDMD5mAC0AAEAAAABAAUM/wD///////8AAAAA//////////8A"
    "AAAA//////////8AAAAA//////////8AAAAA//////////8LDHAvmAC0AAEAAIABABIM/wD/////"
    "//8AAAAA//////////8AAAAA//////////8AAAAA//////////8AAAAA//////////8LDFBLmAC0"
    "AAEAAAABAFAK/wD///////8AAAAA//////////8AAAAA//////////8AAAAA//////////8AAAAA"
    "//////////8LDFCAmAC3AAEAAAABAB4P/wD///////8AAAAA//////////8AAAAA//////////8A"
    "AAAA//////////8AAAAA//////////8LDJBomAC0AAEAAAABACYW/wD///////8AAAAA////////"
    "//8AAAAA//////////8AAAAA//////////8AAAAA//////////8AAAAASFRTSVAgT1JFSlRDSSAA"
    "UwAAAAAAAAAAAAAAAHAgAIBOVUZPSUZJQ0xBQSBETkkgIFNPTgBUAAAAAAAAcCAAgEZBSUZJTFRB"
    "REVXIFRJLEhFIEROUk9FUwBEAABwIACAWUIgLFJPQSBUVU9ISVJFWiBEWUIAAAAAAAAAAHAgAIBB"
    "Q0VWIC5MQSBMSVJIR1NUVCAgT0hUAEUAAAAAcCAAgFJPR0lOSUxBRyBNQSBFTkEgRFRJAFMAAAAA"
    "AABwIACAU0FPU0lDVEFERUkgVE5MRUVMVENBVQBMAAAAAHAgAIBSUFBPUkVZVFIgTUVJQSBOSVdI"
    "VAAAAAAAAAAAcCAAgEhUSUUgUkVSUFNDRUlURVZSIEdJVEgAUwAAAABwIACAT0hETFJFLlMAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAHAgAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcCAAgCAgICAg"
    "IEFIRVZGIE5VISEgISAgICAgIAAAAAAgcAAQMDI2MjEvLzAzMgAATVNLT0RFQiBDQU5PAAAAAE9O"
    "IFRPRiBSQVNFTAAAAAAGDEz8BgxwEAQMRMQGDJzSBgxwEAQMZMAGDETQBwzQewQMdMEGDATPE4tO"
    "2hOLAdAGDAjPoGAzyStACQAGDAzPAYgCjwQMgMAJDCgIEH8BcRB/B9AJDCwIHWBoiCtACQAJDEgI"
    "CQAJAAQM+MEHDMhqMmIoIh3UK0QHDMxqEI/zbvNuCQAHDEBrUQxMXAQM0MIJDMBlDNMwYgzTK0MJ"
    "DMRlKCILiwkAC4sJDPRlUQxMXAQMgMMHDIQBBwzQewQM0MMGDKh6DgykCQQM/NUGDLR6DQxY9gQM"
    "fNcGDMR6DgwkCwQMiNcGDNR5NtgF5jbYBOYGDCB6KNQQ5ijUD+YGDDjQDgyoDwQMmNcHDKiFTAET"
    "YEwBc9MHDKyFIMkIICtDE2AHDHiHCQAJAAQMKMIODCQrCAzg+AQMdMIODEQrCAwA/AQMesIODGQr"
    "CAzA/AQMgMIODIQrCAwg/wQMhsIODMQrCQwAAAQMMMgHDACDc2BAyXNgKtAHDASDCCBJiStAc2AH"
    "DKyDCQAJAAQM5McGDJT5cmD/iLjQK0AGDJj5a40A6gkAAOoHDJhFBwzw3QQMjMcHDPxIBwzw3QQM"
    "jMcGDHj8CQAJAAQMCMYNDCh1Tgw8rAQMiPgAAAAA")),
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
        <part name="bacon_u4" crc="77f63093"/>
        <part name="bacon_u4" crc="77f63093"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 56)")
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
