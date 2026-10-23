#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 47

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be f58a42f4.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0xF58A42F4
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "DNEZkgDgAiEQQvyPBHEH1EZhGCEGiUZlRmYSYlAy94v2r2IhAtArQAkACQAfgFAWBgzQAwQMAPgA"
    "AgkAAeAD0QIhA9ECIQPQK0AJAEgMrCRODECsBgxwECXREmMzZSXSIGADYgHIA4n/cxFDAIkA4yNg"
    "AsgEiQFzBOAHMwCLBOMyIQDiItYt1zNgA4gBiQSIAosB4h/WKtcl0HIgG9AiIADiIRAzYASIKQIi"
    "0CIgGtBiIBrQYiAwNQKJENALQCXkHdET4gDgAiEQQvyPBHEK2gfREmABiASJAogFiQjQK0AJAAjQ"
    "K0AJAAfQK0AJAAkABAwk+EgMPB9IDPweCAzAjAYMHM8GDCDXBgxw1wQMKPgODLgnH4AgAQcMSIYH"
    "DBiIDgoADBYQBwcAUAAAAgECAQgMMAsEDDD4BAw0+A4MEDEfgEQBAAAAAAAAAAAS0RJjFccDZRHS"
    "EtcA5CDgMDQAiz7geyACIiDgeyABEiNmCHYI4VRgeyACJhBB+o8EdohyAXRDYAWI6IsG0gHgAiIC"
    "EgQSBhILAAgSBAwk+EgMPEUwYACATgwwrVJBQUNFRCAgQUhBUkFIQVJBTVBOS1UgVTFWMC4rMSAg"
    "UkFBUkdOK0UI0AJgCCAAiQFxAXFo4AMxA4kRLATQK0AJAANhESwD0CtACQAEDCj4CQw0CAkMUAgg"
    "yBeLDdIiYigiDYlCYhmTOCIDixmQTAIoIgWJE5BNAhKQJQQHoAHjE2AQyADjAokBoAHjAOMC0itC"
    "CQAEDCj4Bwy+hQAgDgISAgoCEtAJoAkAEtAGoAkAEdADoAkAEdAAoAkAC9ESYRghAYsrQAkAhi+W"
    "L6YvIk9DaFNpA2oLSgkAg2QLSpNlJk/2avZpCwD2aAkABAwo+AgM4PgIDAD8CAzA/AgMIP8e0iJi"
    "KCIMizJiKCIGix7UQGIoIgKLHdIrQgkAHNIrQgkAGNZiYAgg+IsV1mJgAIgKifOvCQAA4BrSAiIa"
    "0gAiGtIAIuqvCQAB4AImMmUKoAF1AuACJgHgEtICIhLSACIS0gAiAOUL1P/hCOcK1nImCtALQFIk"
    "CtArQAkABAwo+AQMLPgEDDD4UQxMXAcM2GoHDPBqSAwcIEgMmPUHDLABBwz6ak4MPKxIDH8iUQzc"
    "bwzTMmM4IwaLDdMwYigiDosM0ytDCQAJ0zJjOCMHiwbTMmMB4iIzAokI0ytDCQAG0ytDCQAEDCj4"
    "BAws+AQMMPhRDExcCQzIZQkM4GUJDORlEtACYAggHYke4A4lGgFsMQhBD9IcMhPHA2MR0AJgCCAA"
    "iQhzC9cI4TRgeyACIhBB+o8EclNgCEAMMAfSDDIB4AsAAiIF0CtACQAJAAQMKPhIDFA6MGAAgE4M"
    "mKwHDNB7BAww+DFWMC4rMSAgUkFBUkdOK0UA4BfRAiEY0RJgAYgMiRfREmAIIAqJFtESYAggBIsW"
    "0RJgFtESMAGLAaAB4ADgEdECISJPRi9WL2Yvdi8G0AtACQAG0AtACQD2Z/Zm9mX2ZCZPBNArQAkA"
    "H4C4Dh+AnAQEDCT4BgxwEE4MPKwEDDD4BAw4+AQMiPgEDDT4AAAQJyrQAmAIIAGLCwAJACJPKNAL"
    "QAkAJk8vxwNmBud/5GZiIGBJIAAiEEf5iyPSJtc5xwNlBeFUYHsgAiIQQfqPBHIf0iPQC+ECIiNj"
    "eHMCIxBB+Y8EchfQAmMY0hzXI8cDZQrhAOZWZDDgQjMCi0gz+68BcANkMOAANAqLaCYJixNgAYgC"
    "iSDkBKAJADDkAaAJAAHmQ2B7IAIiEEHjjwRyCdIB4AIiAhIEEgsABhIEDDD4H4B8CAQMNPhIDOxM"
    "SAxwTEgMfEtODLitMGAAgICAAIBggCAgSAz5HUgMOR5IDHkeSAz9HkgMPR9IDH0fmjsAyvUFAOGY"
    "AICWDwBAQgEAoIYAABAnAADoAwAAZAAAAAoAAAABAEVGRVYAUgAARdACYAggdolE0AJgCCByiTYv"
    "Vi9F0aCVAOMSYAggAIkBcxBF+Y9ccUTRl5USYAggB4kRUETSIjADi0TSIjAAiQFzjJAMMRBF8Itk"
    "4AYzCYkzYiwyPDJ7kCgwfZInMAqJCaADYneQAjMEiZxzCENwkgGgODJukvZl9mMy0RJgCCACiWeS"
    "LtEiIS3REmAjZAY0BIn2cEcwBYkEoENgCnBHMACLQ2ACIQNiIdACYCHREmQCIUgwAeRCMACJAeAD"
    "5EYwAIsD4CNkEEABifyvTDIU0RJgLDAA4juUQjACi0gw+68BcgIhKCISiQLgBjIAiwNi/3IIoCIn"
    "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"
    "sAkAGNoB4AMaJk/2a/Zq9mn2aAsACQAV0UNiHiIaASlBCUEBQRNgCEAcMAwwQ2IIMhNkCwAjYBPQ"
    "CyESJgsiIRYLIzIWCyRDFgslVBYB4AsAAifAAMgAtABEAAkASwycfB+AQBEEDAD4AACrqgAAzcxI"
    "DGBLTgy4rUgM6EpODLCtAAAAgICAAIBIDMRXCgwg35gAtAAAAAAA/wAQDv8N////////AAAAAP//"
    "////////AAAAAP//////////AAAAAP//////////AAAAAP//////////CwzwEpgAtAAAAAAA/wAQ"
    "Dv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////"
    "Cwzwn5gAtAAAAAAAAQAwKv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////"
    "////AAAAAP//////////Cwww01QAtAAAAAAAAQCkHzMy////////AwAwKiMiJST/////BQAgHP8F"
    "////////AAAAAP//////////AAAAAP//////////DAywHJgAtAAAAAAAAQAwKv8A////////AQEg"
    "HP8B////////AAAAAP//////////AAAAAP//////////AAAAAP//////////DAywZ1QAtAAAAAAA"
    "AQCkH/8+////////AwAwKv8w////////BQAgHP8A////////AAAAAP//////////AAAAAP//////"
    "////DAyguZgAtAAAAAAAAQAQDv84////////AwAwKv8a////////BQAwKv8A////////AiowKv8q"
    "////////AAAAAP//////////CgzA+ZgAtAABAAAAAQAFDP8A////////AAAAAP//////////AAAA"
    "AP//////////AAAAAP//////////AAAAAP//////////CwxwL5gAtAABAACAAQASDP8A////////"
    "AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////CwxQS5gAtAAB"
    "AAAAAQBQCv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//"
    "////////CwxQgJgAtwABAAAAAQAeD/8A////////AAAAAP//////////AAAAAP//////////AAAA"
    "AP//////////AAAAAP//////////CwyQaJgAtAABAAAAAQAmFv8A////////AAAAAP//////////"
    "AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAEhUU0lQIE9SRUpUQ0kgAFMA"
    "AAAAAAAAAAAAAABwIACATlVGT0lGSUNMQUEgRE5JICBTT04AVAAAAAAAAHAgAIBGQUlGSUxUQURF"
    "VyBUSSxIRSBETlJPRVMARAAAcCAAgFlCICxST0EgVFVPSElSRVogRFlCAAAAAAAAAABwIACAQUNF"
    "ViAuTEEgTElSSEdTVFQgIE9IVABFAAAAAHAgAIBST0dJTklMQUcgTUEgRU5BIERUSQBTAAAAAAAA"
    "cCAAgFNBT1NJQ1RBREVJIFROTEVFTFRDQVUATAAAAABwIACAUlBQT1JFWVRSIE1FSUEgTklXSFQA"
    "AAAAAAAAAHAgAIBIVElFIFJFUlBTQ0VJVEVWUiBHSVRIAFMAAAAAcCAAgE9IRExSRS5TAAAAAAAA"
    "AAAAAAAAAAAAAAAAAABwIACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAgAIAgICAgICBB"
    "SEVWRiBOVSEhICEgICAgICAAAAAAIHAAEDAyNjIxLy8wMzIAAE1TS09ERUIgQ0FOTwAAAABPTiBU"
    "T0YgUkFTRUwAAAAABgxM/AYMcBAfgBwEBgyc0gYMcBAfgDwABgxE0AcM0HsfgEwBBgwEzxOLTtoT"
    "iwHQBgwIz6BgM8krQAkABgwMzwGIAo8fgFgACQwoCBB/AXEQfwfQCQwsCB1gaIgrQAkACQxICAkA"
    "CQAfgNABBwzIajJiKCId1CtEBwzMahCP827zbgkABwxAa1EMTFwfgKgCCQzAZQzTMGIM0ytDCQzE"
    "ZSgiC4sJAAuLCQz0ZVEMTFwfgFgDBwyEAQcM0HsfgKgDBgyoeg4MpAkfgKQUBgy0eg0MWPYfgCQW"
    "BgzEeg4MJAsfgDAWBgzUeTbYBeY22ATmBgwgeijUEOYo1A/mBgw40A4MqA8fgEAWBwyohUwBE2BM"
    "AXPTBwyshSDJCCArQxNgBwx4hwkACQAfgAACDgwkKwgM4PgfgEwCDgxEKwgMAPwfgFICDgxkKwgM"
    "wPwfgFgCDgyEKwgMIP8fgF4CDgzEKwkMAAAfgLwHBwwAg3NgQMlzYCrQBwwEgwggSYkrQHNgBwys"
    "gwkACQAfgHAHBgyU+XJg/4i40CtABgyY+WuNAOoJAADqBwyYRQcM8N0fgBgHBwz8SAcM8N0fgBgH"
    "Bgx4/AkACQAfgLgFDQwodU4MPKwEDIj4AAAAAA==")),
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
        <part name="bacon_u4" crc="f58a42f4"/>
        <part name="bacon_u4" crc="f58a42f4"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 47)")
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
