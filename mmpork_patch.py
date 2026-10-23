#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 36

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be c6584146.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0xC6584146
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "BtRGYRghBolGZUZmEmJQMveL9q9iIQLQK0AJAB+AzBMGDNADAeAD0QIhA9ECIQPQK0AJAEgMrCRO"
    "DECsBgxwECHREmMzZSHSIGADYgHIA4n/cxFDAIkA4yNgAsgEiQFzBOAHMwCLBOMyIQDiHtYo1zNg"
    "A4gBiQSIAosB4hvWJdch0HIgF9AiIADiIRAzYASIKQIe0CIgFtBiIBbQYiAwNQKJDNALQCXkCdoH"
    "0RJgAYgEiQKIBYkI0CtACQAH0CtACQAH0CtACQAEDCT4SAw8H0gM/B4IDMCMBgwczwYMINcGDHDX"
    "BAwo+A4MuCcfgPgABwxIhgcMGIgOCgAMFhAHBwBQAAACAQIBCAwwCwQMMPgODBAxH4AYAQAAAAAA"
    "AAAAEtESYxXHA2UR0hLXAOQg4DA0AIs+4HsgAiIg4HsgARIjZgh2COFUYHsgAiYQQfqPBHaIcgF0"
    "Q2AFiOiLBtIB4AIiAhIEEgYSCwAIEgQMJPhIDDxFMGAAgE4MMK1SQUFDRUQgIEFIQVJBSEFSQU1Q"
    "TktVIFUxVjAuKzEgIFJBQVJHTitFCNACYAggAIkBcQFxaOADMQOJESwE0CtACQADYREsA9ArQAkA"
    "BAwo+AkMNAgJDFAIIMgXiw3SImIoIg2JQmIZkzgiA4sZkEwCKCIFiROQTQISkCUEB6AB4xNgEMgA"
    "4wKJAaAB4wDjAtIrQgkABAwo+AcMvoUAIA4CEgIKAhLQCaAJABLQBqAJABHQA6AJABHQAKAJAAvR"
    "EmEYIQGLK0AJAIYvli+mLyJPQ2hTaQNqC0oJAINkC0qTZSZP9mr2aQsA9mgJAAQMKPgIDOD4CAwA"
    "/AgMwPwIDCD/HNIiYigiDIsyYigiBosb1EBiKCICixrSK0IJABnSK0IJABXWYmAAiAqJAYgNiQDg"
    "GdICIhnSACIZ0gAi7q8JAAHgAiYyZQqgAXUC4AImAeAR0gIiEdIAIhHSACIA5QrU/+EI5wnWciYJ"
    "0AtAUiQJ0CtACQAEDCj4BAws+FEMTFwHDNhqBwzwakgMHCBIDJj1BwywAQcM+mpODDysSAx/IlEM"
    "3G8K0zJjOCMGiwrTMGIoIgqLCdMrQwkABtMyYwLiIjMCiQfTK0MJAAXTK0MJAAQMKPgEDCz4UQxM"
    "XAkMyGUJDOBlCQzkZRLQAmAIIB2JHuAOJRoBbDEIQQ/SHDITxwNjEdACYAggAIkIcwvXCOE0YHsg"
    "AiIQQfqPBHJTYAhADDAH0gwyAeALAAIiBdArQAkACQAEDCj4SAxQOjBgAIBODJisBwzQewQMMPgx"
    "VjAuKzEgIFJBQVJHTitFAOAM0QIhIk9GL1YvZi92LwbQC0AJAAbQC0AJAPZn9mb2ZfZkJk8E0CtA"
    "CQAfgDQMH4AUBAQMJPgGDHAQKtACYAggAYsLAAkAIk8o0AtACQAmTy/HA2YG53/kZmIgYEkgACIQ"
    "R/mLI9Im1znHA2UF4VRgeyACIhBB+o8Ech/SI9AL4QIiI2N4cwIjEEH5jwRyF9ACYxjSHNcjxwNl"
    "CuEA5lZkMOBCMwKLSDP7rwFwA2Qw4AA0CotoJgmLE2ABiAKJIOQEoAkAMOQBoAkAAeZDYHsgAiIQ"
    "QeOPBHIJ0gHgAiICEgQSCwAGEgQMMPgfgDAHBAw0+EgM7ExIDHBMSAx8S04MuK0wYACAgIAAgGCA"
    "ICBIDPkdSAw5HkgMeR5IDP0eSAw9H0gMfR+aOwDK9QUA4ZgAgJYPAEBCAQCghgAAECcAAOgDAABk"
    "AAAACgAAAAEARUZFVgBSAAAg0AJgCCAviR/QAmAIICuJNi9WL0qS9mX2YyDQAmAg0RJkAiFIMAHk"
    "QjAAiQHgA+RGMACLA+AjZBBAAYn8r0wyEtESYCwwAOIulEIwAotIMPuvAXICISgiD4kC4AYyAIsD"
    "Yv9yBaAiJ3Jg/4gFiQDgAicA6gbQK0AJAADqBdArQAkACQAEDDj4BAww+AQMUPgGDJz5Bgxy+kwM"
    "HDcADBAjBAxw+FEM/AjoA7wC9AGWAAvQAmAIIBCJSCQOiwvREmAIIAiLB9ACYAggBola4AIhBdEB"
    "4AIhCwAJAAXQK0AJAAQMMPgEDDj4BAxo+AQMbPgHDPDdQMgPiQrREmEYIQ6JCdESYRghBIsI0RJg"
    "CNESMAWLCNEB4AIhB9ArQAkAB9ArQAkABAww+AQMOPgEDDT4AAAQJwQMaPgHDJyDBwwIgxXQAmAI"
    "ICOJFNACYAggH4t44A4lGgET0AwxElES4AYxFokIQRPHDDESYRHTMmAcMADhCuIiMAKLKDD6rwFx"
    "AiMH0iJgHDAI0RYwAIsTYAIiBtArQAkACQAEDDD4BAw4+AQMNPhSDEi2AAAQJwkMAAAEDFT4AAAB"
    "AAAAAgAAAAMAAAAEAAAABQAAAAYAAAAHAAAACAAAAAkAAAAKAAAAFAAAAB4AAAAoAAAAMgAAADwA"
    "AABGAAAAUAAAAFoAAABkAIYvli+mL7Yvxi/WLyJPz9ACbeLREmLQMgGL2KAJANIhzdESYAggAYn/"
    "cAIh3dzAYAxgx9ZgYRxhACbO4ixiIDEHiyAwGYnU0MwAYYAB4BSgYoAgMBGLYoQIIA6JAOBigGGE"
    "AXAE4RcwAIsTYMrRzDEQYixiBzIAiQAhy9uyYAggFovK0RJgytIiMDeLsdESYAggM4kA4AIhAeAC"
    "K8BgwNEAIbzQaOEVDK/RPeAmoAIhwGC70RBiADICibzRDqAJAKTREmAIIASJAOACIbfRBaAJALbR"
    "EmAK4iYwDYkA4AIhAium0QIhoNECIZ3ReOACIZnRWuACoAIhKDACIaewCQB+sQkAAOrCYLPRGCAF"
    "iaLQ9nDMAAggAIkB6rDYAOlk52R3gmAIIAOJgVAFiACLAXkQR/aPeHip2ADrgmAIIECJgVAFiD2L"
    "mNACYAggBIuX0AJgl9ESMAaLglASiAOJEuACGDywCQCCUBKIKomoKiiJi1DHURcwJIuMUMhRGDCY"
    "0RwwHDESMByJs2AMMJXRDDERYtNjKDM9YwjiIjMRi9EhglABcAIYGrAJAEDgDDACOQOJG7AJAASg"
    "CQCDZAHleLDZJQF7ZOBkcAI7to94eCZP9m32bPZr9mr2aQsA9mgiT4HQC0CDZCZPCwAJACJPf9AL"
    "QAHkCCAkiX3QAmV44A4lGgZ20Aw2g2FjYh7jFmACIhBD+48EclNgDDBy0Qwx0SEBeWYvc9ALQFNk"
    "ctALQLNk9mQ+sADlg2Q7sAHlJk8LAAkAg2QB5TSw2SX3rwkAVtESYAggDYtV0RJgVdIiMAiJPtES"
    "YAggFYkA4AIhQtELoBJgOtESYAggDIsB4AIhO9ESYD3RAiEB4DjRAiE40QAhONEAIQsACQBD0RJh"
    "GCEBizXREmAx0QIhMdEAITHRCwAAISJPRi8y0AtACQDyZDHRGSAx0RwwDRQt0AtACQD2ZC/RGSAt"
    "0RwwWCUAiQtgDhQmTwsACQAiT0YvVi8/0AtAAeT2ZfZkCCAkiT3QAmZmL3jgDiYaBzXQDDc70AIn"
    "BeABFxLgAhcA4AMXSxdcFw0XDhd2LzDQC0BzZPZn9mR2LzDQC0AJABLQC0AJAAHlCSW3v/ZkJk8L"
    "AAkACQBIDMRXBAxE+AQMaPgEDGz4BAx0+AQMePgEAgAABAx8+E4MPKxIDH8iUQzcbwQMYPhTDKT0"
    "BgxQtAAA//8CAAAAAAAAgAAA/38AAA4CAAAUAgQMPPgEDED4UQwoCwQMOPgEDDT4AAAQJ0gMPB9I"
    "DPgdSAw4HkgMeB5IDPweSAw8H0gMfB9MDBw3UQz8CAAAACBSDEi2KAAAAAQMAPoIDEALBwyg9kwM"
    "7CQIDDATgMAEAAoCyAAiTyjREmAIIBaJ/3ACIQDqPIgpCiTYT5mCYAggB4kA4AIoqCoDiYhUiVVc"
    "vwkAEEnyj1x4QrAJAB3REmAIIC2J/3ACIQDqd4gpChfUNJVCYAggHYlPUzgjBYuoKgKLAOAWoAIk"
    "COP/cz8UOCMCiwDgDqACJDNiCEIIQiwyH3IjZhhGKyYL0ismAOAKFAsUbBQQRdyPXHQA6hCwCQAm"
    "TwsACQAJAAQMfPhMDBw3UQz8CAQMePgEAgAAAAYJACJPDdgemYJgCCAOiYFQC9ESMAqLCtESMAeJ"
    "AOACKKgqA4mMVI1VAL8JAAyQDDgQSemLJk8LAAkATgz4xg0MAAAODAAAAAGQAIYvli+mL7YvIk+V"
    "2gDgCBqR2WDrvDuSYAggCYmRUY/YgmIoIgSJEDIpiUh4+K8JAGTgDDAMORBL7YuJ2qhQCCAAiwQa"
    "AOAHGqNQCCABi9mgCQAA4AMaIOETYhNjE2QTZYLWg9flsAkAIOETYhNjE2QTZYDWgNfcsAkAw6AJ"
    "AHjapFCAMAGLAeAIGoKFDWCeBp+EA2KDhZwDg2EMcRGFDWVYJQyJEGD/iAGJIDAEixGE/4gGiTAw"
    "BIkMce+vCQC3rwkAZ9oWGoSFCCAKiWTabdACZ6RQgDABiYQadRqlUHNmCDZTYWgxEUEDiYSFCCCf"
    "iQDhXNAOIRoBKUEJQRNkiLAJAANnhbAJAANmgrAJAANiQ2Mw4DgjAokMMwGgCQAg4yDhEDMBiygi"
    "AokMMgGgCQAg4gw2DDczYWNjLuRzZUvWS9d2sAkARtqmVwR3gmIA4wDhQdRg5Vw1QmAIIBeJQVAg"
    "MBSLT4QDZnNplGD/iA6JYDD6i4WFDWAIIAKJQmYIJgWJAXFE4E0AEUAAiwwzZOAMMAw0EEXfixgh"
    "DoumUKdSADIMiSDhE2ITYxNkE2Ux1jHXPrAJACKgCQCmUAcaM2QnsAkAA2YksAkAA2Uw4EgkA4lD"
    "YgwyAaAJACDiSCQBi1glAokMNQGgCQAg5Qw2U2NjZCDhIOUf1h/XGrAJABjaAeADGiZP9mv2avZp"
    "9mgLAAkAFdFDYh4iGgEpQQlBAUETYAhAHDAMMENiCDITZAsAI2AT0AshEiYLIiEWCyMyFgskQxYL"
    "JVQWAeALAAInwADIALQARAAJAEsMnHwfgLwOBAwA+AAAq6oAAM3MSAxgS04MuK1IDOhKTgywrQAA"
    "AICAgACASAzEVwoMIN+YALQAAAAAAP8AEA7/Df///////wAAAAD//////////wAAAAD/////////"
    "/wAAAAD//////////wAAAAD//////////wsM8BKYALQAAAAAAP8AEA7/AP///////wAAAAD/////"
    "/////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsM8J+YALQAAAAAAAEAMCr/"
    "AP///////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsM"
    "MNNUALQAAAAAAAEApB8zMv///////wMAMCojIiUk/////wUAIBz/Bf///////wAAAAD/////////"
    "/wAAAAD//////////wwMsByYALQAAAAAAAEAMCr/AP///////wEBIBz/Af///////wAAAAD/////"
    "/////wAAAAD//////////wAAAAD//////////wwMsGdUALQAAAAAAAEApB//Pv///////wMAMCr/"
    "MP///////wUAIBz/AP///////wAAAAD//////////wAAAAD//////////wwMoLmYALQAAAAAAAEA"
    "EA7/OP///////wMAMCr/Gv///////wUAMCr/AP///////wIqMCr/Kv///////wAAAAD/////////"
    "/woMwPmYALQAAQAAAAEABQz/AP///////wAAAAD//////////wAAAAD//////////wAAAAD/////"
    "/////wAAAAD//////////wsMcC+YALQAAQAAgAEAEgz/AP///////wAAAAD//////////wAAAAD/"
    "/////////wAAAAD//////////wAAAAD//////////wsMUEuYALQAAQAAAAEAUAr/AP///////wAA"
    "AAD//////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsMUICYALcAAQAA"
    "AAEAHg//AP///////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD/////"
    "/////wsMkGiYALQAAQAAAAEAJhb/AP///////wAAAAD//////////wAAAAD//////////wAAAAD/"
    "/////////wAAAAD//////////wAAAABIVFNJUCBPUkVKVENJIABTAAAAAAAAAAAAAAAAcCAAgE5V"
    "Rk9JRklDTEFBIEROSSAgU09OAFQAAAAAAABwIACARkFJRklMVEFERVcgVEksSEUgRE5ST0VTAEQA"
    "AHAgAIBZQiAsUk9BIFRVT0hJUkVaIERZQgAAAAAAAAAAcCAAgEFDRVYgLkxBIExJUkhHU1RUICBP"
    "SFQARQAAAABwIACAUk9HSU5JTEFHIE1BIEVOQSBEVEkAUwAAAAAAAHAgAIBTQU9TSUNUQURFSSBU"
    "TkxFRUxUQ0FVAEwAAAAAcCAAgFJQUE9SRVlUUiBNRUlBIE5JV0hUAAAAAAAAAABwIACASFRJRSBS"
    "RVJQU0NFSVRFVlIgR0lUSABTAAAAAHAgAIBPSERMUkUuUwAAAAAAAAAAAAAAAAAAAAAAAAAAcCAA"
    "gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwIACAICAgICAgQUhFVkYgTlUhISAhICAgICAg"
    "AAAAACBwABAwMjYyMS8vMDMyAABNU0tPREVCIENBTk8AAAAAT04gVE9GIFJBU0VMAAAAAAYMTPwG"
    "DHAQH4DYAwYMnNIGDHAQH4AkAAYMRNAHDNB7H4AgAQYMBM8Ti07aE4sB0AYMCM+gYDPJK0AJAAYM"
    "DM8BiAKPH4BAAAkMKAgQfwFxEH8H0AkMLAgdYGiIK0AJAAkMSAgJAAkAH4CkAQcMyGoyYigiHdQr"
    "RAcMzGoQj/Nu824JAAcMQGtRDExcH4B8AgkMwGUM0zBiDNMrQwkMxGUoIguLCQALiwkM9GVRDExc"
    "H4AgAwcMhAEHDNB7H4BkAwYMqHoODKQJH4AgEgYMtHoNDFj2H4CgEwYMxHoODCQLH4CsEwYM1Hk2"
    "2AXmNtgE5gYMIHoo1BDmKNQP5gYMONAODKgPH4C8EwcMqIVMARNgTAFz0wcMrIUgyQggK0MTYAcM"
    "eIcJAAkAH4DUAQ4MJCsIDOD4H4AgAg4MRCsIDAD8H4AmAg4MZCsIDMD8H4AsAg4MhCsIDCD/H4Ay"
    "Ag4MxCsJDAAAH4BwBgcMAINzYEDJc2Aq0AcMBIMIIEmJK0BzYAcMrIMJAAkAH4AkBgYMlPlyYP+I"
    "uNArQAYMmPlrjQDqCQAA6gcMmEUHDPDdH4DgBQcM/EgHDPDdH4DgBQYMePwJAAkAH4AwBQAAAAA=")),
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
        <part name="bacon_u4" crc="c6584146"/>
        <part name="bacon_u4" crc="c6584146"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 36)")
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
