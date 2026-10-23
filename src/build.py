"""Build the patched Muchi Muchi Pork u4 (Smoked Bacon).

Usage:
    python3 build.py ORIGINAL_mmpork.zip OUT.zip [RAM_DUMP.bin]

ORIGINAL_mmpork.zip must contain the original u4 (CRC d06cfa42). OUT.zip is the same set with u4 replaced.
RAM_DUMP.bin is optional: a dump of main RAM 0C000000-0C1FFFFF taken after boot (from MAME). When given,
every patch site's original value is checked at build time. The patcher in the ROM checks them again at
boot either way, and skips any site that does not match.

No ROM or RAM data is stored in this repository.
"""
import sys, os, struct, re, zipfile, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shasm import Asm

ORIG_ZIP = sys.argv[1]
OUT_ZIP = sys.argv[2]
RAM_DUMP = sys.argv[3] if len(sys.argv) > 3 else None

ROM_OFF = 0x1F0000            # blank (0xFF) area in the program ROM
RUN_BASE = 0x80000000 | ROM_OFF   # executed from ROM via cached P1 address
TEXT_RENDER = 0x0C061070      # game's text-layer redraw routine
MAIN = 0x0C0603D0             # game main, original target of boot literal at 0x1C4

# timed enemies: (update routine at slot+4, timer field offset, section limits in frames)
ANY = -1
# (update routine at slot+4, timer field, sub-state byte offset, mode,
#  rules[(part # slot+0x0C, sub-state, frames, [parts whose health (slot+0x44) is summed])])
# mode 0: remaining = frames - timer field.  mode 1: remaining = frames - game frames since the rule first matched.
ENEMIES = [
    (0x0C0ADF20, 0x98, 0xB4, 0, [(0, ANY, 3600, [13])]),                                   # stage 1 midboss
    (0x0C0B12F0, 0x98, 0xB4, 0, [(0, ANY, 3600, [0])]),                                    # stage 2 midboss
    (0x0C0B9FF0, 0x98, 0xB4, 0, [(0, 1, 10800, [0])]),                                     # stage 1 boss
    (0x0C0BD330, 0x54, 0xB4, 0, [(0, 1, 8100, [50, 51]), (0, 3, 10800, [34, 35, 36, 37]), (0, 5, 7200, [5])]),  # stage 2 boss (section 3 core is part 5; part 0 can't be hurt)
    (0x0C0C1CB0, 0x98, 0xB4, 0, [(0, 1, 10800, [0]), (1, 1, 7200, [1])]),                  # stage 3 boss
    (0x0C0C67B0, 0x54, 0xB4, 0, [(0, 1, 8100, [62]), (0, 3, 10800, [48]), (0, 5, 7200, [0])]),  # stage 4 boss
    (0x0C0CB9A0, 0x98, 0xB4, 0, [(0, 1, 3600, [56]), (0, 3, 10800, [26]), (0, 5, 10800, [0]), (42, 2, 10800, [42])]),  # stage 5 boss
    (0x0C0AF9C0, 0x98, 0xB4, 1, [(0, 1, 3077, [0])]),                                      # stage 3 midboss (exit varies 49-53.5s)
    (0x0C0B2F70, 0x98, 0xB4, 1, [(0, 1, 3090, [0])]),                                      # stage 4 midboss A (scroll exit, +-1s)
    (0x0C0B4B50, 0x98, 0xB4, 1, [(0, 1, 2640, [0])]),                                      # stage 4 midboss B
    (0x0C0B8050, 0x98, 0xB7, 1, [(0, 1, 3870, [0])]),                                      # stage 5 midboss A
    (0x0C0B6890, 0x98, 0xB4, 1, [(0, 1, 5670, [0])]),                                      # stage 5 midboss B
]
ENTRY = 72   # handler(4) field(2) suboff(2) mode(2) hpmask(2) + 5 rules x 12 bytes
# health only counts slots whose header (slot+0) has these bits set (0 = no requirement)
HPMASK = {0x0C0B2F70: 0x8000}   # stage 4 midboss A: skip the undamageable second part-0 object

def table_src():
    s = 'enemy_table:\n'
    for h, f, sub, mode, rules in ENEMIES:
        assert len(rules) <= 5
        s += f'  .long 0x{h:08x}\n  .word 0x{f:x}, 0x{sub:x}, {mode}, 0x{HPMASK.get(h, 0):x}\n'
        for st, sb, lim, hp in rules + [(0, 0, 0, [])] * (5 - len(rules)):
            assert len(hp) <= 7   # list must end with an 0xFF terminator
            h = [x & 0xff for x in hp] + [0xff] * (8 - len(hp))
            s += f'  .word 0x{(st & 0xff) << 8 | (sb & 0xff):04x}, {lim}, ' + ', '.join(f'0x{h[i] << 8 | h[i + 1]:04x}' for i in range(0, 8, 2)) + '\n'
    s += '  .long 0\n'
    return s

def warn_src():
    import textwrap
    disc = ('This project is unofficial and is not affiliated with, endorsed by, or authorized by CAVE. '
            'All rights to the original game and its associated intellectual property remain with their '
            'respective rights holders.').upper()
    lines = textwrap.wrap(disc, 25)                 # 10 lines, cyan (25 chars fits, as tested in build 14)
    assert len(lines) == 10
    lines += ['', 'HAVE FUN!!!'.center(24)]          # blank line, then HAVE FUN!!! in red
    colors = [0x20708000] * 12
    colors[11] = 0x70201000                         # red, same as the original JAPAN line
    out = '  .align 4\nwarntable:\n'
    for t, c in zip(lines, colors):
        b = t.encode('ascii').ljust(28, b'\0')
        out += '  .long ' + ', '.join('0x%08x' % int.from_bytes(b[i:i + 4], 'big') for i in range(0, 28, 4)) + ', 0x%08x\n' % c
    for name, text in (('datestr', '2026/10/23'), ('verstr', 'SMOKED BACON'), ('nfsstr', 'NOT FOR SALE')):
        b = text.encode('ascii') + b'\0'
        b = b.ljust((len(b) + 3) // 4 * 4, b'\0')
        out += name + ':\n  .long ' + ', '.join('0x%08x' % int.from_bytes(b[i:i + 4], 'big') for i in range(0, len(b), 4)) + '\n'
    return out

def patch_sites(ram):
    # (RAM address, expected original long, new long) patches applied to the unpacked program at boot
    rd = lambda a: struct.unpack('>I', ram[a - 0x0C000000:a - 0x0C000000 + 4])[0]
    sites = [
        (0x0C06FC4C, TEXT_RENDER, 'wrapper'),    # gameplay screen text redraw call -> timer/health
        (0x0C06D29C, TEXT_RENDER, 'unlock'),     # title screen text redraw call -> unlock Harahara/Manpuku
        (0x0C06D044, 0x0C077BD0, 'menudraw'),    # title mode-name draw -> 3-line menu
        (0x0C06CF04, 0x8B13DA4E, '0x8B13D001'),  # 0C06CF06: mov.l @(0C06CF0C),r0
        (0x0C06CF08, 0x60A0C933, '0x402B0009'),  # 0C06CF08: jmp @r0 / nop
        (0x0C06CF0C, 0x88018F02, 'menu'),        # literal: menu routine
        (0x0C090828, 0x7F107101, '0x7F10D007'),  # pig pickup: 0C09082A mov.l @(0C090848),r0
        (0x0C09082C, 0x601D8868, '0x402B0009'),  #   jmp @r0 / nop
        (0x0C090848, 0x00090009, 'lardadd'),     #   literal in unused padding
        (0x0C076AC8, 0x62322228, '0xD41D442B'),  # end-of-loop decision: mov.l @(0C076B40),r4 / jmp @r4
        (0x0C076ACC, 0x8F106EF3, '0x6EF30009'),  #   delay slot keeps mov r15,r14
        (0x0C076B40, 0x0C515C4C, 'loopchk'),     #   literal -> loopchk
        (0x0C0965C0, 0xD30C6230, '0xD30C432B'),  # stage-side loop check: jmp @r3 (r3 = literal 0C0965F4)
        (0x0C0965C4, 0x22288B0B, '0x00098B0B'),  #   nop
        (0x0C0965F4, 0x0C515C4C, 'loopchk2'),    #   literal -> loopchk2
        (0x0C070184, 0x0C077BD0, 'modelabel'),   # in-game mode name (column 37) -> shows V1.01 too
        (0x0C067AA8, 0x0C0E09A4, 'warntable'),   # warning screen: 12-line text table -> CAVE OWNS!!!
        (0x0C067AB4, 0x0C0DF658, 'datestr'),     # warning screen: date string -> 2026/10/14
        (0x0C067AC4, 0x0C0E0B24, 'verstr'),      # warning screen: MASTER VER. -> ROPPAKU
        (0x0C0679D4, 0xD836E605, '0xD836E604'),  #   date starts at text row 4 (was 5), so the 23-character line is centred
        (0x0C067A20, 0xD428E610, '0xD428E60F'),
        (0x0C06D038, 0x0C0E0FA8, 'nfsstr'),      # title screen: SALE BY AMI -> NOT FOR SALE (same row 9, centred)
        (0x0C0785A8, 0x014C6013, '0x014CD373'),  # lard: button check when not firing -> mov.l @(0C078778),r3
        (0x0C0785AC, 0xC9202008, '0x432B6013'),  #   jmp @r3 / mov r1,r0
        (0x0C078778, 0x00090009, 'hookB'),       #   literal in unreachable padding
        (0x0C0E2B24, 0x0C08F8E0, 'dbl_sp'),      # item type table: small power-up collect
        (0x0C0E2B44, 0x0C08FC00, 'dbl_bp'),      #   big power-up collect
        (0x0C0E2B64, 0x0C08FCC0, 'dbl_sb'),      #   small bomb collect
        (0x0C0E2B84, 0x0C08FF20, 'dbl_bb'),      #   big bomb collect  #   second part starts at row 15 (was 16)
    ]
    if ram is not None:
        for a, old, _ in sites:
            assert rd(a) == old, hex(a)
    return sites

MENU_COL = 23   # top line of the menu (text-layer column; game draws the mode name at column 20, row 11)
MENU_ROW = 9
ARROW = 0x3E
SRC = r'''
; ---------- patcher: runs once after boot unpacks the program ----------
patcher:
  mov.l LP_SITES,r4
ploop:
  mov.l @r4+,r1
  tst r1,r1
  bt pdone
  mov.l @r4+,r5
  mov.l @r4+,r6
  mov.l @r1,r2
  cmp/eq r5,r2
  bf ploop
  bra ploop
  mov.l r6,@r1
pdone:
  mov.l LP_MAIN,r0
  jmp @r0
  nop
  .align 4
LP_SITES: .long sites
LP_MAIN: .long 0x0C0603D0

; ---------- unlock: title screen hook, marks both hidden modes as unlocked (as if the codes were entered) ----------
unlock:
  mov #1,r0
  mov.l LU_HARA,r1
  mov.l r0,@r1
  mov.l LU_MANP,r1
  mov.l r0,@r1
  mov.l LU_ORIG,r0
  jmp @r0
  nop
  .align 4
LU_HARA: .long 0x0C4824AC
LU_MANP: .long 0x0C4EAC40
LU_ORIG: .long 0x0C061070

; ---------- menu: replaces the title's hold-Up/Down mode check (jumped to from 0C06CF06, only reached with credits) ----------
; selection 0 = ARCADE, 1 = HARAHARA, 2 = MANPUKU; Up/Down presses (edge byte 0C481F3C) move the arrow
menu:
  mov.l LM_SEL,r1
  mov.l @r1,r3
  mov r3,r5
  mov.l LM_EDGE,r2
  mov.b @r2,r0
  mov r0,r2
  tst #1,r0
  bt m_noup
  add #-1,r3
  cmp/pz r3
  bt m_noup
  mov #0,r3
m_noup:
  mov r2,r0
  tst #2,r0
  bt m_nodn
  add #1,r3
  mov #4,r0
  cmp/gt r0,r3
  bf m_nodn
  mov #4,r3
m_nodn:
  mov.l r3,@r1
; V1.01 flag and drain-rate table pointers follow the selection
  mov #0,r2
  mov.l LM_DRAIN0,r6
  mov.l LM_MED0,r7
  mov r3,r0
  cmp/eq #3,r0
  bt m_isv
  cmp/eq #4,r0
  bf m_notv
m_isv:
; V1.01+ and ARRANGE (which starts as V1.01+)
  mov #1,r2
  mov.l LM_DRAIN2,r6
  mov.l LM_MED2,r7
m_notv:
; V1.01+: the every-40th-kill medal (8th step of the small-enemy drop list) becomes a power-up like the other steps
  mov.l LM_MLIT,r0
  mov.l r7,@r0
  mov.l LM_FLAG,r0
  mov.l r2,@r0
  mov #0,r2
  mov.l r2,@(4,r0)
; ARRANGE flag (0C04F830) = selection 4
  mov r3,r0
  cmp/eq #4,r0
  movt r2
  mov.l LM_ARR,r0
  mov.l r2,@r0
  mov.l LM_DLIT1,r0
  mov.l r6,@r0
  mov.l LM_DLIT2,r0
  mov.l r6,@r0
  cmp/eq r3,r5
  bt m_go
  mov.l LM_SOUND,r0
  jsr @r0
  mov #37,r4
m_go:
  mov.l LM_HELD,r10
  mov.l LM_SEL,r1
  mov.l @r1,r0
  cmp/eq #1,r0
  bt m_hara
  cmp/eq #2,r0
  bt m_manp
  mov.l LM_ARCADE,r0
  jmp @r0
  nop
m_hara:
  mov.l LM_HARA,r0
  jmp @r0
  nop
m_manp:
  mov.l LM_MANP,r0
  jmp @r0
  nop
  .align 4
LM_SEL: .long 0x0C04F824
LM_EDGE: .long 0x0C481F3C
LM_HELD: .long 0x0C481EFC
LM_SOUND: .long 0x0C088CC0
LM_ARCADE: .long 0x0C06CF1C
LM_HARA: .long 0x0C06D720
LM_MANP: .long 0x0C06D770
LM_FLAG: .long 0x0C04F828
LM_DRAIN0: .long 0x0C0E27B8
LM_DRAIN2: .long drain2
LM_DLIT1: .long 0x0C078648
LM_DLIT2: .long 0x0C078818
drain2: .long 0x0A0E0C00, 0x10160707, 0x50000000, 0x01020102
LM_MLIT: .long 0x0C080B30
LM_ARR: .long 0x0C04F830
LM_MED0: .long 0x0C0E3110
LM_MED2: .long nomedal
nomedal: .long 0x00000000, 0x00000000

; ---------- menudraw: replaces the title's mode-name draw (0C077BD0); draws the 3-line menu with an arrow ----------
menudraw:
  mov.l LD_SEL,r1
  mov.l @r1,r3
  mova MENU_TXT,r0
  mov r0,r5
  mov.l LD_CELL,r2
  mov.l LD_COLOR,r7
  mov #0,r4
d_line:
  mov #32,r0
  cmp/eq r3,r4
  bf d_noarrow
  mov #ARROW,r0
d_noarrow:
  or r7,r0
  mov.l r0,@r2
  mov #32,r0
  or r7,r0
  mov.l r0,@(4,r2)
  mov r2,r6
  add #8,r6
  mov #8,r1
d_ch:
  mov.b @r5+,r0
  or r7,r0
  mov.l r0,@r6
  dt r1
  bf/s d_ch
  add #4,r6
  add #-120,r2
  add #1,r4
  mov r4,r0
  cmp/eq #5,r0
  bf d_line
  mov.l LD_DIRTY,r2
  mov #1,r0
  mov.l r0,@r2
  mov.l r0,@(8,r2)
  mov.l r0,@(16,r2)
  mov.l r0,@(24,r2)
  rts
  mov.l r0,@(32,r2)
  .align 4
LD_SEL: .long 0x0C04F824
LD_CELL: .long CELL_TOP
LD_COLOR: .long 0x60308000
LD_DIRTY: .long DIRTY_BOTTOM
MENU_TXT: .long 0x41524341, 0x44452020, 0x48415241, 0x48415241, 0x4D414E50, 0x554B5520, 0x56312E30, 0x312B2020, 0x41525241, 0x4E474520

; ---------- V1.01: lard pickup (jumped to from 0C09082A; r1 = meter, r12 = meter address) ----------
lardadd:
  mov.l LA_FLAG,r0
  mov.l @r0,r0
  tst r0,r0
  bt la_one
  add #1,r1
la_one:
  add #1,r1
  mov #104,r0
  cmp/ge r0,r1
  bt la_full
  mov.w r1,@r12
  mov.l LA_RET,r0
  jmp @r0
  nop
la_full:
  mov r0,r1
  mov.w r1,@r12
  mov.l LA_FULL,r0
  jmp @r0
  nop
  .align 4
LA_FLAG: .long 0x0C04F828
LA_RET: .long 0x0C090834
LA_FULL: .long 0x0C090850

; ---------- V1.01+: releasing B leaves lard form and keeps the meter (jumped to from 0C0785AC via r3; r0 = r1 = held buttons, r4 = player struct) ----------
; returns to 0C0785BE with r3 = 1 to take the game's own "leave lard form" path (normally pressing A)
hookB:
  tst #32,r0
  bf hb_zero
  mov.l HB_FLAG,r2
  mov.l @r2,r2
  tst r2,r2
  bt hb_orig
  mov.l @r4,r2
  mov.w HB_MECH,r3
  tst r3,r2
  bf hb_exit
; not in lard form yet (options still moving, or an empty-meter lard shot): stop as well if the lard shot is on
  mov.w HB_FIRE,r0
  mov.b @(r0,r4),r2
  tst r2,r2
  bt hb_orig
hb_exit:
  mov.w HB_LARD,r0
  mov.w @(r0,r4),r2
  mov.w HB_KEEP,r0
  mov.w r2,@(r0,r4)
  bra hb_back
  mov #1,r3
hb_orig:
  mov r1,r0
  tst #16,r0
  mov #0,r3
  bt hb_back
  bra hb_back
  mov #1,r3
hb_zero:
  mov #0,r3
hb_back:
  mov.l HB_RET,r2
  jmp @r2
  nop
  .align 4
HB_FLAG: .long 0x0C04F828
HB_RET: .long 0x0C0785BE
HB_MECH: .word 0x2000
HB_LARD: .word 0x020E
HB_KEEP: .word 0x0212
HB_FIRE: .word 0x020A

; ---------- V1.01+: power-up and bomb pickups count twice (item collect handlers in the type table point here) ----------
dbl_sp:
  mov.l DB_SP,r0
  bra dbl
  nop
dbl_bp:
  mov.l DB_BP,r0
  bra dbl
  nop
dbl_sb:
  mov.l DB_SB,r0
  bra dbl
  nop
dbl_bb:
  mov.l DB_BB,r0
  bra dbl
  nop
dbl:
  mov.l DB_FLAG,r1
  mov.l @r1,r1
  tst r1,r1
  bf dbl_go
  jmp @r0
  nop
dbl_go:
  mov.l r8,@-r15
  mov.l r9,@-r15
  mov.l r10,@-r15
  sts.l pr,@-r15
  mov r4,r8
  mov r5,r9
  mov r0,r10
  jsr @r10
  nop
  mov r8,r4
  jsr @r10
  mov r9,r5
  lds.l @r15+,pr
  mov.l @r15+,r10
  mov.l @r15+,r9
  rts
  mov.l @r15+,r8
  .align 4
DB_FLAG: .long 0x0C04F828
DB_SP: .long 0x0C08F8E0
DB_BP: .long 0x0C08FC00
DB_SB: .long 0x0C08FCC0
DB_BB: .long 0x0C08FF20

; ---------- V1.01+: end-of-loop decision (jumped to from 0C076ACA via r4; r3 = 0C48201C loop counter, r0 = 0, r14 already set) ----------
; V1.01+ loop index (0C04F82C): 0 = loop 1, 1 = loop 2, 2 = loop 3 (Manpuku rules)
loopchk:
  mov.l LC_FLAG,r2
  mov.l @r2,r2
  tst r2,r2
  bf lc_v101
  mov.l @r3,r2
  tst r2,r2
  bf lc_end
  mov.l LC_MISS,r4
  mov.b @r4,r2
  tst r2,r2
  bf lc_end
  mov.l LC_CONT,r2
  jmp @r2
  nop
lc_end:
  mov.l LC_END,r2
  jmp @r2
  nop
lc_v101:
  mov.l LC_IDX,r6
  mov.l @r6,r0
  cmp/eq #0,r0
  bt lc_l2
  cmp/eq #1,r0
  bt lc_l3
; after loop 3: put the mode back to Arcade (score goes to the same ranking as the rest of V1.01+), then ending
  mov #0,r0
  mov.l LC_MODE1,r2
  mov.l r0,@r2
  mov.l LC_MODE2,r2
  mov.b r0,@r2
  mov.l LC_MODE3,r2
  mov.b r0,@r2
  bra lc_end
  nop
lc_l2:
  mov #1,r0
  mov.l r0,@r6
  mov.l @r3,r5
  bra lc_next
  add #1,r5
lc_l3:
  mov #2,r0
  mov.l r0,@r6
  mov #1,r0
  mov.l LC_MODE1,r2
  mov.l r0,@r2
  mov.l LC_MODE2,r2
  mov.b r0,@r2
  mov.l LC_MODE3,r2
  mov.b r0,@r2
  mov #0,r5
lc_next:
; same as the game's loop branch (0C076B20) but without setting the extend step to -1
  mov.l LC_LOOP,r4
  mov #-1,r1
  mov #8,r7
  mov.l LC_F598,r6
  mov.l r7,@r6
  mov.l LC_SUB,r0
  jsr @r0
  mov.l r5,@r4
  mov.l LC_TAIL,r0
  jmp @r0
  nop
  .align 4
LC_FLAG: .long 0x0C04F828
LC_IDX: .long 0x0C04F82C
LC_MISS: .long 0x0C515C4C
LC_CONT: .long 0x0C076AD8
LC_END: .long 0x0C076AF0
LC_LOOP: .long 0x0C48201C
LC_F598: .long 0x0C48F598
LC_SUB: .long 0x0C0701B0
LC_TAIL: .long 0x0C076AFA
LC_MODE1: .long 0x0C4EAC3C
LC_MODE2: .long 0x0C48227F
LC_MODE3: .long 0x0C516FDC

; ---------- V1.01+: stage-side copy of the loop check (jumped to from 0C0965C2 via r3; r0 must be kept). Runs before loopchk. ----------
loopchk2:
  mov.l L2_FLAG,r3
  mov.l @r3,r3
  tst r3,r3
  bf l2_v101
  mov.l L2_MISS,r3
  mov.b @r3,r2
  tst r2,r2
  bf l2_end
  mov.l L2_CONT,r3
  jmp @r3
  nop
l2_v101:
  mov.l L2_IDX,r3
  mov.l @r3,r3
  mov #2,r2
  cmp/hs r2,r3
  bt l2_end
  mov.l L2_LOOP2,r3
  jmp @r3
  nop
l2_end:
  mov.l L2_END,r3
  jmp @r3
  nop
  .align 4
L2_FLAG: .long 0x0C04F828
L2_IDX: .long 0x0C04F82C
L2_MISS: .long 0x0C515C4C
L2_CONT: .long 0x0C0965C8
L2_END: .long 0x0C0965E0
L2_LOOP2: .long 0x0C0965E4

; ---------- in-game mode label (replaces the call at 0C0700DE to 0C077BD0: r4 = mode, r5 = column, r6 = row) ----------
modelabel:
  mov.l ML_FLAG,r0
  mov.l @r0,r0
  tst r0,r0
  bt ml_orig
  mov #30,r0
  mulu.w r0,r5
  sts macl,r1
  add r6,r1
  shll2 r1
  mov.l ML_CELLS,r2
  add r1,r2
  mova ML_TXT,r0
  mov r0,r3
  mov.l ML_ARR,r0
  mov.l @r0,r0
  tst r0,r0
  bt ml_v101
  add #8,r3
ml_v101:
  mov.l ML_COLOR,r7
  mov #8,r1
ml_ch:
  mov.b @r3+,r0
  or r7,r0
  mov.l r0,@r2
  dt r1
  bf/s ml_ch
  add #4,r2
  mov r5,r0
  shll2 r0
  add r0,r0
  mov.l ML_DIRTY,r2
  add r0,r2
  mov #1,r0
  rts
  mov.l r0,@r2
ml_orig:
  mov.l ML_ORIG,r0
  jmp @r0
  nop
  .align 4
ML_FLAG: .long 0x0C04F828
ML_CELLS: .long 0x0C483A50
ML_COLOR: .long 0x60308000
ML_DIRTY: .long 0x0C4EAC98
ML_ORIG: .long 0x0C077BD0
ML_ARR: .long 0x0C04F830
ML_TXT: .long 0x56312E30, 0x312B2020, 0x41525241, 0x4E474520

; ---------- wrapper: replaces calls to the text-layer redraw ----------
wrapper:
  mov #0,r0
  mov.l LW_SEL,r1
  mov.l r0,@r1
  sts.l pr,@-r15
  mov.l r4,@-r15
  mov.l r5,@-r15
  mov.l r6,@-r15
  mov.l r7,@-r15
  mov.l LW_TIMER,r0
  jsr @r0
  nop
  mov.l LW_AHUD,r0
  jsr @r0
  nop
  mov.l @r15+,r7
  mov.l @r15+,r6
  mov.l @r15+,r5
  mov.l @r15+,r4
  lds.l @r15+,pr
  mov.l LW_ORIG,r0
  jmp @r0
  nop
  .align 4
LW_TIMER: .long timer
LW_AHUD: .long ahud
LW_SEL: .long 0x0C04F824
LW_ORIG: .long 0x0C061070

; ---------- ARRANGE HUD (1-player mode): "2p" becomes FEVER, the 2P score shows the counter (0C04F834), no 2P join ----------
ahud:
  mov.l AH_ARR,r0
  mov.l @r0,r0
  tst r0,r0
  bf ah_on
  rts
  nop
ah_on:
; hide the 2P Start button (bit 0x80 of the P2 input copies)
  mova AH_P2IN,r0
  mov r0,r6
  mov #6,r7
  mov #127,r4
ah_blk:
  mov.l @r6+,r2
  mov.b @r2,r0
  and r4,r0
  mov.b r0,@r2
  dt r7
  bf ah_blk
; column 39 rows 21-25: FEVER (same colour as the 2p label)
  mov.l AH_C39,r2
  mov.l AH_LCOL,r7
  mova AH_FTXT,r0
  mov r0,r5
  mov #5,r1
ah_f:
  mov.b @r5+,r0
  or r7,r0
  mov.l r0,@r2
  dt r1
  bf/s ah_f
  add #4,r2
; columns 36-37 rows 19-29: blank the 2P join prompts
  mov.l AH_C36,r2
  mov.l AH_BLANK,r0
  mov #11,r1
ah_b:
  mov.l r0,@r2
  mov r2,r3
  add #120,r3
  mov.l r0,@r3
  dt r1
  bf/s ah_b
  add #4,r2
; column 38 rows 20-29: counter, right-aligned, 10 digits, leading blanks
  mov.l AH_CNT,r0
  mov.l @r0,r3
  mov.l AH_C38,r2
  mov.l AH_SCOL,r7
  mova AH_POW,r0
  mov r0,r5
  mov #10,r1
  mov #0,r6
ah_d:
  mov.l @r5+,r4
  mov #48,r0
ah_sub:
  cmp/hs r4,r3
  bf ah_dig
  sub r4,r3
  bra ah_sub
  add #1,r0
ah_dig:
  mov r0,r4
  mov #48,r0
  cmp/eq r0,r4
  bf ah_nz
  tst r6,r6
  bf ah_put
  mov r1,r0
  cmp/eq #1,r0
  bt ah_zero
  mov #32,r4
  bra ah_put
  nop
ah_zero:
  mov #48,r4
  bra ah_put
  nop
ah_nz:
  mov #1,r6
ah_put:
  mov r4,r0
  or r7,r0
  mov.l r0,@r2
  dt r1
  bf/s ah_d
  add #4,r2
; redraw columns 36-39
  mov.l AH_DIRTY,r2
  mov #1,r0
  mov.l r0,@r2
  mov.l r0,@(8,r2)
  mov.l r0,@(16,r2)
  rts
  mov.l r0,@(24,r2)
  .align 4
AH_ARR: .long 0x0C04F830
AH_CNT: .long 0x0C04F834
AH_C39: .long 0x0C484CEC
AH_C38: .long 0x0C484C70
AH_C36: .long 0x0C484B7C
AH_DIRTY: .long 0x0C4EADB8
AH_LCOL: .long 0x60308000
AH_SCOL: .long 0x80808000
AH_BLANK: .long 0x80602020
AH_P2IN: .long 0x0C481DF9, 0x0C481E39, 0x0C481E79, 0x0C481EFD, 0x0C481F3D, 0x0C481F7D
AH_POW: .long 1000000000, 100000000, 10000000, 1000000, 100000, 10000, 1000, 100, 10, 1
AH_FTXT: .long 0x46455645, 0x52000000

; ---------- timer: find timed boss/midboss, draw seconds remaining ----------
timer:
  mov.l r8,@-r15
  mov.l r9,@-r15
  mov.l r10,@-r15
  mov.l r11,@-r15
  sts.l pr,@-r15
  mov.l LT_STATE,r10
  mov #0,r0
  mov.l r0,@(32,r10)
  mov.l LT_ENEMY,r9
  mov #96,r11
  add r11,r11
sloop:
  mov.l @r9,r0
  tst r0,r0
  bt snext
  mov.l @(4,r9),r1
  mov.l LT_TABLE,r8
tloop:
  mov.l @r8,r2
  tst r2,r2
  bt snext
  cmp/eq r1,r2
  bt found
  add #72,r8
  bra tloop
  nop
snext:
  mov #100,r0
  add r0,r0
  add r0,r9
  dt r11
  bf sloop
; nothing timed on screen: clear our cells once
clear:
  mov.l LT_STATE,r10
  mov.l @(32,r10),r0
  tst r0,r0
  bf keep16
  mov.l r0,@(16,r10)
keep16:
  mov #0,r0
  mov.l r0,@(28,r10)
  mov.l @(12,r10),r0
  tst r0,r0
  bf clr_do
  bra tdone
  nop
clr_do:
  mov #0,r0
  mov.l r0,@(12,r10)
  mov #32,r1
  mov r1,r2
  mov r1,r3
  mov r1,r4
  mov r1,r5
  mov.l LT_CELL0,r6
  mov.l LT_DIRTY0,r7
  bsr draw
  nop
  mov #32,r1
  mov r1,r2
  mov r1,r3
  mov r1,r4
  mov r1,r5
  mov.l LT_CELL1,r6
  mov.l LT_DIRTY1,r7
  bsr draw
  nop
  bra tdone
  nop
found:
  mov.l LT_STATE,r10
  mov.l @(16,r10),r0
  cmp/eq r8,r0
  bf f_go
  mov #1,r0
  mov.l r0,@(32,r10)
f_go:
  mov.w @(4,r8),r0
  extu.w r0,r0
  mov.l @(r0,r9),r6
  mov.b @(15,r9),r0
  mov r0,r2
  mov.w @(6,r8),r0
  mov.b @(r0,r9),r3
  mov r8,r1
  add #12,r1
rloop:
  mov.w @(2,r1),r0
  extu.w r0,r5
  tst r5,r5
  bt nomatch
  mov.b @r1,r0
  cmp/eq #-1,r0
  bt s0ok
  cmp/eq r2,r0
  bf rnext
s0ok:
  mov.b @(1,r1),r0
  cmp/eq #-1,r0
  bt rmatch
  cmp/eq r3,r0
  bt rmatch
rnext:
  add #12,r1
  bra rloop
  nop
nomatch:
  bra snext
  nop
rmatch:
  mov.l LT_STATE,r10
  mov.l r1,@(24,r10)
  mov.w @(8,r8),r0
  tst r0,r0
  bt mode0
  mov.l LT_STATE,r10
  mov.l LT_FCOUNT,r0
  mov.l @r0,r7
  mov.l @(16,r10),r0
  cmp/eq r8,r0
  bt m1have
  mov.l r8,@(16,r10)
  mov.l r7,@(20,r10)
m1have:
  mov.l @(20,r10),r0
  mov r7,r6
  sub r0,r6
mode0:
  mov r5,r1
  sub r6,r1
  cmp/pz r1
  bt rpos
  mov.w @(8,r8),r0
  tst r0,r0
  bt snext
  mov #0,r1
rpos:
  mov.l LT_DIV6,r0
  mulu.w r0,r1
  sts macl,r1
  shlr16 r1
  shlr2 r1
  mov r1,r4
  bsr div10
  nop
  mov r0,r7
  bsr div10
  nop
  mov r0,r6
  bsr div10
  nop
  mov r0,r2
  mov r4,r3
  mov #48,r0
  tst r3,r3
  bt h_sp
  add r0,r3
  bra h_ok
  nop
h_sp:
  mov #32,r3
h_ok:
  mov #32,r1
  cmp/eq r1,r3
  bf t_dig
  tst r2,r2
  bt t_sp
t_dig:
  add r0,r2
  bra t_ok
  nop
t_sp:
  mov #32,r2
t_ok:
  add r0,r6
  add r0,r7
  mov r3,r1
  mov r6,r3
  mov #46,r4
  mov r7,r5
  mov.l LT_CELL0,r6
  mov.l LT_DIRTY0,r7
  bsr draw
  nop
; ---- health: sum slot+0x44 of this enemy's listed parts
  mov.l LT_STATE,r10
  mov.l @(24,r10),r7
  add #4,r7
  mov.l @r8,r2
  mov #0,r3
  mov #0,r1
  mov.l LT_ENEMY,r4
  mov #96,r5
  add r5,r5
hloop:
  mov.l @r4,r0
  tst r0,r0
  bt hnext
  mov.l @(4,r4),r0
  cmp/eq r2,r0
  bf hnext
  mov.b @(15,r4),r0
  mov r0,r6
  mov r7,r9
hcmp:
  mov.b @r9+,r0
  cmp/eq #-1,r0
  bt hnext
  cmp/eq r6,r0
  bf hcmp
hadd:
  mov.w @(10,r8),r0
  extu.w r0,r0
  tst r0,r0
  bt hok
  mov.l @r4,r6
  tst r0,r6
  bt hnext
hok:
  add #1,r1
  mov #68,r0
  mov.w @(r0,r4),r0
  cmp/pz r0
  bf hnext
  add r0,r3
hnext:
  mov #100,r0
  add r0,r0
  add r0,r4
  dt r5
  bf hloop
  tst r1,r1
  bf hp_have
  mov.l @(24,r10),r0
  mov.l @(28,r10),r2
  cmp/eq r0,r2
  bt hp_digits
  mov #32,r1
  mov r1,r2
  mov r1,r3
  mov r1,r4
  mov r1,r5
  mov.l LT_CELL1,r6
  mov.l LT_DIRTY1,r7
  bsr draw
  nop
  bra hp_done
  nop
hp_have:
  mov.l @(24,r10),r0
  mov.l r0,@(28,r10)
hp_digits:
  mov r3,r4
  bsr div10
  nop
  mov r0,r6
  bsr div10
  nop
  mov r0,r5
  mov #48,r0
  tst r4,r4
  bt hp_h_sp
  mov r4,r2
  add r0,r2
  bra hp_h_ok
  nop
hp_h_sp:
  mov #32,r2
hp_h_ok:
  tst r4,r4
  bf hp_t_dig
  tst r5,r5
  bt hp_t_sp
hp_t_dig:
  add r0,r5
  bra hp_t_ok
  nop
hp_t_sp:
  mov #32,r5
hp_t_ok:
  add r0,r6
  mov r5,r3
  mov r6,r4
  mov #32,r1
  mov #32,r5
  mov.l LT_CELL1,r6
  mov.l LT_DIRTY1,r7
  bsr draw
  nop
hp_done:
  mov.l LT_STATE,r10
  mov #1,r0
  mov.l r0,@(12,r10)
tdone:
  lds.l @r15+,pr
  mov.l @r15+,r11
  mov.l @r15+,r10
  mov.l @r15+,r9
  mov.l @r15+,r8
  rts
  nop

; r4 -> r4 = r4/10, r0 = r4%10   (clobbers r1, r2)
div10:
  mov.l LT_DIV10,r1
  mov r4,r2
  mulu.w r1,r2
  sts macl,r1
  shlr16 r1
  shlr2 r1
  shlr r1
  mov r1,r0
  shll2 r0
  add r1,r0
  add r0,r0
  mov r4,r2
  sub r0,r2
  mov r1,r4
  rts
  mov r2,r0

; draw chars r1..r5 into 5 consecutive text cells at r6, then set the column redraw flag at r7
draw:
  mov.l LT_COLOR,r0
  or r0,r1
  mov.l r1,@r6
  or r0,r2
  mov.l r2,@(4,r6)
  or r0,r3
  mov.l r3,@(8,r6)
  or r0,r4
  mov.l r4,@(12,r6)
  or r0,r5
  mov.l r5,@(16,r6)
  mov #1,r0
  rts
  mov.l r0,@r7

WT_NSLOT: .word 192
WT_STRIDE: .word 200
WT_SUB: .word 0xB4
WT_HP: .word 0x44
  .align 4
LT_ENEMY: .long 0x0C4B7C9C
LT_TABLE: .long enemy_table
LT_STATE: .long 0x0C04F800
LT_DIV6: .long 0x0000AAAB
LT_DIV10: .long 0x0000CCCD
LT_CELL0: .long 0x0C484B60
LT_DIRTY0: .long 0x0C4EADB8
LT_CELL1: .long 0x0C484AE8
LT_DIRTY1: .long 0x0C4EADB0
LT_MAINBIT: .long 0x00008000
LT_COLOR: .long 0x80808000
LT_FCOUNT: .long 0x0C4857C4   ; gameplay update-step counter (stops while paused); was 0C516FD0
'''

def main():
    sites = patch_sites(open(RAM_DUMP, 'rb').read() if RAM_DUMP else None)
    cell_top = 0x0C483A50 + (MENU_COL * 30 + MENU_ROW) * 4
    dirty_bottom = 0x0C4EAC98 + (MENU_COL - 4) * 8
    body = SRC.replace('CELL_TOP', hex(cell_top)).replace('DIRTY_BOTTOM', hex(dirty_bottom)).replace('#ARROW', f'#{ARROW}')
    src = body + table_src() + warn_src() + '  .align 4\nsites:\n' + ''.join(f'  .long 0x{a:08x}, 0x{o:08x}, {t}\n' for a, o, t in sites) + '  .long 0\n'
    code, labels = Asm(RUN_BASE).assemble(src)

    z = zipfile.ZipFile(ORIG_ZIP)
    u4 = bytearray(z.read('u4'))
    be = bytearray(len(u4)); be[0::2] = u4[1::2]; be[1::2] = u4[0::2]
    assert all(b == 0xFF for b in be[ROM_OFF:ROM_OFF + len(code)]), 'target area not blank'
    assert struct.unpack('>I', be[0x1C4:0x1C8])[0] == MAIN
    be[ROM_OFF:ROM_OFF + len(code)] = code
    be[0x1C4:0x1C8] = struct.pack('>I', labels['patcher'])
    sw = bytearray(len(be)); sw[0::2] = be[1::2]; sw[1::2] = be[0::2]
    with zipfile.ZipFile(OUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as o:
        for n in z.namelist():
            o.writestr(n, bytes(sw) if n == 'u4' else z.read(n))
    print('code bytes', len(code), 'patcher at', hex(labels['patcher']), 'wrapper', hex(labels['wrapper']),
          'timer', hex(labels['timer']), 'u4 crc', hex(zlib.crc32(bytes(sw))))
    return labels

if __name__ == '__main__':
    main()
