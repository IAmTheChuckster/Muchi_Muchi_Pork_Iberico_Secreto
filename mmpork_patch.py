#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 20

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 8ab3ab56.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x8AB3AB56
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "BtRGYRghBolGZUZmEmJQMveL9q9iIQLQK0AJAB+AxAsGDNADAeAD0QIhA9ECIQPQK0AJAEgMrCRO"
    "DECsBgxwECTREmMzZSTSIGADYgHIA4n/cxFDAIkA4yNgAsgEiQFzBOAHMwCLBOMyITNgBIgJiy3H"
    "A2YM53/kZmIgYEkgACIQR/mLAOIb1iPXM2ADiAKLAeIZ1iHXH9ByIBXQIiAA4iEQFtBiIBbQYiAw"
    "NQKJDNALQCXkCdoH0RJgAYgEiQKIBYkI0CtACQAH0CtACQAH0CtACQAEDCT4SAw8H0gM/B4IDMCM"
    "BgwczwYMINcGDHDXBAwo+A4MuCcfgAQBBwxIhgcMGIgOCgAMFhAHBwBQAAACAQIBCAwwCw4MEDEf"
    "gCABAAAAAAAAAABIDPgdSAz5HUgMOB5IDDkeSAx4HkgMeR5IDPweSAz9HkgMPB9IDD0fSAx8H0gM"
    "fR8S0RJjFccDZRHSEtcA5CDgMDQAiz7geyACIiDgeyABEiNmCHYI4VRgeyACJhBB+o8EdohyAXRD"
    "YAWI6IsG0gHgAiICEgQSBhILAAgSBAwk+EgMPEUwYACATgwwrVJBQUNFRCAgQUhBUkFIQVJBTVBO"
    "S1UgVTFWMC4rMSAgUkFBUkdOIEUI0AJgCCAAiQFxAXFo4AMxA4kRLATQK0AJAANhESwD0CtACQAE"
    "DCj4CQw0CAkMUAggyBeLDdIiYigiDYlCYhmTOCIDixmQTAIoIgWJE5BNAhKQJQQHoAHjE2AQyADj"
    "AokBoAHjAOMC0itCCQAEDCj4Bwy+hQAgDgISAgoCEtAJoAkAEtAGoAkAEdADoAkAEdAAoAkAC9ES"
    "YRghAYsrQAkAhi+WL6YvIk9DaFNpA2oLSgkAg2QLSpNlJk/2avZpCwD2aAkABAwo+AgM4PgIDAD8"
    "CAzA/AgMIP8c0iJiKCIMizJiKCIGixvUQGIoIgKLGtIrQgkAGdIrQgkAFdZiYACICokBiA2JAOAZ"
    "0gIiGdIAIhnSACLurwkAAeACJjJlCqABdQLgAiYB4BHSAiIR0gAiEdIAIgDlCtT/4QjnCdZyJgnQ"
    "C0BSJAnQK0AJAAQMKPgEDCz4UQxMXAcM2GoHDPBqSAwcIEgMmPUHDLABBwz6ak4MPKxIDH8iUQzc"
    "bwrTMmM4IwaLCtMwYigiCosJ0ytDCQAG0zJjAuIiMwKJB9MrQwkABdMrQwkABAwo+AQMLPhRDExc"
    "CQzIZQkM4GUJDORlD9ACYAggGIke4A4lGgFsMQhBDNIcMg/HA2ML1wjhNGB7IAIiEEH6jwRyU2AI"
    "QAwwBtIMMgHgCwACIgXQK0AJAAQMKPhIDFA6MGAAgE4MmKwHDNB7MVYwLisxICAA4ArRAiEiT0Yv"
    "Vi9mL3YvBdALQAkA9mf2ZvZl9mQmTwPQK0AJAAkAH4AsBAQMJPgGDHAQhi+WL6Yvti8iT5XaAOAI"
    "GpHZYOu8O5JgCCAJiZFRj9iCYigiBIkQMimJSHj4rwkAZOAMMAw5EEvti4naqFAIIACLBBoA4Aca"
    "o1AIIAGL2aAJAADgAxog4RNiE2MTZBNlgtaD1+WwCQAg4RNiE2MTZBNlgNaA19ywCQDDoAkAeNqk"
    "UIAwAYsB4AgagoUNYJ4Gn4QDYoOFnAODYQxxEYUNZVglDIkQYP+IAYkgMASLEYT/iAaJMDAEiQxx"
    "768JALevCQBn2hYahIUIIAqJZNpt0AJnpFCAMAGJhBp1GqVQc2YINlNhaDERQQOJhIUIIJ+JAOFc"
    "0A4hGgEpQQlBE2SIsAkAA2eFsAkAA2aCsAkAA2JDYzDgOCMCiQwzAaAJACDjIOEQMwGLKCICiQwy"
    "AaAJACDiDDYMNzNhY2Mu5HNlS9ZL13awCQBG2qZXBHeCYgDjAOFB1GDlXDVCYAggF4lBUCAwFItP"
    "hANmc2mUYP+IDolgMPqLhYUNYAggAolCZggmBYkBcUTgTQARQACLDDNk4AwwDDQQRd+LGCEOi6ZQ"
    "p1IAMgyJIOETYhNjE2QTZTHWMdc+sAkAIqAJAKZQBxozZCewCQADZiSwCQADZTDgSCQDiUNiDDIB"
    "oAkAIOJIJAGLWCUCiQw1AaAJACDlDDZTY2NkIOEg5R/WH9casAkAGNoB4AMaJk/2a/Zq9mn2aAsA"
    "CQAV0UNiHiIaASlBCUEBQRNgCEAcMAwwQ2IIMhNkCwAjYBPQCyESJgsiIRYLIzIWCyRDFgslVBYB"
    "4AsAAifAAMgAtABEAAkASwycfB+AtAYEDAD4AACrqgAAzcxIDGBLTgy4rUgM6EpODLCtAAAAgICA"
    "AIBIDMRXCgwg35gAtAAAAAAA/wAQDv8N////////AAAAAP//////////AAAAAP//////////AAAA"
    "AP//////////AAAAAP//////////CwzwEpgAtAAAAAAA/wAQDv8A////////AAAAAP//////////"
    "AAAAAP//////////AAAAAP//////////AAAAAP//////////Cwzwn5gAtAAAAAAAAQAwKv8A////"
    "////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////Cwww01QA"
    "tAAAAAAAAQCkHzMy////////AwAwKiMiJST/////BQAgHP8F////////AAAAAP//////////AAAA"
    "AP//////////DAywHJgAtAAAAAAAAQAwKv8A////////AQEgHP8B////////AAAAAP//////////"
    "AAAAAP//////////AAAAAP//////////DAywZ1QAtAAAAAAAAQCkH/8+////////AwAwKv8w////"
    "////BQAgHP8A////////AAAAAP//////////AAAAAP//////////DAyguZgAtAAAAAAAAQAQDv84"
    "////////AwAwKv8a////////BQAwKv8A////////AiowKv8q////////AAAAAP//////////CgzA"
    "+ZgAtAABAAAAAQAFDP8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////"
    "AAAAAP//////////CwxwL5gAtAABAACAAQASDP8A////////AAAAAP//////////AAAAAP//////"
    "////AAAAAP//////////AAAAAP//////////CwxQS5gAtAABAAAAAQBQCv8A////////AAAAAP//"
    "////////AAAAAP//////////AAAAAP//////////AAAAAP//////////CwxQgJgAtwABAAAAAQAe"
    "D/8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////////AAAAAP//////////"
    "CwyQaJgAtAABAAAAAQAmFv8A////////AAAAAP//////////AAAAAP//////////AAAAAP//////"
    "////AAAAAP//////////AAAAAEhUU0lQIE9SRUpUQ0kgAFMAAAAAAAAAAAAAAABwIACATlVGT0lG"
    "SUNMQUEgRE5JICBTT04AVAAAAAAAAHAgAIBGQUlGSUxUQURFVyBUSSxIRSBETlJPRVMARAAAcCAA"
    "gFlCICxST0EgVFVPSElSRVogRFlCAAAAAAAAAABwIACAQUNFViAuTEEgTElSSEdTVFQgIE9IVABF"
    "AAAAAHAgAIBST0dJTklMQUcgTUEgRU5BIERUSQBTAAAAAAAAcCAAgFNBT1NJQ1RBREVJIFROTEVF"
    "TFRDQVUATAAAAABwIACAUlBQT1JFWVRSIE1FSUEgTklXSFQAAAAAAAAAAHAgAIBIVElFIFJFUlBT"
    "Q0VJVEVWUiBHSVRIAFMAAAAAcCAAgE9IRExSRS5TAAAAAAAAAAAAAAAAAAAAAAAAAABwIACAAAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHAgAIAgICAgICBBSEVWRiBOVSEhICEgICAgICAAAAAA"
    "IHAAEDAyNjIxLy8wMzIAAE1TS09ERUIgQ0FOTwAAAABPTiBUT0YgUkFTRUwAAAAABgxM/AYMcBAf"
    "gPgDBgyc0gYMcBAfgCQABgxE0AcM0HsfgFgBBgwEzxOLTtoTiwHQBgwIz6BgM8krQAkABgwMzwGI"
    "Ao8fgEAACQwoCBB/AXEQfwfQCQwsCB1gaIgrQAkACQxICAkACQAfgNwBBwzIajJiKCId1CtEBwzM"
    "ahCP827zbgkABwxAa1EMTFwfgLQCCQzAZQzTMGIM0ytDCQzEZSgiC4sJAAuLCQz0ZVEMTFwfgFgD"
    "BwyEAQcM0HsfgJwDBgyoeg4MpAkfgBgKBgy0eg0MWPYfgJgLBgzEeg4MJAsfgKQLBgzUeTbYBeY2"
    "2ATmBgwgeijUEOYo1A/mBgw40A4MqA8fgLQLBwyohUwBE2BMAXPTBwyshSDJCCArQxNgBwx4hwkA"
    "CQAfgAwCDgwkKwgM4PgfgFgCDgxEKwgMAPwfgF4CDgxkKwgMwPwfgGQCDgyEKwgMIP8fgGoCAAAA"
    "AA==")),
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
        <part name="bacon_u4" crc="8ab3ab56"/>
        <part name="bacon_u4" crc="8ab3ab56"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 20)")
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
