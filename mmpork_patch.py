#!/usr/bin/env python3
"""
Muchi Muchi Pork! Iberico Secreto (Cave CV1000) - patch build 61

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes iberico_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkibc.zip (the set with u4 replaced by iberico_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Iberico Secreto.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched iberico_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 1032b21e.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x1032B21E
U4_SIZE = 0x200000
OUT_NAME = "iberico_u4"
SET_NAME = "mmporkibc.zip"
MRA_NAME = "Muchi Muchi Pork! Iberico Secreto.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "IwKJDDMBoAkAIOMg4RAzAYsoIgKJDDIBoAkAIOIMNgw3M2FjYy7kc2VV1lbXjLAJAFDaplcEd4Ji"
    "AOMA4UvUYOVcNUJgCCAXiUFQIDAUi0+EA2ZzaZRg/4gOiWAw+ouFhQ1gCCACiUJmCCYFiQFxROBN"
    "ABFAAIsMM2TgDDAMNBBF34sYIQaLplCnUgAyDIkA5CygAOWmUKdSBxo91gAyAotiYiYzAIsyJjnW"
    "YmIA5CgiD4kzYQhBCEEIQUDlIjEDiygxAXQQRfmLSCQCizgjAIkB5DPVD+AGMwiLMNUzYAwwJjAD"
    "iyvVIjMAiSvVJ9YI5yDgFUQFiwjhEzQCjRfgQ2APcFsgAiYEdvh0EEfwiyXXAeACJxfaAeADGiZP"
    "9mv2avZp9mgLAAkAFNFDYh4iGgEpQQlBAUETYAhAHDAMMENiCDITZAsAI2AY0AshEiYLIiEWCyMy"
    "FgskQxYLJVQWAeALAAInwADIALQARABLDJx8BAxo0gQMAPgAAKuqAADNzEgM2EtODMCtSAxoS0gM"
    "XEsEDJj4gCAAIEAgAICAgAAAIIAAEE4MuK0AAACAgIAAgEgMxFcKDCDfmAC0AAAAAAD/ABAO/w3/"
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
    "cCAAgCAgICAgIEFIRVZGIE5VISEgISAgICAgIAAAAAAgcAAQMDI2MjEvLzA0MkkgRUJJUk9DUyBD"
    "RUVST1QAAAAAAABPTiBUT0YgUkFTRUwAAAAABgxM/AYMcBAEDNTDBgyc0gYMcBAEDGTABgxE0AcM"
    "0HsEDHTBBgwEzxOLTtoTiwHQBgwIz6BgM8krQAkABgwMzwGIAo8EDIDACQwoCBB/AXEQfwfQCQws"
    "CB1gaIgrQAkACQxICAkACQAEDPjBBwzIajJiKCId1CtEBwzMahCP827zbgkABwxAa1EMTFwEDNDC"
    "CQzAZQzTMGIM0ytDCQzEZSgiC4sJAAuLCQz0ZVEMTFwEDIDDBwyEAQcM0HsEDNDDBgyoeg4MpAkE"
    "DMzVBgy0eg0MWPYEDEzXBgzUeTbYBeY22ALmBgzEeg4MJAsEDGjXBgzUeTbYBeY22ATmBgwgeijU"
    "EOYo1A/mBgw40A4MqA8EDGzXBwyohUwBE2BMAXPTBwyshSDJCCArQxNgBwx4hwkACQAEDCjCDgwk"
    "KwgM4PgEDHTCDgxEKwgMAPwEDHrCDgxkKwgMwPwEDIDCDgyEKwgMIP8EDIbCDgzEKwkMAAAEDMDH"
    "BwwAg3NgQMlzYCrQBwwEgwggSYkrQHNgBwysgwkACQAEDHTHBgyU+XJg/4i40CtABgyY+WuNAOoJ"
    "AADqBwyYRQcM8N0EDBzHBwz8SAcM8N0EDBzHBgx4/AkACQAEDJjFDQwodU4MPKwEDIj4AAAAAA==")),
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
        <part name="iberico_u4" crc="1032b21e"/>
        <part name="iberico_u4" crc="1032b21e"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into iberico_u4 (Iberico Secreto, build 61)")
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
