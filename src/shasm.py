"""Minimal two-pass SH-3 (big-endian) assembler for the subset used by the timer patch."""
import re, struct

def R(s):
    m = re.fullmatch(r'r(\d+)', s.strip())
    if not m: raise ValueError('bad reg ' + s)
    return int(m.group(1))

class Asm:
    def __init__(self, base):
        self.base = base

    def assemble(self, src):
        lines = []
        for raw in src.splitlines():
            line = raw.split(';')[0].strip()
            if not line: continue
            while True:
                m = re.match(r'^([A-Za-z_]\w*):\s*(.*)$', line)
                if not m: break
                lines.append(('label', m.group(1)))
                line = m.group(2).strip()
            if line: lines.append(('ins', line))
        # pass 1: sizes
        labels = {}
        for pass_ in (1, 2):
            pc = 0
            out = bytearray()
            for kind, x in lines:
                if kind == 'label':
                    labels[x] = self.base + pc
                    continue
                op, _, args = x.partition(' ')
                args = args.strip()
                if op == '.align':
                    n = int(args)
                    while pc % n:
                        out += struct.pack('>H', 0x0009)
                        pc = len(out)
                    continue
                if op == '.long':
                    for a in args.split(','):
                        v = self.val(a.strip(), labels, pass_)
                        out += struct.pack('>I', v & 0xffffffff)
                    pc = len(out); continue
                if op == '.word':
                    for a in args.split(','):
                        v = self.val(a.strip(), labels, pass_)
                        out += struct.pack('>H', v & 0xffff)
                    pc = len(out); continue
                w = self.enc(op, args, self.base + pc, labels, pass_)
                out += struct.pack('>H', w)
                pc = len(out)
            if pass_ == 2:
                return bytes(out), labels

    def val(self, s, labels, pass_):
        s = s.strip()
        if s in labels: return labels[s]
        if re.fullmatch(r'[A-Za-z_]\w*', s):
            if pass_ == 1: return 0
            raise KeyError(s)
        return int(s, 0)

    def enc(self, op, a, pc, labels, pass_):
        L = lambda s: self.val(s, labels, pass_)
        args = [x.strip() for x in re.split(r',(?![^()]*\))', a)] if a else []
        def disp_pc(target, scale, mask_pc):
            if pass_ == 1: return 0
            base = ((pc & ~3) if mask_pc else pc) + 4
            d = target - base
            assert d % scale == 0 and 0 <= d // scale <= 255, (op, a, hex(pc), d)
            return d // scale
        def br(target, bits):
            if pass_ == 1: return 0
            d = target - (pc + 4)
            assert d % 2 == 0, (op, a)
            d //= 2
            lim = 1 << (bits - 1)
            assert -lim <= d < lim, (op, a, d)
            return d & ((1 << bits) - 1)
        n = lambda i: R(args[i])
        if op == 'nop': return 0x0009
        if op == 'rts': return 0x000b
        if op == 'mov':
            if args[0].startswith('#'):
                v = int(args[0][1:], 0); assert -128 <= v <= 127
                return 0xE000 | (n(1) << 8) | (v & 0xff)
            return 0x6003 | (n(1) << 8) | (n(0) << 4)
        if op == 'mova':
            return 0xC700 | disp_pc(L(args[0]), 4, True)
        if op == 'tst' and args[0].startswith('#'):
            v = int(args[0][1:], 0); assert 0 <= v <= 255 and R(args[1]) == 0
            return 0xC800 | v
        if op == 'cmp/eq' and args[0].startswith('#'):
            v = int(args[0][1:], 0); assert -128 <= v <= 127 and R(args[1]) == 0
            return 0x8800 | (v & 0xff)
        if op == 'mov.b':
            s, d = args
            m = re.fullmatch(r'@\((\d+),r(\d+)\)', s)
            if m:
                assert R(d) == 0 and int(m.group(1)) < 16
                return 0x8400 | (int(m.group(2)) << 4) | int(m.group(1))
            m = re.fullmatch(r'@\(r0,r(\d+)\)', s)
            if m: return 0x000C | (R(d) << 8) | (int(m.group(1)) << 4)
            m = re.fullmatch(r'@r(\d+)\+', s)
            if m: return 0x6004 | (R(d) << 8) | (int(m.group(1)) << 4)
            m = re.fullmatch(r'@r(\d+)', s)
            if m: return 0x6000 | (R(d) << 8) | (int(m.group(1)) << 4)
            m = re.fullmatch(r'@r(\d+)', d)
            if m and re.fullmatch(r'r\d+', s): return 0x2000 | (int(m.group(1)) << 8) | (R(s) << 4)
            m = re.fullmatch(r'@\((\d+),r(\d+)\)', d)
            if m and R(s) == 0 and int(m.group(1)) < 16: return 0x8000 | (int(m.group(2)) << 4) | int(m.group(1))
            raise ValueError('mov.b form ' + a)
        if op in ('mov.l', 'mov.w'):
            sz = op[-1]
            s, d = args
            m = re.fullmatch(r'@\((\d+),r(\d+)\)', s)
            if m:
                disp, rm = int(m.group(1)), int(m.group(2))
                if sz == 'l':
                    assert disp % 4 == 0 and disp < 64
                    return 0x5000 | (R(d) << 8) | (rm << 4) | (disp // 4)
                assert R(d) == 0 and disp % 2 == 0 and disp < 32
                return 0x8500 | (rm << 4) | (disp // 2)
            m = re.fullmatch(r'@\(r0,r(\d+)\)', s)
            if m:
                return (0x000E if sz == 'l' else 0x000D) | (R(d) << 8) | (int(m.group(1)) << 4)
            m = re.fullmatch(r'@r(\d+)\+', s)
            if m:
                return (0x6006 if sz == 'l' else 0x6005) | (R(d) << 8) | (int(m.group(1)) << 4)
            m = re.fullmatch(r'@r(\d+)', s)
            if m:
                return (0x6002 if sz == 'l' else 0x6001) | (R(d) << 8) | (int(m.group(1)) << 4)
            # stores
            m = re.fullmatch(r'@-r(\d+)', d)
            if m:
                return (0x2006 if sz == 'l' else 0x2005) | (int(m.group(1)) << 8) | (R(s) << 4)
            m = re.fullmatch(r'@\((\d+),r(\d+)\)', d)
            if m:
                disp, rn = int(m.group(1)), int(m.group(2))
                assert sz == 'l' and disp % 4 == 0 and disp < 64
                return 0x1000 | (rn << 8) | (R(s) << 4) | (disp // 4)
            m = re.fullmatch(r'@\(r0,r(\d+)\)', d)
            if m:
                return (0x0006 if sz == 'l' else 0x0005) | (int(m.group(1)) << 8) | (R(s) << 4)
            m = re.fullmatch(r'@r(\d+)', d)
            if m:
                return (0x2002 if sz == 'l' else 0x2001) | (int(m.group(1)) << 8) | (R(s) << 4)
            # PC-relative literal load
            if sz == 'l':
                return 0xD000 | (R(d) << 8) | disp_pc(L(s), 4, True)
            return 0x9000 | (R(d) << 8) | disp_pc(L(s), 2, False)
        if op == 'sts.l' and args[0] == 'pr':
            return 0x4022 | (int(args[1][3:]) << 8)
        if op == 'lds.l' and args[1] == 'pr':
            return 0x4026 | (int(args[0][2:-1]) << 8)
        if op == 'sts' and args[0] == 'macl': return 0x001A | (n(1) << 8)
        if op == 'jsr': return 0x400B | (int(args[0][2:]) << 8)
        if op == 'jmp': return 0x402B | (int(args[0][2:]) << 8)
        two = {'add': 0x300C, 'sub': 0x3008, 'cmp/eq': 0x3000, 'cmp/hs': 0x3002, 'cmp/ge': 0x3003,
               'cmp/hi': 0x3006, 'cmp/gt': 0x3007, 'tst': 0x2008, 'or': 0x200B, 'and': 0x2009,
               'mulu.w': 0x200E, 'extu.w': 0x600D, 'extu.b': 0x600C}
        if op == 'add' and args[0].startswith('#'):
            v = int(args[0][1:], 0); assert -128 <= v <= 127
            return 0x7000 | (n(1) << 8) | (v & 0xff)
        if op in two: return two[op] | (n(1) << 8) | (n(0) << 4)
        one = {'dt': 0x4010, 'shlr': 0x4001, 'shlr2': 0x4009, 'shlr16': 0x4029, 'shll2': 0x4008,
               'cmp/pz': 0x4011}
        if op in one: return one[op] | (n(0) << 8)
        if op == 'movt': return 0x0029 | (n(0) << 8)
        if op == 'bt': return 0x8900 | br(L(args[0]), 8)
        if op == 'bf': return 0x8B00 | br(L(args[0]), 8)
        if op == 'bt/s': return 0x8D00 | br(L(args[0]), 8)
        if op == 'bf/s': return 0x8F00 | br(L(args[0]), 8)
        if op == 'bra': return 0xA000 | br(L(args[0]), 12)
        if op == 'bsr': return 0xB000 | br(L(args[0]), 12)
        raise ValueError('unsupported: ' + op + ' ' + a)
