#!/usr/bin/env python3
"""
Muchi Muchi Pork! Smoked Bacon (Cave CV1000) - patch build 54

Usage:
    python3 mmpork_patch.py mmpork.zip              -> writes bacon_u4 next to the zip
    python3 mmpork_patch.py mmpork.zip --zip        -> also writes mmporkbcn.zip (the set with u4 replaced by bacon_u4)
    python3 mmpork_patch.py mmpork.zip --mra        -> also writes "Muchi Muchi Pork! Smoked Bacon.mra" (MiSTer)
    python3 mmpork_patch.py mmpork.zip -o OUT       -> writes the patched bacon_u4 to OUT
    python3 mmpork_patch.py u4                      -> a loose original u4 works too (no --zip)

The original u4 must have CRC32 d06cfa42; the result is checked to be 280ac34f.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x280AC34F
U4_SIZE = 0x200000
OUT_NAME = "bacon_u4"
SET_NAME = "mmporkbcn.zip"
MRA_NAME = "Muchi Muchi Pork! Smoked Bacon.mra"

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "BdEG0gbTFmACIhBD+48EcgTQK0AJAAkAH4AAAAQMAMAAAD8GBAwowAzRGZIA4AIhEEL8jwRxB9RG"
    "YRghBolGZUZmEmJQMveL9q9iIQLQK0AJAAkABAwk1wYM0AMEDAD4AAIJAAHgA9ECIQPRAiED0CtA"
    "CQBIDKwkTgxArAYMcBAl0RJjM2Ul0iBgA2IByAOJ/3MRQwCJAOMjYALIBIkBcwTgBzMAiwTjMiEA"
    "4iLWLdczYAOIAYkEiAKLAeIf1irXJdByIBvQIiAA4iEQM2AEiCkCItAiIBrQYiAa0GIgMDUCiRDQ"
    "C0Al5B3RE+IA4AIhEEL8jwRxCtoH0RJgAYgEiQKIBYkI0CtACQAI0CtACQAH0CtACQAJAAQMJPhI"
    "DDwfSAz8HggMwIwGDBzPBgwg1wYMcNcEDCj4Dgy4JwQMSMEHDEiGBwwYiA4KAAwWEAcHAFAAAAIB"
    "AgEIDDALBAww+AQMNPgODBAxBAxswQAAAAAAAAAAEtESYxXHA2UR0hLXAOQg4DA0AIs+4HsgAiIg"
    "4HsgARIjZgh2COFUYHsgAiYQQfqPBHaIcgF0Q2AFiOiLBtIB4AIiAhIEEgYSCwAIEgQMJPhIDDxF"
    "MGAAgE4MMK1SQUFDRUQgIEFIQVJBSEFSQU1QTktVIFUxVjAuKzEgIFJBQVJHTitFCNACYAggAIkB"
    "cQFxaOADMQOJESwE0CtACQADYREsA9ArQAkABAwo+AkMNAgJDFAIIMgXiw3SImIoIg2JQmIZkzgi"
    "A4sZkEwCKCIFiROQTQISkCUEB6AB4xNgEMgA4wKJAaAB4wDjAtIrQgkABAwo+AcMvoUAIA4CEgIK"
    "AhLQCaAJABLQBqAJABHQA6AJABHQAKAJAAvREmEYIQGLK0AJAIYvli+mLyJPQ2hTaQNqC0oJAINk"
    "C0qTZSZP9mr2aQsA9mgJAAQMKPgIDOD4CAwA/AgMwPwIDCD/HtIiYigiDIsyYigiBose1EBiKCIC"
    "ix3SK0IJABzSK0IJABjWYmAIIPiLFdZiYACIConzrwkAAOAa0gIiGtIAIhrSACLqrwkAAeACJjJl"
    "CqABdQLgAiYB4BLSAiIS0gAiEtIAIgDlC9T/4QjnCtZyJgrQC0BSJArQK0AJAAQMKPgEDCz4BAww"
    "+FEMTFwHDNhqBwzwakgMHCBIDJj1BwywAQcM+mpODDysSAx/IlEM3G8M0zJjOCMGiw3TMGIoIg6L"
    "DNMrQwkACdMyYzgjB4sG0zJjAeIiMwKJCNMrQwkABtMrQwkABAwo+AQMLPgEDDD4UQxMXAkMyGUJ"
    "DOBlCQzkZRLQAmAIIB6JHuAOJRoBbDEIQQ/SHDITxwNjEdACYAggAYkLAAkAC9cI4TRgeyACIhBB"
    "+o8EclNgCEAMMAbSDDIB4AsAAiIF0CtACQAEDCj4SAxQOjBgAIBODJisBwzQewQMMPgxVjAuKzEg"
    "IFJBQVJHTitFAOAg0QIhJdEQYAggLImAiCqJwIgoiR3REmABiAyJHNESYAggCokb0RJgCCAEixzR"
    "EmAc0RIwAYsBoAHgAOAW0QIhIk9GL1YvZi92LwvQC0AJAAvQC0AJAPZn9mb2ZfZkJk8J0CtACQAi"
    "T0YvVi9mL3YvAtALQAkA7q8JAAQMjM8EDOzEBAwk+AYMcBBODDysBAww+AQMOPgEDIj4UQwoCwQM"
    "NPgAABAnGdACYAggAYsLAAkAIk8X0AtACQAmTxbQAmMb1ziQAjMAixrXCEM8MwDkMpESMwKLGDP7"
    "rwF0E9II5QjmYzQCixfgB6AJABVEAokg4AKgCQBDYA9weyACIgRy+HQQRe2LB9IB4AsAAiIEDDD4"
    "BAyUyAQMNPhIDOxMSAxwTEgM1EtODLCtSAy4SkAgAIAggAAgECfiBDBgAIBggAAggIAAgGCAICAA"
    "ABAnAADoAwAAZAAAAAoAAAABAEVGRVYgUgAATdACYAggC4lK0AJgCCAJi1TQAmACiAOLU9ACYAgg"
    "AYt3oAkANi9WL0fRqJUA4xJgCCAAiQFzEEX5j1xxRtGflRJgCCAHiRFQSNIiMAOLSNIiMACJAXOU"
    "kAwxEEXwi2TgBjMJiTNiLDI8MoOQKDCFkicwCokJoANif5ACMwSJnHMIQ3iSAaA4MnaS9mX2YzTR"
    "EmAIIAOLJ9ESYAggAotrki7RIiEt0RJgI2QGNASJ9nBHMAWJBKBDYApwRzAAi0NgAiEDYiHQAmAh"
    "0RJkAiFIMAHkQjAAiQHgA+RGMACLA+AjZBBAAYn8r0wyFNESYCwwAOI/lEIwAotIMPuvAXICISgi"
    "EokC4AYyAIsDYv9yCKAiJxLRMpACIXJg/4gFiQDgAicA6gbQK0AJAADqBdArQAkACQAEDDj4BAww"
    "+AQMUPgGDJz5Bgxy+kwMHDcADBAjBAxw+FEM/AhODPjGBAyA+AQMfPgEDIz4BAx4+A0MAAAODAAA"
    "6AO8AvQBlgDeAwAGAAGQAA7QAmAIIBWJSCQTiw7REmAIIA2LCtACYAggBIsM0AJgDNIiMAaLWuAC"
    "IQbRAeACIQsACQAF0CtACQAJAAQMMPgEDDj4BAxo+AQMbPgHDPDdBAw0+AAAECdAyA+JCtESYRgh"
    "DokJ0RJhGCEEiwjREmAI0RIwBYsI0QHgAiEH0CtACQAH0CtACQAEDDD4BAw4+AQMNPgAABAnBAxo"
    "+AcMnIMHDAiDFdACYAggI4kU0AJgCCAfi3jgDiUaARPQDDESURLgBjEWiQhBE8cMMRJhEdMyYBww"
    "AOEK4iIwAosoMPqvAXECIwfSImAcMAjRFjAAixNgAiIG0CtACQAJAAQMMPgEDDj4BAw0+FIMSLYA"
    "ABAnCQwAAAQMVPgAAAMAAAAGAAAACQAAAAwAAAAPAAAAEgAAABUAAAAYAAAAGwAAAB4AAAA8AAAA"
    "WgAAAHgAAACWAAAAtAAAANIAAADwAAAADgEAACwBhi+WL6Yvti/GL9YvIk/s0RJgCCALidjREmBu"
    "4RIwBonq0RBgQMgCicvRAeACIcjQAm3e0RJi0DIBi/ygCQDSIdzQAGAIIAOJgIgBicCIAYvxoAkA"
    "wdESYAggAYn/cAIh1NzV0M4B1dIjYxYzAYn8rywzBHA2DMBgDGC21mBhHGEAJs7iLGIgMQeLIDAZ"
    "icbQzABhgAHgFKBigCAwEYtihAggDokA4GKAYYQBcAThFzAAixNgvNHMMRBiLGIHMgCJACG/27Jg"
    "CCAWi77REmC+0iIwSoug0RJgCCBGiQDgAiEB4AIrwGCy0QAhrtBo4RUModF54DmgAiHAYK3REGIA"
    "MgWJl9EB4AIhrtEUoAkAktESYAggB4kA4AIhkdEB4AIhqNEIoAkAp9ESYAriJjAaiYvSAuACIgDg"
    "AiECK5PRAiGN0QIhiNEB4AIhhdESYAKIAol44AGgDDB54IXRAiF/0VrgAqACISgwAiFVsQkAAOrC"
    "YJ/RGCAFiYvQ9nDMAAggAIkB6pvYAOlk52R3gmAIIAOJgVAFiACLAXkQR/aPeHiU2ADrgmAIID+J"
    "gVAFiDyLg9ACYAggBIuC0AJggtESMAaLglASiAOJEuACGDuwCQCCUBKIKYmoKieJi1DHURcwI4uM"
    "UMhRGDCD0RwwHDESMBuJs2AMMIHRDDERYtNjKDM9YwjiIjMQi9EhglABcAIYGbAJAEDgAjkDiRuw"
    "CQAEoAkAg2QB5Xiw2SUBe2TgZHACO7ePeHgmT/Zt9mz2a/Zq9mkLAPZoIk9t0AtAg2QmTwsACQAi"
    "T2vQC0AB5AggJIlp0AJleOAOJRoGYtAMNoNhY2Ie4xZgAiIQQ/uPBHJTYAwwXtEMMdEhAXlmL1/Q"
    "C0BTZF7QC0CzZPZkPrAA5YNkO7AB5SZPCwAJAINkAeU0sNkl968JAELREmAIIA2LQdESYEHSIjAI"
    "iSjREmAIIBWJAOACISzRC6ASYCTREmAIIAyLAeACISXREmAn0QIhAeAi0QIhItEAISLRACELAAkA"
    "L9ESYRghAYsf0RJgG9ECIRvRACEb0QsAACEiT0YvHNALQAkA8mQb0RkgG9EcMA0UF9ALQAkA9mQZ"
    "0RkgF9EcMFglAIkLYA4UJk8LAAkACQBIDMRXBAxE+AQMaPgEDGz4BAyM+AQMkPgEDJT4BAx0+AQM"
    "ePgEAgAABAx8+E4MPKxIDH8iUQzcbwQMYPhTDKT0BgxQtAAA//8CAAAAAAAAgAAA/38AAA4CAAAU"
    "AgQMPPgEDED4UQwoCwAAKALJAYDDBAw4+AQMNPgAABAnSAw8H0gM+B1IDDgeSAx4HkgM/B5IDDwf"
    "SAx8H0wMHDdRDPwIAAAAIFIMSLYoAAAABAwA+ggMQAsHDKD2TAzsJAgMMBOAwAQACgLIACJPK9ES"
    "YAggCon/cAIhAOp4iCkKJrAJAKSwCQA2sAkAJdESYAggGon/cAIhI9ESagDgAiEi0RJgAogpAgHg"
    "KDAg0QIhDrAJAIywCQAd0QDgAiEb0RJgAogBixewCQAmTwsACQAiTxPYLpmCYAggB4kA4AIoqCoD"
    "iYhUiVUqsAkAEEnyj1x4Jk8LAAkAD9gcmQ/SgmAIIAaJgVAFiAOLjVAHMgCLLRgQSfOPeHgLAAkA"
    "BAx8+EwMHDcEDHj4BAyU+AQMjPgEDJD4AAbIAFIMSLb//wCAIk9GL1YvGtALQAHk9mX2ZAggKYkb"
    "0AJmZi944A4mGgcW0Aw3E9ACJwXgARcX0AJgCCAS4ACJAOACFwDgAxdLF1wXDRcOF3YvC9ALQHNk"
    "9mf2ZHYvCtALQAkAC9ALQAkAAeUJJTiw9mQmTwsACQAJAAcMoPaAwAQACAxAC1IMSLYIDDATTAzs"
    "JAYMULQEDJD4Ik8N2B6ZgmAIIA6JgVAL0RIwCosK0RIwB4kA4AIoqCoDiYxUjVWjvwkADJAMOBBJ"
    "6YsmTwsACQBODPjGDQwAAA4MAAAAAZAAIk9GLwvQC0AJAPJkCtEZIArRHDANFAfQC0AJAPZkCdEZ"
    "IAfRHDBYJQCJC2AOFCZPCwAJAAYMULQAAP//AgAAAAIAAAABAP//M9ACYDPREjAHiTPQAmAIIAOL"
    "MtEA4AsAAiEiTy/REmoB4AIhLtgA6YNnQHeCYAggAYsJoAIncmAIIAWLAeACJ6gqAYkIsAkAAXlL"
    "kAI5649ceCZPCwAJAJNiRJACOQOLQpACOQCLPZCDYwFyAjItiVxzMmEYIfiLg2QzZRfmRmESJRBG"
    "+48EdTNnQHcB4AInOlQ7VUNmbDZMNmNhCEEcMRw2++EcRlNn/eEcR3g2ahNTZmw2XDZjYQhBHDEc"
    "NvvhHEZDZ/3hHEd8NmsTCwAJAAQMNPgAABAnBAw4+AQMhPhMDBw3AAaAAQACCQCGL5Yvpi+2LyJP"
    "ldoA4Agakdlg67w7kmAIIAmJkVGP2IJiKCIEiRAyKYlIePivCQBk4AwwDDkQS+2LidqoUAggAIsE"
    "GgDgBxqjUAggAYvZoAkAAOADGiDhE2ITYxNkE2WC1oPX5bAJACDhE2ITYxNkE2WA1oDX3LAJAMOg"
    "CQB42qRQgDABiwHgCBqChQ1gngafhANig4WcA4NhDHERhQ1lWCUMiRBg/4gBiSAwBIsRhP+IBokw"
    "MASJDHHvrwkAt68JAGfaFhqEhQggColk2m3QAmekUIAwAYmEGnUapVBzZgg2U2FoMRFBA4mEhQgg"
    "n4kA4VzQDiEaASlBCUETZIiwCQADZ4WwCQADZoKwCQADYkNjMOA4IwKJDDMBoAkAIOMg4RAzAYso"
    "IgKJDDIBoAkAIOIMNgw3M2FjYy7kc2VL1kvXdrAJAEbaplcEd4JiAOMA4UHUYOVcNUJgCCAXiUFQ"
    "IDAUi0+EA2ZzaZRg/4gOiWAw+ouFhQ1gCCACiUJmCCYFiQFxROBNABFAAIsMM2TgDDAMNBBF34sY"
    "IQ6LplCnUgAyDIkg4RNiE2MTZBNlMdYx1z6wCQAioAkAplAHGjNkJ7AJAANmJLAJAANlMOBIJAOJ"
    "Q2IMMgGgCQAg4kgkAYtYJQKJDDUBoAkAIOUMNlNjY2Qg4SDlH9Yf1xqwCQAY2gHgAxomT/Zr9mr2"
    "afZoCwAJABXRQ2IeIhoBKUEJQQFBE2AIQBwwDDBDYggyE2QLACNgE9ALIRImCyIhFgsjMhYLJEMW"
    "CyVUFgHgCwACJ8AAyAC0AEQACQBLDJx8BAwU0gQMAPgAAKuqAADNzEgMYEtODLitSAzoSk4MsK0A"
    "AACAgIAAgEgMxFcKDCDfmAC0AAAAAAD/ABAO/w3///////8AAAAA//////////8AAAAA////////"
    "//8AAAAA//////////8AAAAA//////////8LDPASmAC0AAAAAAD/ABAO/wD///////8AAAAA////"
    "//////8AAAAA//////////8AAAAA//////////8AAAAA//////////8LDPCfmAC0AAAAAAABADAq"
    "/wD///////8AAAAA//////////8AAAAA//////////8AAAAA//////////8AAAAA//////////8L"
    "DDDTVAC0AAAAAAABAKQfMzL///////8DADAqIyIlJP////8FACAc/wX///////8AAAAA////////"
    "//8AAAAA//////////8MDLAcmAC0AAAAAAABADAq/wD///////8BASAc/wH///////8AAAAA////"
    "//////8AAAAA//////////8AAAAA//////////8MDLBnVAC0AAAAAAABAKQf/z7///////8DADAq"
    "/zD///////8FACAc/wD///////8AAAAA//////////8AAAAA//////////8MDKC5mAC0AAAAAAAB"
    "ABAO/zj///////8DADAq/xr///////8FADAq/wD///////8CKjAq/yr///////8AAAAA////////"
    "//8KDMD5mAC0AAEAAAABAAUM/wD///////8AAAAA//////////8AAAAA//////////8AAAAA////"
    "//////8AAAAA//////////8LDHAvmAC0AAEAAIABABIM/wD///////8AAAAA//////////8AAAAA"
    "//////////8AAAAA//////////8AAAAA//////////8LDFBLmAC0AAEAAAABAFAK/wD///////8A"
    "AAAA//////////8AAAAA//////////8AAAAA//////////8AAAAA//////////8LDFCAmAC3AAEA"
    "AAABAB4P/wD///////8AAAAA//////////8AAAAA//////////8AAAAA//////////8AAAAA////"
    "//////8LDJBomAC0AAEAAAABACYW/wD///////8AAAAA//////////8AAAAA//////////8AAAAA"
    "//////////8AAAAA//////////8AAAAASFRTSVAgT1JFSlRDSSAAUwAAAAAAAAAAAAAAAHAgAIBO"
    "VUZPSUZJQ0xBQSBETkkgIFNPTgBUAAAAAAAAcCAAgEZBSUZJTFRBREVXIFRJLEhFIEROUk9FUwBE"
    "AABwIACAWUIgLFJPQSBUVU9ISVJFWiBEWUIAAAAAAAAAAHAgAIBBQ0VWIC5MQSBMSVJIR1NUVCAg"
    "T0hUAEUAAAAAcCAAgFJPR0lOSUxBRyBNQSBFTkEgRFRJAFMAAAAAAABwIACAU0FPU0lDVEFERUkg"
    "VE5MRUVMVENBVQBMAAAAAHAgAIBSUFBPUkVZVFIgTUVJQSBOSVdIVAAAAAAAAAAAcCAAgEhUSUUg"
    "UkVSUFNDRUlURVZSIEdJVEgAUwAAAABwIACAT0hETFJFLlMAAAAAAAAAAAAAAAAAAAAAAAAAAHAg"
    "AIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAcCAAgCAgICAgIEFIRVZGIE5VISEgISAgICAg"
    "IAAAAAAgcAAQMDI2MjEvLzAzMgAATVNLT0RFQiBDQU5PAAAAAE9OIFRPRiBSQVNFTAAAAAAGDEz8"
    "BgxwEAQMRMQGDJzSBgxwEAQMZMAGDETQBwzQewQMdMEGDATPE4tO2hOLAdAGDAjPoGAzyStACQAG"
    "DAzPAYgCjwQMgMAJDCgIEH8BcRB/B9AJDCwIHWBoiCtACQAJDEgICQAJAAQM+MEHDMhqMmIoIh3U"
    "K0QHDMxqEI/zbvNuCQAHDEBrUQxMXAQM0MIJDMBlDNMwYgzTK0MJDMRlKCILiwkAC4sJDPRlUQxM"
    "XAQMgMMHDIQBBwzQewQM0MMGDKh6DgykCQQMeNUGDLR6DQxY9gQM+NYGDMR6DgwkCwQMBNcGDNR5"
    "NtgF5jbYBOYGDCB6KNQQ5ijUD+YGDDjQDgyoDwQMFNcHDKiFTAETYEwBc9MHDKyFIMkIICtDE2AH"
    "DHiHCQAJAAQMKMIODCQrCAzg+AQMdMIODEQrCAwA/AQMesIODGQrCAzA/AQMgMIODIQrCAwg/wQM"
    "hsIODMQrCQwAAAQM1McHDACDc2BAyXNgKtAHDASDCCBJiStAc2AHDKyDCQAJAAQMiMcGDJT5cmD/"
    "iLjQK0AGDJj5a40A6gkAAOoHDJhFBwzw3QQMMMcHDPxIBwzw3QQMMMcGDHj8CQAJAAQMrMUNDCh1"
    "Tgw8rAQMiPgAAAAA")),
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
        <part name="bacon_u4" crc="280ac34f"/>
        <part name="bacon_u4" crc="280ac34f"/>
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
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 into bacon_u4 (Smoked Bacon, build 54)")
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
