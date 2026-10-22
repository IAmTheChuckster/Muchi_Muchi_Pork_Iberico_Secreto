#!/usr/bin/env python3
"""
Muchi Muchi Pork (Cave CV1000) - patch build 15
Timer + boss health display, ARCADE / HARAHARA / MANPUKU / V1.01+ title menu,
V1.01+ mode (lard changes, three loops, extends in every loop), new warning screen.

Usage:
    python3 mmpork_patch.py mmpork.zip          -> writes u4 next to the zip
    python3 mmpork_patch.py u4                  -> writes u4_patched next to it
    python3 mmpork_patch.py mmpork.zip -o OUT   -> writes the patched u4 to OUT
    python3 mmpork_patch.py mmpork.zip --zip    -> also writes mmpork_patched.zip
                                                   (same set, u4 replaced)

The original u4 must have CRC32 d06cfa42; the result is checked to be 141602f2.
Only the Python standard library is used.
"""
import argparse, base64, os, sys, zipfile, zlib

ORIG_CRC = 0xD06CFA42
PATCHED_CRC = 0x141602F2
U4_SIZE = 0x200000

# Patch blocks: (offset in the u4 file as stored in the MAME set, bytes)
PATCHES = [
    (0x1C4, base64.b64decode("H4AAAA==")),
    (0x1F0000, base64.b64decode(
    "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"
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
    "H4DAAwYMnNIGDHAQH4AkAAYMRNAHDNB7H4D0AAYMBM8Ti07aE4sB0AYMCM+gYDPJK0AJAAYMDM8B"
    "iAKPH4BAAAkMKAgQfwFxEH8H0AkMLAgdYGiIK0AJAAkMSAgJAAkAH4BwAQcMyGoyYigiHdQrRAcM"
    "zGoQj/Nu824JAAcMQGtRDExcH4B8AgkMwGUM0zBiDNMrQwkMxGUoIguLCQALiwkM9GVRDExcH4Ag"
    "AwcMhAEHDNB7H4BkAwYMqHoODKQJH4DgCQYMtHoNDFj2H4BgCwYMxHoODCQLH4BsCwYM1Hk22AXm"
    "NtgE5gYMIHoo1BDmKNQP5gYMONAODKgPH4B8CwcMCIcANwKNADca0gcMDIeDYEWvK0KDYAcMdIcJ"
    "AAkAH4CgAQcMqIVMARNgTAFz0wcMrIUgyQggK0MTYAcMeIcJAAkAH4DgAQ4MJCsIDOD4H4AiAg4M"
    "RCsIDAD8H4AoAg4MZCsIDMD8H4AuAg4MhCsIDCD/H4A0AgAAAAA=")),
]


def find_u4(zf):
    for name in zf.namelist():
        if os.path.basename(name).lower() == "u4":
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


def main():
    ap = argparse.ArgumentParser(description="Patch Muchi Muchi Pork u4 (build 15)")
    ap.add_argument("input", help="mmpork.zip or a loose u4 file")
    ap.add_argument("-o", "--output", help="where to write the patched u4")
    ap.add_argument("--zip", action="store_true", help="also write mmpork_patched.zip (input must be a zip)")
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
    out = a.output or os.path.join(folder, "u4" if is_zip else os.path.basename(a.input) + "_patched")
    with open(out, "wb") as f:
        f.write(patched)
    print("original u4 CRC %08x OK" % ORIG_CRC)
    print("wrote %s (CRC %08x)" % (out, PATCHED_CRC))

    if a.zip:
        if not is_zip:
            sys.exit("error: --zip needs a zip as input")
        zout = os.path.join(folder, "mmpork_patched.zip")
        with zipfile.ZipFile(a.input) as zi, zipfile.ZipFile(zout, "w", zipfile.ZIP_DEFLATED) as zo:
            for info in zi.infolist():
                body = patched if info.filename == name else zi.read(info.filename)
                zo.writestr(info.filename, body)
        print("wrote %s" % zout)
    print("Back up your original u4 before flashing real hardware.")


if __name__ == "__main__":
    main()
