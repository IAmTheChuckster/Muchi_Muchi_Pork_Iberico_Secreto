"""Copy a new build into the two patchers (../index.html, ../patch.py) and the MiSTer .mra.

Usage:
    python3 update_patchers.py ORIGINAL_mmpork.zip PATCHED.zip [BUILD_NUMBER]

BUILD_NUMBER is optional: by default it is the build number currently in ../index.html plus 1, so every
run that writes index.html counts as a new build.

PATCHED.zip must be built with --god (build.py), so it holds the FEVER counter digits. Diffs the two u4 files,
checks the change is only ROM 0x1C4-0x1C7, the code block from 0x1F0000 and the glyph area, then writes the
code bytes (never the digits: those come from the user's GOD package at patch time), the new CRC (with the
digits) and the build number into both patchers, and copies god_glyphs.py into patch.py. Feature text is
edited by hand.
"""
import sys, os, re, zipfile, zlib, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import god_glyphs
GLYPH_OFF = god_glyphs.GLYPH_FILE_OFF

orig_zip, new_zip = sys.argv[1], sys.argv[2]
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
if len(sys.argv) > 3:
    build = sys.argv[3]
else:
    cur = re.search(r'build (\d+)', open(os.path.join(root, 'index.html')).read())
    build = str(int(cur.group(1)) + 1)
o = zipfile.ZipFile(orig_zip).read('u4')
p = zipfile.ZipFile(new_zip).read('u4')
assert zlib.crc32(o) == 0xD06CFA42, 'original u4 CRC is not d06cfa42'
crc = zlib.crc32(p)
diff = [i for i in range(len(o)) if o[i] != p[i]]
assert all(0x1C4 <= i < 0x1C8 or 0x1F0000 <= i < 0x200000 for i in diff), 'unexpected changes'
assert any(GLYPH_OFF <= i < GLYPH_OFF + god_glyphs.GLYPH_BYTES for i in diff), 'PATCHED.zip has no digits (build with --god)'
end = (max(i for i in diff if i < GLYPH_OFF) + 4) // 4 * 4
b1 = base64.b64encode(p[0x1C4:0x1C8]).decode()
b2 = base64.b64encode(p[0x1F0000:end]).decode()

py = os.path.join(root, 'patch.py')
s = open(py, encoding='utf8').read()
s = re.sub(r'PATCHED_CRC = 0x[0-9A-Fa-f]{8}', 'PATCHED_CRC = 0x%08X' % crc, s)
s = re.sub(r'checked to be [0-9a-f]{8}', 'checked to be %08x' % crc, s)
s = re.sub(r'build \d+', 'build %s' % build, s)
s = re.sub(r'(<part name="iberico_u4" crc=")[0-9a-f]{8}', lambda m: m.group(1) + '%08x' % crc, s)
i = s.index('PATCHES = ['); j = s.index(']', s.index('(0x1F0000', i))
lines = '\n'.join('    "%s"' % b2[k:k + 76] for k in range(0, len(b2), 76))
s = s[:i] + 'PATCHES = [\n    (0x1C4, base64.b64decode("%s")),\n    (0x1F0000, base64.b64decode(\n%s)),\n' % (b1, lines) + s[j:]
g = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'god_glyphs.py'), encoding='utf8').read()
i, j = s.index('# --- god_glyphs: begin'), s.index('# --- god_glyphs: end ---') + len('# --- god_glyphs: end ---' + chr(10))
s = s[:i] + g + s[j:]
open(py, 'w', encoding='utf8', newline=chr(10)).write(s)

ht = os.path.join(root, 'index.html')
h = open(ht).read()
old = re.search(r'PATCHED_CRC = 0x([0-9a-f]{8})', h).group(1)
h = h.replace(old, '%08x' % crc)
h = re.sub(r'build \d+', 'build %s' % build, h)
h = re.sub(r'\[0x1C4, "[^"]*"\]', '[0x1C4, "%s"]' % b1, h)
h = re.sub(r'\[0x1F0000, "[^"]*"\]', '[0x1F0000, "%s"]' % b2, h)
open(ht, 'w').write(h)
print('build', build, 'u4 CRC %08x' % crc, '(%d bytes at 0x1F0000)' % (end - 0x1F0000))

mra = os.path.join(root, 'mister', 'Muchi Muchi Pork! Iberico Secreto.mra')
if not os.path.exists(mra):
    mra = os.path.join(root, 'Muchi Muchi Pork! Iberico Secreto.mra')
m = open(mra).read()
m = re.sub(r'(<part name="iberico_u4" crc=")[0-9a-f]{8}', lambda x: x.group(1) + '%08x' % crc, m)
open(mra, 'w', newline='\n').write(m)
