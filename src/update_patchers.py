"""Copy a new build into the two patchers (../index.html, ../mmpork_patch.py) and the MiSTer .mra.

Usage:
    python3 update_patchers.py ORIGINAL_mmpork.zip PATCHED.zip BUILD_NUMBER

Diffs the two u4 files, checks the change is only ROM 0x1C4-0x1C7 and the 0x1F0000 block, then writes
the new bytes, the new CRC and the build number into both patchers. Feature text is edited by hand.
"""
import sys, os, re, zipfile, zlib, base64

orig_zip, new_zip, build = sys.argv[1], sys.argv[2], sys.argv[3]
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
o = zipfile.ZipFile(orig_zip).read('u4')
p = zipfile.ZipFile(new_zip).read('u4')
assert zlib.crc32(o) == 0xD06CFA42, 'original u4 CRC is not d06cfa42'
crc = zlib.crc32(p)
diff = [i for i in range(len(o)) if o[i] != p[i]]
assert all(0x1C4 <= i < 0x1C8 or 0x1F0000 <= i < 0x1F1000 for i in diff), 'unexpected changes'
end = (max(diff) + 4) // 4 * 4
b1 = base64.b64encode(p[0x1C4:0x1C8]).decode()
b2 = base64.b64encode(p[0x1F0000:end]).decode()

py = os.path.join(root, 'mmpork_patch.py')
s = open(py).read()
s = re.sub(r'PATCHED_CRC = 0x[0-9A-Fa-f]{8}', 'PATCHED_CRC = 0x%08X' % crc, s)
s = re.sub(r'checked to be [0-9a-f]{8}', 'checked to be %08x' % crc, s)
s = re.sub(r'build \d+', 'build %s' % build, s)
s = re.sub(r'(<part name="bacon_u4" crc=")[0-9a-f]{8}', lambda m: m.group(1) + '%08x' % crc, s)
i = s.index('PATCHES = ['); j = s.index(']', s.index('(0x1F0000', i))
lines = '\n'.join('    "%s"' % b2[k:k + 76] for k in range(0, len(b2), 76))
s = s[:i] + 'PATCHES = [\n    (0x1C4, base64.b64decode("%s")),\n    (0x1F0000, base64.b64decode(\n%s)),\n' % (b1, lines) + s[j:]
open(py, 'w').write(s)

ht = os.path.join(root, 'index.html')
h = open(ht).read()
old = re.search(r'PATCHED_CRC = 0x([0-9a-f]{8})', h).group(1)
h = h.replace(old, '%08x' % crc)
h = re.sub(r'build \d+', 'build %s' % build, h)
h = re.sub(r'\[0x1C4, "[^"]*"\]', '[0x1C4, "%s"]' % b1, h)
h = re.sub(r'\[0x1F0000, "[^"]*"\]', '[0x1F0000, "%s"]' % b2, h)
open(ht, 'w').write(h)
print('build', build, 'u4 CRC %08x' % crc, '(%d bytes at 0x1F0000)' % (end - 0x1F0000))

mra = os.path.join(root, 'Muchi Muchi Pork! Smoked Bacon.mra')
m = open(mra).read()
m = re.sub(r'(<part name="bacon_u4" crc=")[0-9a-f]{8}', lambda x: x.group(1) + '%08x' % crc, m)
open(mra, 'w', newline='\n').write(m)
