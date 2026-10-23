#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 46

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 44ad3b27.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x44AD3B27
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "DNEZkgDgAiEQQvyPBHEH1EZhGCEGiUZlRmYSYlAy94v2r2IhAtArQAkACQAfgDwWBgzQAwQMAPgA"
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
    "H4CkDh+AnAQEDCT4BgxwEE4MPKwEDDD4BAw4+AQMiPgEDDT4AAAQJyrQAmAIIAGLCwAJACJPKNAL"
    "QAkAJk8vxwNmBud/5GZiIGBJIAAiEEf5iyPSJtc5xwNlBeFUYHsgAiIQQfqPBHIf0iPQC+ECIiNj"
    "eHMCIxBB+Y8EchfQAmMY0hzXI8cDZQrhAOZWZDDgQjMCi0gz+68BcANkMOAANAqLaCYJixNgAYgC"
    "iSDkBKAJADDkAaAJAAHmQ2B7IAIiEEHjjwRyCdIB4AIiAhIEEgsABhIEDDD4H4BoCAQMNPhIDOxM"
    "SAxwTEgMfEtODLitMGAAgICAAIBggCAgSAz5HUgMOR5IDHkeSAz9HkgMPR9IDH0fmjsAyvUFAOGY"
    "AICWDwBAQgEAoIYAABAnAADoAwAAZAAAAAoAAAABAEVGRVYAUgAAQdACYAggb4lA0AJgCCBriTYv"
    "Vi9B0ZaVAOMSYAggAIkBcxBF+Y9ccUDRjZUSYAggB4kRUD/SIjADiz/SIjAAiQFzgpAMMRBF8Itk"
    "4AYzCYkzYiwyPDJxkCgwc5InMAqJCaADYm2QAjMEiZxzCENmkgGgODJkkvZl9mMt0RJgI2QGNASJ"
    "9nBHMAWJBKBDYApwRzAAi0NgAiEDYiHQAmAh0RJkAiFIMAHkQjAAiQHgA+RGMACLA+AjZBBAAYn8"
    "r0wyE9ESYCwwAOI4lEIwAotIMPuvAXICISgiEokC4AYyAIsDYv9yCKAiJxHRK5ACIXJg/4gFiQDg"
    "AicA6gbQK0AJAADqBdArQAkABAw4+AQMMPgEDFD4Bgyc+QYMcvpMDBw3AAwQIwQMcPhRDPwITgz4"
    "xgQMgPgNDAAADgwAAOgDvAL0AZYA3gMABgABkAAO0AJgCCAViUgkE4sO0RJgCCANiwrQAmAIIASL"
    "DNACYAzSIjAGi1rgAiEG0QHgAiELAAkABdArQAkACQAEDDD4BAw4+AQMaPgEDGz4Bwzw3QQMNPgA"
    "ABAnQMgPiQrREmEYIQ6JCdESYRghBIsI0RJgCNESMAWLCNEB4AIhB9ArQAkAB9ArQAkABAww+AQM"
    "OPgEDDT4AAAQJwQMaPgHDJyDBwwIgxXQAmAIICOJFNACYAggH4t44A4lGgET0AwxElES4AYxFokI"
    "QRPHDDESYRHTMmAcMADhCuIiMAKLKDD6rwFxAiMH0iJgHDAI0RYwAIsTYAIiBtArQAkACQAEDDD4"
    "BAw4+AQMNPhSDEi2AAAQJwkMAAAEDFT4AAADAAAABgAAAAkAAAAMAAAADwAAABIAAAAVAAAAGAAA"
    "ABsAAAAeAAAAPAAAAFoAAAB4AAAAlgAAALQAAADSAAAA8AAAAA4BAAAsAYYvli+mL7Yvxi/WLyJP"
    "+dESYAggC4nl0RJgbuESMAaJ99EQYEDIAonb0QHgAiHY0AJt69ESYtAyAYvqoAkA0iHp0ABgCCAD"
    "iYCIAYnAiAGL36AJANHREmAIIAGJ/3ACIeHc4tDOAeLSI2MWMwGJ/K8sMwRwNgzAYAxgxtZgYRxh"
    "ACbO4ixiIDEHiyAwGYnT0MwAYYAB4BSgYoAgMBGLYoQIIA6JAOBigGGEAXAE4RcwAIsTYMnRzDEQ"
    "YixiBzIAiQAhzNuyYAggFovL0RJgy9IiMDiLsNESYAggNIkA4AIhAeACK8Bgv9EAIbvQaOEVDK7R"
    "eeAnoAIhwGC60RBiADICib3RDqAJAKPREmAIIASJAOACIbjRBaAJALfREmAK4iYwDokA4AIhAiul"
    "0QIhn9ECIZzReOAMMAIhmNFa4AKgAiEoMAIhgbEJAADqwmC10RggBYmh0PZwzAAIIACJAeqx2ADp"
    "ZOdkd4JgCCADiYFQBYgAiwF5EEf2j3h4qtgA64JgCCA/iYFQBYg8i5nQAmAIIASLmNACYJjREjAG"
    "i4JQEogDiRLgAhg7sAkAglASiCmJqConiYtQx1EXMCOLjFDIURgwmdEcMBwxEjAbibNgDDCX0Qwx"
    "EWLTYygzPWMI4iIzEIvRIYJQAXACGBmwCQBA4AI5A4kbsAkABKAJAINkAeV4sNklAXtk4GRwAju3"
    "j3h4Jk/2bfZs9mv2avZpCwD2aCJPg9ALQINkJk8LAAkAIk+B0AtAAeQIICSJf9ACZXjgDiUaBnjQ"
    "DDaDYWNiHuMWYAIiEEP7jwRyU2AMMHTRDDHRIQF5Zi910AtAU2R00AtAs2T2ZD6wAOWDZDuwAeUm"
    "TwsACQCDZAHlNLDZJfevCQBY0RJgCCANi1fREmBX0iIwCIk+0RJgCCAViQDgAiFC0QugEmA60RJg"
    "CCAMiwHgAiE70RJgPdECIQHgONECITjRACE40QAhCwAJAEXREmEYIQGLNdESYDHRAiEx0QAhMdEL"
    "AAAhIk9GLzLQC0AJAPJkMdEZIDHRHDANFC3QC0AJAPZkL9EZIC3RHDBYJQCJC2AOFCZPCwAJACJP"
    "Ri9WL0HQC0AB5PZl9mQIICSJP9ACZmYveOAOJhoHN9AMNz3QAicF4AEXEuACFwDgAxdLF1wXDRcO"
    "F3YvMtALQHNk9mf2ZHYvMtALQAkAEtALQAkAAeUJJbe/9mQmTwsACQAJAEgMxFcEDET4BAxo+AQM"
    "bPgEDHT4BAx4+AQCAAAEDHz4Tgw8rEgMfyJRDNxvBAxg+FMMpPQGDFC0AAD//wIAAAAAAACAAAD/"
    "fwAADgIAABQCBAw8+AQMQPhRDCgLAAAoAskBgMMEDDj4BAw0+AAAECdIDDwfSAz4HUgMOB5IDHge"
    "SAz8HkgMPB9IDHwfTAwcN1EM/AgAAAAgUgxItigAAAAEDAD6CAxACwcMoPZMDOwkCAwwE4DABAAK"
    "AsgAIk8o0RJgCCAWif9wAiEA6niIKQok2E+ZgmAIIAeJAOACKKgqA4mIVIlVWL8JABBJ8o9ceEKw"
    "CQAd0RJgCCAuif9wAiEA6jiSIDApChbUM5VCYAggHYlPUzgjBYuoKgKLAOAWoAIkCOP/cz8UOCMC"
    "iwDgDqACJDNiCEIIQiwyH3IjZhhGKyYL0ismAOAKFAsUbBQQRdyPXHQA6g+wCQAmTwsACQAEDHz4"
    "TAwcN1EM/AgEDHj4BAIAAAAG7wAiTw3YHpmCYAggDomBUAvREjAKiwrREjAHiQDgAiioKgOJjFSN"
    "Vfy+CQAMkAw4EEnpiyZPCwAJAE4M+MYNDAAADgwAAAABkAAz0AJgM9ESMAeJM9ACYAggA4sy0QDg"
    "CwACISJPL9ESagHgAiEu2ADpg2dAd4JgCCABiwmgAidyYAggBYsB4AInqCoBiQiwCQABeUuQAjnr"
    "j1x4Jk8LAAkAk2JEkAI5A4tCkAI5AIs9kINjAXICMi2JXHMyYRgh+IuDZDNlF+ZGYRIlEEb7jwR1"
    "M2dAdwHgAic6VDtVQ2ZsNkw2Y2EIQRwxHDb74RxGU2f94RxHeDZqE1NmbDZcNmNhCEEcMRw2++Ec"
    "RkNn/eEcR3w2axMLAAkABAw0+AAAECcEDDj4BAyE+EwMHDcABoABAAIJAIYvli+mL7YvIk+V2gDg"
    "CBqR2WDrvDuSYAggCYmRUY/YgmIoIgSJEDIpiUh4+K8JAGTgDDAMORBL7YuJ2qhQCCAAiwQaAOAH"
    "GqNQCCABi9mgCQAA4AMaIOETYhNjE2QTZYLWg9flsAkAIOETYhNjE2QTZYDWgNfcsAkAw6AJAHja"
    "pFCAMAGLAeAIGoKFDWCeBp+EA2KDhZwDg2EMcRGFDWVYJQyJEGD/iAGJIDAEixGE/4gGiTAwBIkM"
    "ce+vCQC3rwkAZ9oWGoSFCCAKiWTabdACZ6RQgDABiYQadRqlUHNmCDZTYWgxEUEDiYSFCCCfiQDh"
    "XNAOIRoBKUEJQRNkiLAJAANnhbAJAANmgrAJAANiQ2Mw4DgjAokMMwGgCQAg4yDhEDMBiygiAokM"
    "MgGgCQAg4gw2DDczYWNjLuRzZUvWS9d2sAkARtqmVwR3gmIA4wDhQdRg5Vw1QmAIIBeJQVAgMBSL"
    "T4QDZnNplGD/iA6JYDD6i4WFDWAIIAKJQmYIJgWJAXFE4E0AEUAAiwwzZOAMMAw0EEXfixghDoum"
    "UKdSADIMiSDhE2ITYxNkE2Ux1jHXPrAJACKgCQCmUAcaM2QnsAkAA2YksAkAA2Uw4EgkA4lDYgwy"
    "AaAJACDiSCQBi1glAokMNQGgCQAg5Qw2U2NjZCDhIOUf1h/XGrAJABjaAeADGiZP9mv2avZp9mgL"
    "AAkAFdFDYh4iGgEpQQlBAUETYAhAHDAMMENiCDITZAsAI2AT0AshEiYLIiEWCyMyFgskQxYLJVQW"
    "AeALAAInwADIALQARAAJAEsMnHwfgCwRBAwA+AAAq6oAAM3MSAxgS04MuK1IDOhKTgywrQAAAICA"
    "gACASAzEVwoMIN+YALQAAAAAAP8AEA7/Df///////wAAAAD//////////wAAAAD//////////wAA"
    "AAD//////////wAAAAD//////////wsM8BKYALQAAAAAAP8AEA7/AP///////wAAAAD/////////"
    "/wAAAAD//////////wAAAAD//////////wAAAAD//////////wsM8J+YALQAAAAAAAEAMCr/AP//"
    "/////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsMMNNU"
    "ALQAAAAAAAEApB8zMv///////wMAMCojIiUk/////wUAIBz/Bf///////wAAAAD//////////wAA"
    "AAD//////////wwMsByYALQAAAAAAAEAMCr/AP///////wEBIBz/Af///////wAAAAD/////////"
    "/wAAAAD//////////wAAAAD//////////wwMsGdUALQAAAAAAAEApB//Pv///////wMAMCr/MP//"
    "/////wUAIBz/AP///////wAAAAD//////////wAAAAD//////////wwMoLmYALQAAAAAAAEAEA7/"
    "OP///////wMAMCr/Gv///////wUAMCr/AP///////wIqMCr/Kv///////wAAAAD//////////woM"
    "wPmYALQAAQAAAAEABQz/AP///////wAAAAD//////////wAAAAD//////////wAAAAD/////////"
    "/wAAAAD//////////wsMcC+YALQAAQAAgAEAEgz/AP///////wAAAAD//////////wAAAAD/////"
    "/////wAAAAD//////////wAAAAD//////////wsMUEuYALQAAQAAAAEAUAr/AP///////wAAAAD/"
    "/////////wAAAAD//////////wAAAAD//////////wAAAAD//////////wsMUICYALcAAQAAAAEA"
    "Hg//AP///////wAAAAD//////////wAAAAD//////////wAAAAD//////////wAAAAD/////////"
    "/wsMkGiYALQAAQAAAAEAJhb/AP///////wAAAAD//////////wAAAAD//////////wAAAAD/////"
    "/////wAAAAD//////////wAAAABIVFNJUCBPUkVKVENJIABTAAAAAAAAAAAAAAAAcCAAgE5VRk9J"
    "RklDTEFBIEROSSAgU09OAFQAAAAAAABwIACARkFJRklMVEFERVcgVEksSEUgRE5ST0VTAEQAAHAg"
    "AIBZQiAsUk9BIFRVT0hJUkVaIERZQgAAAAAAAAAAcCAAgEFDRVYgLkxBIExJUkhHU1RUICBPSFQA"
    "RQAAAABwIACAUk9HSU5JTEFHIE1BIEVOQSBEVEkAUwAAAAAAAHAgAIBTQU9TSUNUQURFSSBUTkxF"
    "RUxUQ0FVAEwAAAAAcCAAgFJQUE9SRVlUUiBNRUlBIE5JV0hUAAAAAAAAAABwIACASFRJRSBSRVJQ"
    "U0NFSVRFVlIgR0lUSABTAAAAAHAgAIBPSERMUkUuUwAAAAAAAAAAAAAAAAAAAAAAAAAAcCAAgAAA"
    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABwIACAICAgICAgQUhFVkYgTlUhISAhICAgICAgAAAA"
    "ACBwABAwMjYyMS8vMDMyAABNU0tPREVCIENBTk8AAAAAT04gVE9GIFJBU0VMAAAAAAYMTPwGDHAQ"
    "H4AcBAYMnNIGDHAQH4A8AAYMRNAHDNB7H4BMAQYMBM8Ti07aE4sB0AYMCM+gYDPJK0AJAAYMDM8B"
    "iAKPH4BYAAkMKAgQfwFxEH8H0AkMLAgdYGiIK0AJAAkMSAgJAAkAH4DQAQcMyGoyYigiHdQrRAcM"
    "zGoQj/Nu824JAAcMQGtRDExcH4CoAgkMwGUM0zBiDNMrQwkMxGUoIguLCQALiwkM9GVRDExcH4BY"
    "AwcMhAEHDNB7H4CoAwYMqHoODKQJH4CQFAYMtHoNDFj2H4AQFgYMxHoODCQLH4AcFgYM1Hk22AXm"
    "NtgE5gYMIHoo1BDmKNQP5gYMONAODKgPH4AsFgcMqIVMARNgTAFz0wcMrIUgyQggK0MTYAcMeIcJ"
    "AAkAH4AAAg4MJCsIDOD4H4BMAg4MRCsIDAD8H4BSAg4MZCsIDMD8H4BYAg4MhCsIDCD/H4BeAg4M"
    "xCsJDAAAH4CoBwcMAINzYEDJc2Aq0AcMBIMIIEmJK0BzYAcMrIMJAAkAH4BcBwYMlPlyYP+IuNAr"
    "QAYMmPlrjQDqCQAA6gcMmEUHDPDdH4AEBwcM/EgHDPDdH4AEBwYMePwJAAkAH4C4BQ0MKHVODDys"
    "BAyI+AAAAAA=")),
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
        <part name="bacon_u4" crc="44ad3b27"/>
        <part name="bacon_u4" crc="44ad3b27"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 46)")
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
