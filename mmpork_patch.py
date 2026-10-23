#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 51

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 4a588c13.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x4A588C13
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "AANmJLAJAANlMOBIJAOJQ2IMMgGgCQAg4kgkAYtYJQKJDDUBoAkAIOUMNlNjY2Qg4SDlH9Yf1xqw"
    "CQAY2gHgAxomT/Zr9mr2afZoCwAJABXRQ2IeIhoBKUEJQQFBE2AIQBwwDDBDYggyE2QLACNgE9AL"
    "IRImCyIhFgsjMhYLJEMWCyVUFgHgCwACJ8AAyAC0AEQACQBLDJx8H4B4EQQMAPgAAKuqAADNzEgM"
    "YEtODLitSAzoSk4MsK0AAACAgIAAgEgMxFcKDCDfmAC0AAAAAAD/ABAO/w3///////8AAAAA////"
    "//////8AAAAA//////////8AAAAA//////////8AAAAA//////////8LDPASmAC0AAAAAAD/ABAO"
    "/wD///////8AAAAA//////////8AAAAA//////////8AAAAA//////////8AAAAA//////////8L"
    "DPCfmAC0AAAAAAABADAq/wD///////8AAAAA//////////8AAAAA//////////8AAAAA////////"
    "//8AAAAA//////////8LDDDTVAC0AAAAAAABAKQfMzL///////8DADAqIyIlJP////8FACAc/wX/"
    "//////8AAAAA//////////8AAAAA//////////8MDLAcmAC0AAAAAAABADAq/wD///////8BASAc"
    "/wH///////8AAAAA//////////8AAAAA//////////8AAAAA//////////8MDLBnVAC0AAAAAAAB"
    "AKQf/z7///////8DADAq/zD///////8FACAc/wD///////8AAAAA//////////8AAAAA////////"
    "//8MDKC5mAC0AAAAAAABABAO/zj///////8DADAq/xr///////8FADAq/wD///////8CKjAq/yr/"
    "//////8AAAAA//////////8KDMD5mAC0AAEAAAABAAUM/wD///////8AAAAA//////////8AAAAA"
    "//////////8AAAAA//////////8AAAAA//////////8LDHAvmAC0AAEAAIABABIM/wD///////8A"
    "AAAA//////////8AAAAA//////////8AAAAA//////////8AAAAA//////////8LDFBLmAC0AAEA"
    "AAABAFAK/wD///////8AAAAA//////////8AAAAA//////////8AAAAA//////////8AAAAA////"
    "//////8LDFCAmAC3AAEAAAABAB4P/wD///////8AAAAA//////////8AAAAA//////////8AAAAA"
    "//////////8AAAAA//////////8LDJBomAC0AAEAAAABACYW/wD///////8AAAAA//////////8A"
    "AAAA//////////8AAAAA//////////8AAAAA//////////8AAAAASFRTSVAgT1JFSlRDSSAAUwAA"
    "AAAAAAAAAAAAAHAgAIBOVUZPSUZJQ0xBQSBETkkgIFNPTgBUAAAAAAAAcCAAgEZBSUZJTFRBREVX"
    "IFRJLEhFIEROUk9FUwBEAABwIACAWUIgLFJPQSBUVU9ISVJFWiBEWUIAAAAAAAAAAHAgAIBBQ0VW"
    "IC5MQSBMSVJIR1NUVCAgT0hUAEUAAAAAcCAAgFJPR0lOSUxBRyBNQSBFTkEgRFRJAFMAAAAAAABw"
    "IACAU0FPU0lDVEFERUkgVE5MRUVMVENBVQBMAAAAAHAgAIBSUFBPUkVZVFIgTUVJQSBOSVdIVAAA"
    "AAAAAAAAcCAAgEhUSUUgUkVSUFNDRUlURVZSIEdJVEgAUwAAAABwIACAT0hETFJFLlMAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAHAgAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcCAAgCAgICAgIEFI"
    "RVZGIE5VISEgISAgICAgIAAAAAAgcAAQMDI2MjEvLzAzMgAATVNLT0RFQiBDQU5PAAAAAE9OIFRP"
    "RiBSQVNFTAAAAAAGDEz8BgxwEB+AHAQGDJzSBgxwEB+APAAGDETQBwzQex+ATAEGDATPE4tO2hOL"
    "AdAGDAjPoGAzyStACQAGDAzPAYgCjx+AWAAJDCgIEH8BcRB/B9AJDCwIHWBoiCtACQAJDEgICQAJ"
    "AB+A0AEHDMhqMmIoIh3UK0QHDMxqEI/zbvNuCQAHDEBrUQxMXB+AqAIJDMBlDNMwYgzTK0MJDMRl"
    "KCILiwkAC4sJDPRlUQxMXB+AWAMHDIQBBwzQex+AqAMGDKh6DgykCR+A3BQGDLR6DQxY9h+AXBYG"
    "DMR6DgwkCx+AaBYGDNR5NtgF5jbYBOYGDCB6KNQQ5ijUD+YGDDjQDgyoDx+AeBYHDKiFTAETYEwB"
    "c9MHDKyFIMkIICtDE2AHDHiHCQAJAB+AAAIODCQrCAzg+B+ATAIODEQrCAwA/B+AUgIODGQrCAzA"
    "/B+AWAIODIQrCAwg/x+AXgIODMQrCQwAAB+AgAcHDACDc2BAyXNgKtAHDASDCCBJiStAc2AHDKyD"
    "CQAJAB+ANAcGDJT5cmD/iLjQK0AGDJj5a40A6gkAAOoHDJhFBwzw3R+A3AYHDPxIBwzw3R+A3AYG"
    "DHj8CQAJAB+AfAUNDCh1Tgw8rAQMiPgAAAAA")),
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
        <part name="bacon_u4" crc="4a588c13"/>
        <part name="bacon_u4" crc="4a588c13"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 51)")
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
