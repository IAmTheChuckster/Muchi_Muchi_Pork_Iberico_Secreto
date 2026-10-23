#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 45

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be cd5a3108.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0xCD5A3108
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
    "CQAEDDj4BAww+AQMUPgGDJz5Bgxy+kwMHDcADBAjBAxw+FEM/AhODPjGBAyA+A0MAAAODAAA6AO8"
    "AvQBlgDeAwAGAAGQAA7QAmAIIBWJSCQTiw7REmAIIA2LCtACYAggBIsM0AJgDNIiMAaLWuACIQbR"
    "AeACIQsACQAF0CtACQAJAAQMMPgEDDj4BAxo+AQMbPgHDPDdBAw0+AAAECdAyA+JCtESYRghDokJ"
    "0RJhGCEEiwjREmAI0RIwBYsI0QHgAiEH0CtACQAH0CtACQAEDDD4BAw4+AQMNPgAABAnBAxo+AcM"
    "nIMHDAiDFdACYAggI4kU0AJgCCAfi3jgDiUaARPQDDESURLgBjEWiQhBE8cMMRJhEdMyYBwwAOEK"
    "4iIwAosoMPqvAXECIwfSImAcMAjRFjAAixNgAiIG0CtACQAJAAQMMPgEDDj4BAw0+FIMSLYAABAn"
    "CQwAAAQMVPgAAAMAAAAGAAAACQAAAAwAAAAPAAAAEgAAABUAAAAYAAAAGwAAAB4AAAA8AAAAWgAA"
    "AHgAAACWAAAAtAAAANIAAADwAAAADgEAACwBhi+WL6Yvti/GL9YvIk/50RJgCCALieXREmBu4RIw"
    "Bon30RBgQMgCidvRAeACIdjQAm3r0RJi0DIBi+qgCQDSIenQAGAIIAOJgIgBicCIAYvfoAkA0dES"
    "YAggAYn/cAIh4dzi0M4B4tIjYxYzAYn8rywzBHA2DMBgDGDG1mBhHGEAJs7iLGIgMQeLIDAZidPQ"
    "zABhgAHgFKBigCAwEYtihAggDokA4GKAYYQBcAThFzAAixNgydHMMRBiLGIHMgCJACHM27JgCCAW"
    "i8vREmDL0iIwOIuw0RJgCCA0iQDgAiEB4AIrwGC/0QAhu9Bo4RUMrtF54CegAiHAYLrREGIAMgKJ"
    "vdEOoAkAo9ESYAggBIkA4AIhuNEFoAkAt9ESYAriJjAOiQDgAiECK6XRAiGf0QIhnNF44AwwAiGY"
    "0VrgAqACISgwAiGBsQkAAOrCYLXRGCAFiaHQ9nDMAAggAIkB6rHYAOlk52R3gmAIIAOJgVAFiACL"
    "AXkQR/aPeHiq2ADrgmAIID+JgVAFiDyLmdACYAggBIuY0AJgmNESMAaLglASiAOJEuACGDuwCQCC"
    "UBKIKYmoKieJi1DHURcwI4uMUMhRGDCZ0RwwHDESMBuJs2AMMJfRDDERYtNjKDM9YwjiIjMQi9Eh"
    "glABcAIYGbAJAEDgAjkDiRuwCQAEoAkAg2QB5Xiw2SUBe2TgZHACO7ePeHgmT/Zt9mz2a/Zq9mkL"
    "APZoIk+D0AtAg2QmTwsACQAiT4HQC0AB5AggJIl/0AJleOAOJRoGeNAMNoNhY2Ie4xZgAiIQQ/uP"
    "BHJTYAwwdNEMMdEhAXlmL3XQC0BTZHTQC0CzZPZkPrAA5YNkO7AB5SZPCwAJAINkAeU0sNkl968J"
    "AFjREmAIIA2LV9ESYFfSIjAIiT7REmAIIBWJAOACIULRC6ASYDrREmAIIAyLAeACITvREmA90QIh"
    "AeA40QIhONEAITjRACELAAkARdESYRghAYs10RJgMdECITHRACEx0QsAACEiT0YvMtALQAkA8mQx"
    "0RkgMdEcMA0ULdALQAkA9mQv0RkgLdEcMFglAIkLYA4UJk8LAAkAIk9GL1YvQdALQAHk9mX2ZAgg"
    "JIk/0AJmZi944A4mGgc30Aw3PdACJwXgARcS4AIXAOADF0sXXBcNFw4Xdi8y0AtAc2T2Z/Zkdi8y"
    "0AtACQAS0AtACQAB5Qklt7/2ZCZPCwAJAAkASAzEVwQMRPgEDGj4BAxs+AQMdPgEDHj4BAIAAAQM"
    "fPhODDysSAx/IlEM3G8EDGD4Uwyk9AYMULQAAP//AgAAAAAAAIAAAP9/AAAOAgAAFAIEDDz4BAxA"
    "+FEMKAsAACgCyQGAwwQMOPgEDDT4AAAQJ0gMPB9IDPgdSAw4HkgMeB5IDPweSAw8H0gMfB9MDBw3"
    "UQz8CAAAACBSDEi2KAAAAAQMAPoIDEALBwyg9kwM7CQIDDATgMAEAAoCyAAiTyjREmAIIBaJ/3AC"
    "IQDqeIgpCiTYT5mCYAggB4kA4AIoqCoDiYhUiVVYvwkAEEnyj1x4QrAJAB3REmAIIC6J/3ACIQDq"
    "OJIgMCkKFtQzlUJgCCAdiU9TOCMFi6gqAosA4BagAiQI4/9zPxQ4IwKLAOAOoAIkM2IIQghCLDIf"
    "ciNmGEYrJgvSKyYA4AoUCxRsFBBF3I9cdADqD7AJACZPCwAJAAQMfPhMDBw3UQz8CAQMePgEAgAA"
    "AAbvACJPDdgemYJgCCAOiYFQC9ESMAqLCtESMAeJAOACKKgqA4mMVI1V/L4JAAyQDDgQSemLJk8L"
    "AAkATgz4xg0MAAAODAAAAAGQADPQAmAz0RIwB4kz0AJgCCADizLRAOALAAIhIk8v0RJqAeACIS7Y"
    "AOmDZ0B3gmAIIAGLCaACJ3JgCCAFiwHgAieoKgGJCLAJAAF5S5ACOeuPXHgmTwsACQCTYkSQAjkD"
    "i0KQAjkAiz2Qg2MBcgIyLYlcczJhGCH4i4NkM2UX5kZhEiUQRvuPBHUzZ0B3AeACJzpUO1VDZmw2"
    "TDZjYQhBHDEcNvvhHEZTZ/3hHEd4NmoTU2ZsNlw2Y2EIQRwxHDb74RxGQ2f94RxHfDZrEwsACQAE"
    "DDT4AAAQJwQMOPgEDIT4TAwcNwAGgAEAAgkAhi+WL6Yvti8iT5XaAOAIGpHZYOu8O5JgCCAJiZFR"
    "j9iCYigiBIkQMimJSHj4rwkAZOAMMAw5EEvti4naqFAIIACLBBoA4Acao1AIIAGL2aAJAADgAxog"
    "4RNiE2MTZBNlgtaD1+WwCQAg4RNiE2MTZBNlgNaA19ywCQDDoAkAeNqkUIAwAYsB4AgagoUNYJ4G"
    "n4QDYoOFnAODYQxxEYUNZVglDIkQYP+IAYkgMASLEYT/iAaJMDAEiQxx768JALevCQBn2hYahIUI"
    "IAqJZNpt0AJnpFCAMAGJhBp1GqVQc2YINlNhaDERQQOJhIUIIJ+JAOFc0A4hGgEpQQlBE2SIsAkA"
    "A2eFsAkAA2aCsAkAA2JDYzDgOCMCiQwzAaAJACDjIOEQMwGLKCICiQwyAaAJACDiDDYMNzNhY2Mu"
    "5HNlS9ZL13awCQBG2qZXBHeCYgDjAOFB1GDlXDVCYAggF4lBUCAwFItPhANmc2mUYP+IDolgMPqL"
    "hYUNYAggAolCZggmBYkBcUTgTQARQACLDDNk4AwwDDQQRd+LGCEOi6ZQp1IAMgyJIOETYhNjE2QT"
    "ZTHWMdc+sAkAIqAJAKZQBxozZCewCQADZiSwCQADZTDgSCQDiUNiDDIBoAkAIOJIJAGLWCUCiQw1"
    "AaAJACDlDDZTY2NkIOEg5R/WH9casAkAGNoB4AMaJk/2a/Zq9mn2aAsACQAV0UNiHiIaASlBCUEB"
    "QRNgCEAcMAwwQ2IIMhNkCwAjYBPQCyESJgsiIRYLIzIWCyRDFgslVBYB4AsAAifAAMgAtABEAAkA"
    "SwycfB+AHBEEDAD4AACrqgAAzcxIDGBLTgy4rUgM6EpODLCtAAAAgICAAIBIDMRXCgwg35gAtAAA"
    "AAAA/wAQDv8N////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//"
    "////////CwzwEpgAtAAAAAAA/wAQDv8A////////AAAAAP//////////AAAAAP//////////AAAA"
    "AP//////////AAAAAP//////////Cwzwn5gAtAAAAAAAAQAwKv8A////////AAAAAP//////////"
    "AAAAAP//////////AAAAAP//////////AAAAAP//////////Cwww01QAtAAAAAAAAQCkHzMy////"
    "////AwAwKiMiJST/////BQAgHP8F////////AAAAAP//////////AAAAAP//////////DAywHJgA"
    "tAAAAAAAAQAwKv8A////////AQEgHP8B////////AAAAAP//////////AAAAAP//////////AAAA"
    "AP//////////DAywZ1QAtAAAAAAAAQCkH/8+////////AwAwKv8w////////BQAgHP8A////////"
    "AAAAAP//////////AAAAAP//////////DAyguZgAtAAAAAAAAQAQDv84////////AwAwKv8a////"
    "////BQAwKv8A////////AiowKv8q////////AAAAAP//////////CgzA+ZgAtAABAAAAAQAFDP8A"
    "////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////Cwxw"
    "L5gAtAABAACAAQASDP8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////"
    "AAAAAP//////////CwxQS5gAtAABAAAAAQBQCv8A////////AAAAAP//////////AAAAAP//////"
    "////AAAAAP//////////AAAAAP//////////CwxQgJgAtwABAAAAAQAeD/8A////////AAAAAP//"
    "////////AAAAAP//////////AAAAAP//////////AAAAAP//////////CwyQaJgAtAABAAAAAQAm"
    "Fv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////"
    "AAAAAEhUU0lQIE9SRUpUQ0kgAFMAAAAAAAAAAAAAAABwIACATlVGT0lGSUNMQUEgRE5JICBTT04A"
    "VAAAAAAAAHAgAIBGQUlGSUxUQURFVyBUSSxIRSBETlJPRVMARAAAcCAAgFlCICxST0EgVFVPSElS"
    "RVogRFlCAAAAAAAAAABwIACAQUNFViAuTEEgTElSSEdTVFQgIE9IVABFAAAAAHAgAIBST0dJTklM"
    "QUcgTUEgRU5BIERUSQBTAAAAAAAAcCAAgFNBT1NJQ1RBREVJIFROTEVFTFRDQVUATAAAAABwIACA"
    "UlBQT1JFWVRSIE1FSUEgTklXSFQAAAAAAAAAAHAgAIBIVElFIFJFUlBTQ0VJVEVWUiBHSVRIAFMA"
    "AAAAcCAAgE9IRExSRS5TAAAAAAAAAAAAAAAAAAAAAAAAAABwIACAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAAAAHAgAIAgICAgICBBSEVWRiBOVSEhICEgICAgICAAAAAAIHAAEDAyNjIxLy8wMzIA"
    "AE1TS09ERUIgQ0FOTwAAAABPTiBUT0YgUkFTRUwAAAAABgxM/AYMcBAfgBwEBgyc0gYMcBAfgDwA"
    "BgxE0AcM0HsfgEwBBgwEzxOLTtoTiwHQBgwIz6BgM8krQAkABgwMzwGIAo8fgFgACQwoCBB/AXEQ"
    "fwfQCQwsCB1gaIgrQAkACQxICAkACQAfgNABBwzIajJiKCId1CtEBwzMahCP827zbgkABwxAa1EM"
    "TFwfgKgCCQzAZQzTMGIM0ytDCQzEZSgiC4sJAAuLCQz0ZVEMTFwfgFgDBwyEAQcM0HsfgKgDBgyo"
    "eg4MpAkfgIAUBgy0eg0MWPYfgAAWBgzEeg4MJAsfgAwWBgzUeTbYBeY22ATmBgwgeijUEOYo1A/m"
    "Bgw40A4MqA8fgBwWBwyohUwBE2BMAXPTBwyshSDJCCArQxNgBwx4hwkACQAfgAACDgwkKwgM4Pgf"
    "gEwCDgxEKwgMAPwfgFICDgxkKwgMwPwfgFgCDgyEKwgMIP8fgF4CDgzEKwkMAAAfgJgHBwwAg3Ng"
    "QMlzYCrQBwwEgwggSYkrQHNgBwysgwkACQAfgEwHBgyU+XJg/4i40CtABgyY+WuNAOoJAADqBwyY"
    "RQcM8N0fgPQGBwz8SAcM8N0fgPQGBgx4/AkACQAfgKgFDQwodU4MPKwEDIj4AAAAAA==")),
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
        <part name="bacon_u4" crc="cd5a3108"/>
        <part name="bacon_u4" crc="cd5a3108"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 45)")
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
