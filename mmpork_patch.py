#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 44

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 7cb1dd18.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x7CB1DD18
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "DDgQSemLJk8LAAkATgz4xg0MAAAODAAAAAGQADPQAmAz0RIwB4kz0AJgCCADizLRAOALAAIhIk8v"
    "0RJqAeACIS7YAOmDZ0B3gmAIIAGLCaACJ3JgCCAFiwHgAieoKgGJCLAJAAF5S5ACOeuPXHgmTwsA"
    "CQCTYkSQAjkDi0KQAjkAiz2Qg2MBcgIyLYlcczJhGCH4i4NkM2UX5kZhEiUQRvuPBHUzZ0B3AeAC"
    "JzpUO1VDZmw2TDZjYQhBHDEcNvvhHEZTZ/3hHEd4NmoTU2ZsNlw2Y2EIQRwxHDb74RxGQ2f94RxH"
    "fDZrEwsACQAEDDT4AAAQJwQMOPgEDIT4TAwcNwAGgAEAAgkAhi+WL6Yvti8iT5XaAOAIGpHZYOu8"
    "O5JgCCAJiZFRj9iCYigiBIkQMimJSHj4rwkAZOAMMAw5EEvti4naqFAIIACLBBoA4Acao1AIIAGL"
    "2aAJAADgAxog4RNiE2MTZBNlgtaD1+WwCQAg4RNiE2MTZBNlgNaA19ywCQDDoAkAeNqkUIAwAYsB"
    "4AgagoUNYJ4Gn4QDYoOFnAODYQxxEYUNZVglDIkQYP+IAYkgMASLEYT/iAaJMDAEiQxx768JALev"
    "CQBn2hYahIUIIAqJZNpt0AJnpFCAMAGJhBp1GqVQc2YINlNhaDERQQOJhIUIIJ+JAOFc0A4hGgEp"
    "QQlBE2SIsAkAA2eFsAkAA2aCsAkAA2JDYzDgOCMCiQwzAaAJACDjIOEQMwGLKCICiQwyAaAJACDi"
    "DDYMNzNhY2Mu5HNlS9ZL13awCQBG2qZXBHeCYgDjAOFB1GDlXDVCYAggF4lBUCAwFItPhANmc2mU"
    "YP+IDolgMPqLhYUNYAggAolCZggmBYkBcUTgTQARQACLDDNk4AwwDDQQRd+LGCEOi6ZQp1IAMgyJ"
    "IOETYhNjE2QTZTHWMdc+sAkAIqAJAKZQBxozZCewCQADZiSwCQADZTDgSCQDiUNiDDIBoAkAIOJI"
    "JAGLWCUCiQw1AaAJACDlDDZTY2NkIOEg5R/WH9casAkAGNoB4AMaJk/2a/Zq9mn2aAsACQAV0UNi"
    "HiIaASlBCUEBQRNgCEAcMAwwQ2IIMhNkCwAjYBPQCyESJgsiIRYLIzIWCyRDFgslVBYB4AsAAifA"
    "AMgAtABEAAkASwycfB+A7BAEDAD4AACrqgAAzcxIDGBLTgy4rUgM6EpODLCtAAAAgICAAIBIDMRX"
    "Cgwg35gAtAAAAAAA/wAQDv8N////////AAAAAP//////////AAAAAP//////////AAAAAP//////"
    "////AAAAAP//////////CwzwEpgAtAAAAAAA/wAQDv8A////////AAAAAP//////////AAAAAP//"
    "////////AAAAAP//////////AAAAAP//////////Cwzwn5gAtAAAAAAAAQAwKv8A////////AAAA"
    "AP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////Cwww01QAtAAAAAAA"
    "AQCkHzMy////////AwAwKiMiJST/////BQAgHP8F////////AAAAAP//////////AAAAAP//////"
    "////DAywHJgAtAAAAAAAAQAwKv8A////////AQEgHP8B////////AAAAAP//////////AAAAAP//"
    "////////AAAAAP//////////DAywZ1QAtAAAAAAAAQCkH/8+////////AwAwKv8w////////BQAg"
    "HP8A////////AAAAAP//////////AAAAAP//////////DAyguZgAtAAAAAAAAQAQDv84////////"
    "AwAwKv8a////////BQAwKv8A////////AiowKv8q////////AAAAAP//////////CgzA+ZgAtAAB"
    "AAAAAQAFDP8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//"
    "////////CwxwL5gAtAABAACAAQASDP8A////////AAAAAP//////////AAAAAP//////////AAAA"
    "AP//////////AAAAAP//////////CwxQS5gAtAABAAAAAQBQCv8A////////AAAAAP//////////"
    "AAAAAP//////////AAAAAP//////////AAAAAP//////////CwxQgJgAtwABAAAAAQAeD/8A////"
    "////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////CwyQaJgA"
    "tAABAAAAAQAmFv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAA"
    "AP//////////AAAAAEhUU0lQIE9SRUpUQ0kgAFMAAAAAAAAAAAAAAABwIACATlVGT0lGSUNMQUEg"
    "RE5JICBTT04AVAAAAAAAAHAgAIBGQUlGSUxUQURFVyBUSSxIRSBETlJPRVMARAAAcCAAgFlCICxS"
    "T0EgVFVPSElSRVogRFlCAAAAAAAAAABwIACAQUNFViAuTEEgTElSSEdTVFQgIE9IVABFAAAAAHAg"
    "AIBST0dJTklMQUcgTUEgRU5BIERUSQBTAAAAAAAAcCAAgFNBT1NJQ1RBREVJIFROTEVFTFRDQVUA"
    "TAAAAABwIACAUlBQT1JFWVRSIE1FSUEgTklXSFQAAAAAAAAAAHAgAIBIVElFIFJFUlBTQ0VJVEVW"
    "UiBHSVRIAFMAAAAAcCAAgE9IRExSRS5TAAAAAAAAAAAAAAAAAAAAAAAAAABwIACAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAHAgAIAgICAgICBBSEVWRiBOVSEhICEgICAgICAAAAAAIHAAEDAy"
    "NjIxLy8wMzIAAE1TS09ERUIgQ0FOTwAAAABPTiBUT0YgUkFTRUwAAAAABgxM/AYMcBAfgBwEBgyc"
    "0gYMcBAfgDwABgxE0AcM0HsfgEwBBgwEzxOLTtoTiwHQBgwIz6BgM8krQAkABgwMzwGIAo8fgFgA"
    "CQwoCBB/AXEQfwfQCQwsCB1gaIgrQAkACQxICAkACQAfgNABBwzIajJiKCId1CtEBwzMahCP827z"
    "bgkABwxAa1EMTFwfgKgCCQzAZQzTMGIM0ytDCQzEZSgiC4sJAAuLCQz0ZVEMTFwfgFgDBwyEAQcM"
    "0HsfgKgDBgyoeg4MpAkfgFAUBgy0eg0MWPYfgNAVBgzEeg4MJAsfgNwVBgzUeTbYBeY22ATmBgwg"
    "eijUEOYo1A/mBgw40A4MqA8fgOwVBwyohUwBE2BMAXPTBwyshSDJCCArQxNgBwx4hwkACQAfgAAC"
    "DgwkKwgM4PgfgEwCDgxEKwgMAPwfgFICDgxkKwgMwPwfgFgCDgyEKwgMIP8fgF4CDgzEKwkMAAAf"
    "gGQHBwwAg3NgQMlzYCrQBwwEgwggSYkrQHNgBwysgwkACQAfgBgHBgyU+XJg/4i40CtABgyY+WuN"
    "AOoJAADqBwyYRQcM8N0fgMAGBwz8SAcM8N0fgMAGBgx4/AkACQAfgHQFAAAAAA==")),
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
        <part name="bacon_u4" crc="7cb1dd18"/>
        <part name="bacon_u4" crc="7cb1dd18"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 44)")
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
