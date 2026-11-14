# --- god_glyphs: begin (copied into ../patch.py by update_patchers.py; Python standard library only) ---
# Builds the FEVER counter digits from the user's own Xbox 360 Muchi Muchi Pork! Games-on-Demand package
# (a .zip or .7z holding D51AAA66751AC42DD8A0 and D51AAA66751AC42DD8A0.data/DataNNNN, any folder, any name).
# Nothing of the game is stored in the patch: the digits are cut from the package at patch time.
#
# Steps: archive -> GOD data files (hash blocks skipped) -> XDVDFS disc image -> MPD100.bin (Cave archive,
# one stored entry: the graphics data) -> chunk 1610 (the 360 counter digits) -> decode (Cave LZSS + dictionary,
# the same format as the arcade NAND) -> 10 digits cut from fixed cells -> shrunk (integer area average,
# 1-bit transparency) -> big-endian ARGB1555 words, laid out as GLYPH_LAYOUT says, followed by a gold glow
# (halo) for each digit, drawn additively under it.
import struct, zipfile, lzma, re

GOD_ID = 'D51AAA66751AC42DD8A0'
GLYPH_SHEET = 1610
GLYPH_CELLS = {8: (2, 0), 9: (2, 64), 4: (82, 0), 5: (82, 64), 6: (82, 128), 7: (82, 192),
               0: (162, 0), 1: (162, 64), 2: (162, 128), 3: (162, 192)}
GLYPH_CW, GLYPH_CH = 76, 64                 # cell size in the sheet (native, rotated orientation)
GLYPH_SIZES = [(17, 14)]     # (w, h) of the counter digits (the layout allows more sizes; one is used)
GLYPH_STRIDE = 24     # each digit is stored (and uploaded) 24 px wide: the blitter upload width must be a multiple
                      # of 8 like all the game's own uploads (the MiSTer core froze on 17-23 px uploads)
GLYPH_FILE_OFF = 0x1F3800   # where the digits go in the u4 (right after the patch code's 14 KB)
GLOW_PAD = 3                # the glow reaches 3 px past the digit; glow images are (w+6) x (h+6),
GLOW_W, GLOW_H = GLYPH_SIZES[0][0] + 2 * GLOW_PAD, GLYPH_SIZES[0][1] + 2 * GLOW_PAD   # stored 24 px wide
# glow colour (5-bit R, G, B) by squared distance to the nearest digit pixel; further away = transparent
GLOW_LEVELS = {0: (20, 15, 3), 1: (18, 13, 3), 2: (15, 11, 2), 4: (11, 8, 2), 5: (9, 6, 1), 8: (6, 4, 1), 9: (4, 3, 1)}
BLK = 0x1000
PER_FILE = 203 * 204


def glyph_layout():
    """[(w, h, byte offset of digit 0)] per size; digit d of a size is at offset + d * GLYPH_STRIDE * h * 2
    (rows of GLYPH_STRIDE pixels, the columns past w transparent)."""
    out, off = [], 0
    for w, h in GLYPH_SIZES:
        out.append((w, h, off))
        off += 10 * GLYPH_STRIDE * h * 2
    return out, off


GLYPH_LAYOUT, GLOW_OFF = glyph_layout()        # glow images follow the digits: digit d at GLOW_OFF + d * 24 * GLOW_H * 2
GLYPH_BYTES = GLOW_OFF + 10 * GLYPH_STRIDE * GLOW_H * 2


def _glow(px, w, h):
    """Glow image (GLOW_W x GLOW_H, rows padded to GLYPH_STRIDE) around one digit (w x h pixels)."""
    pts = [(x, y) for y in range(h) for x in range(w) if px[y * w + x] & 0x8000]
    # only outside the digit: flood fill from the image border through non-digit pixels (holes stay dark)
    solid = set((x + GLOW_PAD, y + GLOW_PAD) for x, y in pts)
    outside, todo = set(), [(x, y) for x in range(GLOW_W) for y in (0, GLOW_H - 1)] +         [(x, y) for y in range(GLOW_H) for x in (0, GLOW_W - 1)]
    while todo:
        x, y = todo.pop()
        if (x, y) in outside or (x, y) in solid or not (0 <= x < GLOW_W and 0 <= y < GLOW_H):
            continue
        outside.add((x, y))
        todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    out = []
    for y in range(GLOW_H):
        for x in range(GLYPH_STRIDE):
            v = 0
            if (x, y) in outside:
                cx, cy = x - GLOW_PAD, y - GLOW_PAD
                d = min(((cx - a) ** 2 + (cy - b) ** 2 for a, b in pts), default=99)
                c = GLOW_LEVELS.get(d)
                if c:
                    v = 0x8000 | (c[0] << 10) | (c[1] << 5) | c[2]
            out.append(v)
    return out


class _Stream:
    """Forward-only reader over one archive member, reopened when a read goes backwards."""
    def __init__(self, opener):
        self.opener = opener
        self.fh = None
        self.pos = 0

    def read_at(self, off, n):
        if self.fh is None or off < self.pos:
            self.fh = self.opener()
            self.pos = 0
        while self.pos < off:
            k = len(self.fh.read(min(off - self.pos, 1 << 20)))
            if not k:
                raise ValueError('a GOD data file is shorter than expected')
            self.pos += k
        data = self.fh.read(n)
        self.pos += len(data)
        if len(data) != n:
            raise ValueError('a GOD data file is shorter than expected')
        return data


def _data_re():
    return re.compile(r'(^|/)' + GOD_ID + r'\.data/Data(\d{4})$', re.I)


class _ZipSource:
    def __init__(self, path):
        self.z = zipfile.ZipFile(path)
        names = [n.replace('\\', '/') for n in self.z.namelist()]
        real = dict(zip(names, self.z.namelist()))
        rx = _data_re()
        self.has_pkg = any(n.split('/')[-1].upper() == GOD_ID for n in names)
        self.datas = sorted((n for n in names if rx.search(n)), key=lambda n: int(rx.search(n).group(2)))
        self.streams = [_Stream(lambda m=real[n]: self.z.open(m)) for n in self.datas]


# ---- 7z (only what is needed to stream the data files out of an LZMA / LZMA2 archive) ----
class _SevenZip:
    def __init__(self, path):
        self.f = open(path, 'rb')
        sh = self.f.read(32)
        if sh[:6] != b"7z\xbc\xaf\x27\x1c":
            raise ValueError('not a 7z file')
        nh_off, nh_size = struct.unpack_from('<QQ', sh, 12)
        self.f.seek(32 + nh_off)
        self.b = self.f.read(nh_size)
        self.p = 0
        t = self._byte()
        if t == 0x17:
            s = self._streams()
            fo = s['folders'][0]
            self.f.seek(32 + s['packpos'])
            packed = self.f.read(s['packsizes'][0])
            self.b = self._decode_folder(fo, packed, fo['sizes'][-1])
            self.p = 0
            t = self._byte()
        if t != 1:
            raise ValueError("this 7z's header can't be read")
        self.main = None
        self.files = []
        while True:
            t = self._byte()
            if t == 0:
                break
            if t == 2:
                while self._byte():
                    self.p += self._num()
            elif t == 3:
                self._streams()
            elif t == 4:
                self.main = self._streams()
            elif t == 5:
                self._files()
            else:
                self.p += self._num()

    def _byte(self):
        v = self.b[self.p]
        self.p += 1
        return v

    def _num(self):
        first = self._byte()
        mask, v = 0x80, 0
        for i in range(8):
            if not first & mask:
                return v + ((first & (mask - 1)) << (8 * i))
            v |= self._byte() << (8 * i)
            mask >>= 1
        return v

    def _bits(self, n, all_check):
        if all_check and self._byte():
            return [True] * n
        out, cur = [], 0
        for i in range(n):
            if not i & 7:
                cur = self._byte()
            out.append(bool(cur & (0x80 >> (i & 7))))
        return out

    def _digests(self, n):
        d = self._bits(n, True)
        self.p += 4 * sum(d)
        return d

    def _streams(self):
        s = {'packpos': 0, 'packsizes': [], 'folders': [], 'subsizes': None}
        while True:
            t = self._byte()
            if t == 0:
                break
            if t == 6:
                s['packpos'] = self._num()
                n = self._num()
                while True:
                    k = self._byte()
                    if k == 0:
                        break
                    if k == 9:
                        s['packsizes'] = [self._num() for _ in range(n)]
                    elif k == 10:
                        self._digests(n)
                    else:
                        self.p += self._num()
            elif t == 7:
                if self._byte() != 11:
                    raise ValueError("this 7z's header can't be read")
                nf = self._num()
                if self._byte():
                    raise ValueError("this 7z's header can't be read")
                for _ in range(nf):
                    coders, tin, tout = [], 0, 0
                    for _ in range(self._num()):
                        fl = self._byte()
                        cid = self.b[self.p:self.p + (fl & 15)].hex()
                        self.p += fl & 15
                        ni = no = 1
                        if fl & 0x10:
                            ni, no = self._num(), self._num()
                        pr = b''
                        if fl & 0x20:
                            k = self._num()
                            pr = self.b[self.p:self.p + k]
                            self.p += k
                        coders.append((cid, pr))
                        tin += ni
                        tout += no
                    for _ in range(tout - 1):
                        self._num()
                        self._num()
                    npk = tin - (tout - 1)
                    if npk > 1:
                        for _ in range(npk):
                            self._num()
                    s['folders'].append({'coders': coders, 'tout': tout, 'sizes': [], 'nsub': 1, 'crc': False})
                while True:
                    k = self._byte()
                    if k == 0:
                        break
                    if k == 12:
                        for fo in s['folders']:
                            fo['sizes'] = [self._num() for _ in range(fo['tout'])]
                    elif k == 10:
                        for fo, d in zip(s['folders'], self._digests(nf)):
                            fo['crc'] = d
                    else:
                        self.p += self._num()
            elif t == 8:
                k = self._byte()
                if k == 13:
                    for fo in s['folders']:
                        fo['nsub'] = self._num()
                    k = self._byte()
                subs = []
                for fo in s['folders']:
                    if not fo['nsub']:
                        continue
                    tot, acc = fo['sizes'][-1], 0
                    for _ in range(fo['nsub'] - 1):
                        v = self._num() if k == 9 else 0
                        subs.append(v)
                        acc += v
                    subs.append(tot - acc)
                if k == 9:
                    k = self._byte()
                while k:
                    if k == 10:
                        self._digests(sum(0 if (fo['nsub'] == 1 and fo['crc']) else fo['nsub'] for fo in s['folders']))
                    else:
                        self.p += self._num()
                    k = self._byte()
                s['subsizes'] = subs
            else:
                raise ValueError("this 7z's header can't be read")
        if s['subsizes'] is None:
            s['subsizes'] = [fo['sizes'][-1] for fo in s['folders']]
        return s

    def _files(self):
        n = self._num()
        empty = [False] * n
        names = []
        while True:
            t = self._byte()
            if t == 0:
                break
            size = self._num()
            end = self.p + size
            if t == 14:
                empty = self._bits(n, False)
            elif t == 17:
                self._byte()
                raw = self.b[self.p:end]
                names = raw.decode('utf-16-le').split('\0')[:n]
            self.p = end
        self.files = [(names[i].replace('\\', '/') if i < len(names) else '', empty[i]) for i in range(n)]

    @staticmethod
    def _filters(coders):
        out = []
        for cid, pr in reversed(coders):
            if cid == '21':
                out.append({'id': lzma.FILTER_LZMA2, 'dict_size': _lzma2_dict(pr[0])})
            elif cid == '030101':
                d = pr[0]
                out.append({'id': lzma.FILTER_LZMA1, 'lc': d % 9, 'lp': (d // 9) % 5, 'pb': d // 45,
                            'dict_size': struct.unpack_from('<I', pr, 1)[0]})
            elif cid == '00':
                continue
            else:
                raise ValueError("this 7z uses a compression the patcher can't read; re-pack it with LZMA or LZMA2")
        return out

    def _decode_folder(self, fo, packed, size):
        d = lzma.LZMADecompressor(lzma.FORMAT_RAW, filters=self._filters(fo['coders']))
        return d.decompress(packed, size)

    def opener(self, index):
        """Return a function that opens file `index` as a forward stream."""
        m = self.main
        # file -> (folder, offset in folder's output, size)
        fi = si = 0
        packpos = 32 + m['packpos']
        folder_pack = []
        for fo in m['folders']:
            folder_pack.append(packpos)
            packpos += m['packsizes'][len(folder_pack) - 1] if len(folder_pack) - 1 < len(m['packsizes']) else 0
        place, sub_left, off = {}, 0, 0
        for i, (name, isempty) in enumerate(self.files):
            if isempty:
                continue
            while sub_left == 0:
                sub_left = m['folders'][fi]['nsub']
                if sub_left == 0:
                    fi += 1
                else:
                    off = 0
                    cur_folder = fi
                    fi += 1
            place[i] = (cur_folder, off, m['subsizes'][si])
            off += m['subsizes'][si]
            si += 1
            sub_left -= 1
        folder, start, size = place[index]
        fo = m['folders'][folder]
        path, pk = self.f.name, folder_pack[folder]
        filters = self._filters(fo['coders'])

        class S:
            def __init__(s):
                s.fh = open(path, 'rb')
                s.fh.seek(pk)
                s.dec = lzma.LZMADecompressor(lzma.FORMAT_RAW, filters=filters)
                s.buf = b''
                s.skip = start
                s.left = size

            def _more(s):
                while not s.buf:
                    if s.dec.eof:
                        return False
                    chunk = s.fh.read(1 << 20) if s.dec.needs_input else b''
                    s.buf = s.dec.decompress(chunk, 1 << 22)
                    if not s.buf and s.dec.needs_input and not chunk:
                        return False
                return True

            def read(s, n):
                out = bytearray()
                while s.skip and s._more():
                    k = min(s.skip, len(s.buf))
                    s.buf = s.buf[k:]
                    s.skip -= k
                n = min(n, s.left)
                while len(out) < n and s._more():
                    k = min(n - len(out), len(s.buf))
                    out += s.buf[:k]
                    s.buf = s.buf[k:]
                s.left -= len(out)
                return bytes(out)
        return S


def _lzma2_dict(b):
    if b >= 40:
        return 0xFFFFFFFF
    return (2 | (b & 1)) << (b // 2 + 11)


class _SevenZipSource:
    def __init__(self, path):
        sz = _SevenZip(path)
        rx = _data_re()
        self.has_pkg = any(n.split('/')[-1].upper() == GOD_ID and not e for n, e in sz.files)
        idx = [(i, n) for i, (n, e) in enumerate(sz.files) if not e and rx.search(n)]
        idx.sort(key=lambda t: int(rx.search(t[1]).group(2)))
        self.datas = [n for _, n in idx]
        self.streams = [_Stream(sz.opener(i)) for i, _ in idx]


def open_god(path):
    with open(path, 'rb') as f:
        sig = f.read(6)
    if sig[:4] == b"7z\xbc\xaf":
        src = _SevenZipSource(path)
    elif sig[:2] == b'PK':
        src = _ZipSource(path)
    else:
        raise ValueError(path + " isn't a .zip or .7z file")
    missing = []
    if not src.has_pkg:
        missing.append(GOD_ID)
    if not src.datas:
        missing.append(GOD_ID + '.data/DataNNNN')
    if missing:
        raise ValueError('not found in ' + path + ': ' + ' and '.join(missing) +
                         '. Is it the Muchi Muchi Pork! Xbox 360 GOD package?')
    return src


class _Disc:
    def __init__(self, src):
        self.src = src

    def read(self, off, size):
        out = bytearray()
        while size > 0:
            block, inner = divmod(off, BLK)
            f, b = divmod(block, PER_FILE)
            group, k = divmod(b, 204)
            n = min(size, BLK - inner)
            out += self.src.streams[f].read_at((1 + group * 205 + 1 + k) * BLK + inner, n)
            off += n
            size -= n
        return bytes(out)

    def find(self, name):
        if self.read(0x10000, 20) != b'MICROSOFT*XBOX*MEDIA':
            raise ValueError("that GOD package doesn't hold an Xbox disc image")
        sec, size = struct.unpack('<II', self.read(0x10014, 8))
        data = self.read(sec * 0x800, size)
        stack = [0]
        while stack:
            o = stack.pop()
            if o * 4 + 14 > len(data):
                continue
            l, r, s, sz, attr, nl = struct.unpack_from('<HHIIBB', data, o * 4)
            if l == 0xFFFF:
                continue
            if data[o * 4 + 14:o * 4 + 14 + nl].decode('latin-1').lower() == name.lower() and not attr & 0x10:
                return s, sz
            if l:
                stack.append(l)
            if r:
                stack.append(r)
        raise ValueError(name + " wasn't found in the GOD package. Is it Muchi Muchi Pork!?")


def decode_chunk(c):
    """Muchi Muchi Pork! graphics chunk (arcade NAND / 360 MPD100.bin) -> list of 16-bit words."""
    out_bytes, tokens, ndict, bits, ecmd = struct.unpack_from('>IIHHI', c, 0)
    dic = struct.unpack_from('>%dH' % ndict, c, 16)
    cmd = 16 + 2 * ndict
    flg = cmd + ecmd
    lit = flg + (tokens + 7) // 8
    idx = bytearray()
    for t in range(tokens):
        if (c[flg + (t >> 3)] >> (7 - (t & 7))) & 1:
            v = (c[cmd] << 8) | c[cmd + 1]
            cmd += 2
            d = v >> 5
            for _ in range((v & 31) + 3):
                idx.append(idx[-d])
        else:
            idx.append(c[lit])
            lit += 1
    n = out_bytes // 2
    if bits == 0:
        return list(struct.unpack_from('>%dH' % n, bytes(idx), 0))
    px, acc, nb, mask = [], 0, 0, (1 << bits) - 1
    for b in idx:
        acc = ((acc << 8) | b) & 0xFFFFFFFF
        nb += 8
        while nb >= bits and len(px) < n:
            nb -= bits
            px.append(dic[(acc >> nb) & mask])
    return px


def god_sheet(path, index=GLYPH_SHEET):
    """(width, height, ARGB1555 pixels) of one graphics sheet from the GOD package."""
    disc = _Disc(open_god(path))
    sec, size = disc.find('MPD100.bin')
    base = sec * 0x800
    hdr = disc.read(base, 0x24 + 0x114)
    if struct.unpack_from('>I', hdr, 0)[0] != 0xC0090117:
        raise ValueError('MPD100.bin is not a Cave archive')
    flags, usize, csize, off = struct.unpack_from('>IIII', hdr, 0x24)
    if flags != 0:
        raise ValueError('MPD100.bin is in an unexpected format')
    rom = base + off
    count = struct.unpack('>I', disc.read(rom, 4))[0]
    if index >= count:
        raise ValueError('MPD100.bin has too few graphics')
    _, o, n, _ = struct.unpack('>IIII', disc.read(rom + 4 + index * 16, 16))
    px = decode_chunk(disc.read(rom + 4 + count * 16 + o, n))
    w, h = px[6] + 1, px[7] + 1
    return w, h, px[8:8 + w * h]


def _shrink(cell, cw, ch, w, h):
    """Integer area average: target pixel (x, y) covers source columns [x*cw//w, ((x+1)*cw+w-1)//w) and the
    same for rows; opaque when at least half of those source pixels are, colour = mean of the opaque ones."""
    out = []
    for y in range(h):
        y0, y1 = y * ch // h, ((y + 1) * ch + h - 1) // h
        for x in range(w):
            x0, x1 = x * cw // w, ((x + 1) * cw + w - 1) // w
            r = g = b = cnt = 0
            for yy in range(y0, y1):
                row = yy * cw
                for xx in range(x0, x1):
                    v = cell[row + xx]
                    if v & 0x8000:
                        r += (v >> 10) & 31
                        g += (v >> 5) & 31
                        b += v & 31
                        cnt += 1
            tot = (y1 - y0) * (x1 - x0)
            if cnt * 2 >= tot and cnt:
                out.append(0x8000 | ((r // cnt) << 10) | ((g // cnt) << 5) | (b // cnt))
            else:
                out.append(0)
    return out


def build_glyphs(god_path):
    """Bytes for the glyph area of the patched u4 (big-endian words, GLYPH_LAYOUT order)."""
    sw, sh, px = god_sheet(god_path)
    if (sw, sh) != (240, 256):
        raise ValueError('graphic %d of MPD100.bin is not the counter digits' % GLYPH_SHEET)
    cells = []
    for d in range(10):
        cx, cy = GLYPH_CELLS[d]
        cell = []
        for yy in range(cy, cy + GLYPH_CH):
            for xx in range(cx, cx + GLYPH_CW):
                v = px[yy * sw + xx]
                if v == 0x83E0:            # green filler in the sheet
                    v = 0
                cell.append(v)
        cells.append(cell)
    out = bytearray()
    small = []
    for w, h, _ in GLYPH_LAYOUT:
        for d in range(10):
            px = _shrink(cells[d], GLYPH_CW, GLYPH_CH, w, h)
            if len(small) < 10:
                small.append(px)
            for y in range(h):
                out += struct.pack('>%dH' % GLYPH_STRIDE, *(px[y * w:(y + 1) * w] + [0] * (GLYPH_STRIDE - w)))
    w0, h0 = GLYPH_SIZES[0]
    for d in range(10):
        out += struct.pack('>%dH' % (GLYPH_STRIDE * GLOW_H), *_glow(small[d], w0, h0))
    assert len(out) == GLYPH_BYTES
    return bytes(out)
# --- god_glyphs: end ---
