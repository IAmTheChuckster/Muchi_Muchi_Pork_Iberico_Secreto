#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 42

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be cd8312da.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0xCD8312DA
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "KYlIePivCQBk4AwwDDkQS+2LidqoUAggAIsEGgDgBxqjUAggAYvZoAkAAOADGiDhE2ITYxNkE2WC"
    "1oPX5bAJACDhE2ITYxNkE2WA1oDX3LAJAMOgCQB42qRQgDABiwHgCBqChQ1gngafhANig4WcA4Nh"
    "DHERhQ1lWCUMiRBg/4gBiSAwBIsRhP+IBokwMASJDHHvrwkAt68JAGfaFhqEhQggColk2m3QAmek"
    "UIAwAYmEGnUapVBzZgg2U2FoMRFBA4mEhQggn4kA4VzQDiEaASlBCUETZIiwCQADZ4WwCQADZoKw"
    "CQADYkNjMOA4IwKJDDMBoAkAIOMg4RAzAYsoIgKJDDIBoAkAIOIMNgw3M2FjYy7kc2VL1kvXdrAJ"
    "AEbaplcEd4JiAOMA4UHUYOVcNUJgCCAXiUFQIDAUi0+EA2ZzaZRg/4gOiWAw+ouFhQ1gCCACiUJm"
    "CCYFiQFxROBNABFAAIsMM2TgDDAMNBBF34sYIQ6LplCnUgAyDIkg4RNiE2MTZBNlMdYx1z6wCQAi"
    "oAkAplAHGjNkJ7AJAANmJLAJAANlMOBIJAOJQ2IMMgGgCQAg4kgkAYtYJQKJDDUBoAkAIOUMNlNj"
    "Y2Qg4SDlH9Yf1xqwCQAY2gHgAxomT/Zr9mr2afZoCwAJABXRQ2IeIhoBKUEJQQFBE2AIQBwwDDBD"
    "YggyE2QLACNgE9ALIRImCyIhFgsjMhYLJEMWCyVUFgHgCwACJ8AAyAC0AEQACQBLDJx8H4C8DwQM"
    "APgAAKuqAADNzEgMYEtODLitSAzoSk4MsK0AAACAgIAAgEgMxFcKDCDfmAC0AAAAAAD/ABAO/w3/"
    "//////8AAAAA//////////8AAAAA//////////8AAAAA//////////8AAAAA//////////8LDPAS"
    "mAC0AAAAAAD/ABAO/wD///////8AAAAA//////////8AAAAA//////////8AAAAA//////////8A"
    "AAAA//////////8LDPCfmAC0AAAAAAABADAq/wD///////8AAAAA//////////8AAAAA////////"
    "//8AAAAA//////////8AAAAA//////////8LDDDTVAC0AAAAAAABAKQfMzL///////8DADAqIyIl"
    "JP////8FACAc/wX///////8AAAAA//////////8AAAAA//////////8MDLAcmAC0AAAAAAABADAq"
    "/wD///////8BASAc/wH///////8AAAAA//////////8AAAAA//////////8AAAAA//////////8M"
    "DLBnVAC0AAAAAAABAKQf/z7///////8DADAq/zD///////8FACAc/wD///////8AAAAA////////"
    "//8AAAAA//////////8MDKC5mAC0AAAAAAABABAO/zj///////8DADAq/xr///////8FADAq/wD/"
    "//////8CKjAq/yr///////8AAAAA//////////8KDMD5mAC0AAEAAAABAAUM/wD///////8AAAAA"
    "//////////8AAAAA//////////8AAAAA//////////8AAAAA//////////8LDHAvmAC0AAEAAIAB"
    "ABIM/wD///////8AAAAA//////////8AAAAA//////////8AAAAA//////////8AAAAA////////"
    "//8LDFBLmAC0AAEAAAABAFAK/wD///////8AAAAA//////////8AAAAA//////////8AAAAA////"
    "//////8AAAAA//////////8LDFCAmAC3AAEAAAABAB4P/wD///////8AAAAA//////////8AAAAA"
    "//////////8AAAAA//////////8AAAAA//////////8LDJBomAC0AAEAAAABACYW/wD///////8A"
    "AAAA//////////8AAAAA//////////8AAAAA//////////8AAAAA//////////8AAAAASFRTSVAg"
    "T1JFSlRDSSAAUwAAAAAAAAAAAAAAAHAgAIBOVUZPSUZJQ0xBQSBETkkgIFNPTgBUAAAAAAAAcCAA"
    "gEZBSUZJTFRBREVXIFRJLEhFIEROUk9FUwBEAABwIACAWUIgLFJPQSBUVU9ISVJFWiBEWUIAAAAA"
    "AAAAAHAgAIBBQ0VWIC5MQSBMSVJIR1NUVCAgT0hUAEUAAAAAcCAAgFJPR0lOSUxBRyBNQSBFTkEg"
    "RFRJAFMAAAAAAABwIACAU0FPU0lDVEFERUkgVE5MRUVMVENBVQBMAAAAAHAgAIBSUFBPUkVZVFIg"
    "TUVJQSBOSVdIVAAAAAAAAAAAcCAAgEhUSUUgUkVSUFNDRUlURVZSIEdJVEgAUwAAAABwIACAT0hE"
    "TFJFLlMAAAAAAAAAAAAAAAAAAAAAAAAAAHAgAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "cCAAgCAgICAgIEFIRVZGIE5VISEgISAgICAgIAAAAAAgcAAQMDI2MjEvLzAzMgAATVNLT0RFQiBD"
    "QU5PAAAAAE9OIFRPRiBSQVNFTAAAAAAGDEz8BgxwEB+A7AMGDJzSBgxwEB+AJAAGDETQBwzQex+A"
    "NAEGDATPE4tO2hOLAdAGDAjPoGAzyStACQAGDAzPAYgCjx+AQAAJDCgIEH8BcRB/B9AJDCwIHWBo"
    "iCtACQAJDEgICQAJAB+AuAEHDMhqMmIoIh3UK0QHDMxqEI/zbvNuCQAHDEBrUQxMXB+AkAIJDMBl"
    "DNMwYgzTK0MJDMRlKCILiwkAC4sJDPRlUQxMXB+ANAMHDIQBBwzQex+AeAMGDKh6DgykCR+AIBMG"
    "DLR6DQxY9h+AoBQGDMR6DgwkCx+ArBQGDNR5NtgF5jbYBOYGDCB6KNQQ5ijUD+YGDDjQDgyoDx+A"
    "vBQHDKiFTAETYEwBc9MHDKyFIMkIICtDE2AHDHiHCQAJAB+A6AEODCQrCAzg+B+ANAIODEQrCAwA"
    "/B+AOgIODGQrCAzA/B+AQAIODIQrCAwg/x+ARgIODMQrCQwAAB+ANAcHDACDc2BAyXNgKtAHDASD"
    "CCBJiStAc2AHDKyDCQAJAB+A6AYGDJT5cmD/iLjQK0AGDJj5a40A6gkAAOoHDJhFBwzw3R+AkAYH"
    "DPxIBwzw3R+AkAYGDHj8CQAJAB+ARAUAAAAA")),
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
        <part name="bacon_u4" crc="cd8312da"/>
        <part name="bacon_u4" crc="cd8312da"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 42)")
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
