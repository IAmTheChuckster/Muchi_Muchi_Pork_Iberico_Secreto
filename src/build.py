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

ROM_OFF = 0x1F0000            # blank (0xFF) area in the program ROM where the patch is stored
ROM_ADDR = 0x80000000 | ROM_OFF   # its address as seen by the CPU
RUN_BASE = 0x0C04C000         # the patch runs from RAM here (unused by the game; 0C04F800+ is the patch's own RAM)
RUN_LIMIT = 0x0C04F800
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
        (0x0C0E2B84, 0x0C08FF20, 'dbl_bb'),      #   big bomb collect
        (0x0C0E2BC4, 0x0C090000, 'medcol'),      # ARRANGE: medal collect -> FEVER counter
        (0x0C078300, 0x6073C940, '0x6073D02A'),  # bomb check: mov r7,r0 / mov.l @(0C0783AC),r0
        (0x0C078304, 0x20088949, '0x402B6073'),  #   jmp @r0 / mov r7,r0 (delay: r0 = buttons)
        (0x0C0783AC, 0x00090009, 'bombhook'),    #   literal in unreachable padding after rts
        (0x0C06F994, 0x607288FF, '0xD0B8402B'),  # game loop skip test -> mov.l @(0C06FC78),r0 / jmp @r0
        (0x0C06F998, 0x8D6BEA00, '0x0009EA00'),  #   nop (delay slot); fevspeed decides skip or run
        (0x0C074598, 0x0C07DDF0, 'hithook'),     # ARRANGE+: player-hit call (tail jump) -> a hit in Fever ends Fever instead
        (0x0C0748FC, 0x0C07DDF0, 'hithook'),     #   second player-hit call
        (0x0C06FC78, 0x00090009, 'fevspeed'),
        (0x0C0D7528, 0x0C4EAC3C, '0x0C04F888'),  # revenge-bullet routine 0C0D74E0: its "mode == Manpuku" test reads our flag    #   literal in padding after the literal pool  #   second part starts at row 15 (was 16)
    ]
    if ram is not None:
        for a, old, _ in sites:
            assert rd(a) == old, hex(a)
    return sites

FEVER_SPEED = 100   # unused: Fever speed follows the enemy bullet count (fevspeed)
MENU_COL = 23   # top line of the menu (text-layer column; game draws the mode name at column 20, row 11)
MENU_ROW = 9
ARROW = 0x3E
SRC = r'''
; ---------- patcher: runs once after boot unpacks the program ----------
patcher:
; clear the patch's own RAM (0C04F800-0C04FFFF) on every boot and reset: a reset (test button) or a MiSTer
; power-on can leave old values there, MAME starts with zeros
  mov.l LP_RAM,r1
  mov.w LP_RAMN,r2
  mov #0,r0
pclr:
  mov.l r0,@r1
  dt r2
  bf/s pclr
  add #4,r1
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
LP_RAM: .long 0x0C04F800
LP_RAMN: .word 512
  .align 4

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
; new game from the title menu: clear the ARRANGE+ FEVER state (0C04F834..0C04F87F); a continue never comes here
  mov.l LM_FST,r1
  mov #19,r2
  mov #0,r0
m_clr:
  mov.l r0,@r1
  dt r2
  bf/s m_clr
  add #4,r1
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
LM_FST: .long 0x0C04F834
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
MENU_TXT: .long 0x41524341, 0x44452020, 0x48415241, 0x48415241, 0x4D414E50, 0x554B5520, 0x56312E30, 0x312B2020, 0x41525241, 0x4E47452B

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
; V1.01+ is two loops, ARRANGE+ one: after that the ending
  mov.l LC_ARR,r6
  mov.l @r6,r0
  tst r0,r0
  bf lc_end
  mov.l LC_IDX,r6
  mov.l @r6,r0
  cmp/eq #0,r0
  bt lc_l2
  bra lc_end
  nop
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
LC_ARR: .long 0x0C04F830
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
  mov.l L2_ARR,r3
  mov.l @r3,r3
  tst r3,r3
  bf l2_end
  mov.l L2_IDX,r3
  mov.l @r3,r3
  mov #1,r2
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
L2_ARR: .long 0x0C04F830
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
  rts
  nop
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
ML_TXT: .long 0x56312E30, 0x312B2020, 0x41525241, 0x4E47452B

; ---------- wrapper: replaces calls to the text-layer redraw ----------
wrapper:
  mov #0,r0
  mov.l LW_SEL,r1
  mov.l r0,@r1
; ARRANGE+ display and revenge flag only during play: the player state byte is 00 before a game and 80/C0 on
; the start and character select screens, which then run exactly as in V1.01+
  mov.l LW_P1,r1
  mov.b @r1,r0
  tst r0,r0
  bt lw_idle
  cmp/eq #-128,r0
  bt lw_idle
  cmp/eq #-64,r0
  bt lw_idle
; revenge bullets (enemies fire when destroyed): on in Manpuku as in the original, and in ARRANGE+ while the
; FEVER counter is full or Fever is on
  mov.l LW_MODE,r1
  mov.l @r1,r0
  cmp/eq #1,r0
  bt lw_rv1
  mov.l LW_ARR,r1
  mov.l @r1,r0
  tst r0,r0
  bt lw_rv0
  mov.l LW_FEV,r1
  mov.l @r1,r0
  tst r0,r0
  bf lw_rv1
  mov.l LW_CNT,r1
  mov.l @r1,r0
  mov.l LW_MAX,r1
  cmp/hs r1,r0
  bf lw_rv0
lw_rv1:
  bra lw_rvs
  mov #1,r0
lw_rv0:
  mov #0,r0
lw_rvs:
  mov.l LW_RV,r1
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
lw_back:
  mov.l @r15+,r7
  mov.l @r15+,r6
  mov.l @r15+,r5
  mov.l @r15+,r4
  lds.l @r15+,pr
  mov.l LW_ORIG,r0
  jmp @r0
  nop
; not playing: boss timer only (as in the other modes)
lw_idle:
  sts.l pr,@-r15
  mov.l r4,@-r15
  mov.l r5,@-r15
  mov.l r6,@-r15
  mov.l r7,@-r15
  mov.l LW_TIMER,r0
  jsr @r0
  nop
  bra lw_back
  nop
  .align 4
LW_TIMER: .long timer
LW_AHUD: .long ahud
LW_SEL: .long 0x0C04F824
LW_ORIG: .long 0x0C061070
LW_MODE: .long 0x0C4EAC3C
LW_ARR: .long 0x0C04F830
LW_FEV: .long 0x0C04F838
LW_RV: .long 0x0C04F888
LW_P1: .long 0x0C510B28
LW_CNT: .long 0x0C04F834
LW_MAX: .long 10000

; ---------- ARRANGE HUD: the FEVER bar (0C04F834) under the 1P lives; 2P works as normal ----------
ahud:
  mov.l AH_ARR,r0
  mov.l @r0,r0
  tst r0,r0
  bf ah_on
  rts
  nop
ah_on:
  sts.l pr,@-r15
  mov.l AH_FX,r0
  jsr @r0
  nop
  lds.l @r15+,pr
; full 2P: the 2P label, score, join prompts and inputs are left alone.
; column 35 rows 0-7 (under the 1P lives icon): the FEVER bar, 64 pixels (counter * 64 / 10000), built from
; the font's 1-8 pixel blocks (codes 16-23); blue while below 10000 (filling or draining), red when full
  mov.l AH_CNT,r0
  mov.l @r0,r3
  mov.l AH_BLUE,r7
  mov.w AH_10K,r0
  cmp/hs r0,r3
  bf ah_blu
  mov.l AH_RED,r7
ah_blu:
  shll2 r3
  add r3,r3
  mov #0,r4
  mov.w AH_1250,r1
ah_q:
  cmp/hs r1,r3
  bf ah_qd
  sub r1,r3
  bra ah_q
  add #1,r4
ah_qd:
  mov.l AH_BAR,r2
  mov #8,r5
  mov #8,r6
ah_bc:
  cmp/ge r6,r4
  bf ah_bp
  mov #23,r0
  bra ah_bw
  nop
ah_bp:
  cmp/pl r4
  bt ah_bpt
  mov #32,r0
  bra ah_bw
  nop
ah_bpt:
  mov r4,r0
  add #15,r0
ah_bw:
  or r7,r0
  mov.l r0,@r2
  add #4,r2
  add #-8,r4
  dt r5
  bf ah_bc
; column 34 rows 0-13 (under the bar): FEVER READY in yellow while the counter is full, flashing
; (16 frames on, 16 off, from the vblank count); blank otherwise
  mov.l AH_CNT,r0
  mov.l @r0,r3
  mov.w AH_10K,r0
  mov #0,r6
  cmp/hs r0,r3
  bf ah_rdy
  mov.l AH_VBL,r0
  mov.l @r0,r0
  tst #16,r0
  bf ah_rdy
  mov #1,r6
ah_rdy:
  mov.l AH_RDY,r2
  mova AH_RTXT,r0
  mov r0,r5
  mov.l AH_RCOL,r7
  mov #14,r1
ah_rl:
  mov.b @r5+,r0
  extu.b r0,r0
  or r7,r0
  tst r6,r6
  bf ah_rw
  mov #0,r0
ah_rw:
  mov.l r0,@r2
  dt r1
  bf/s ah_rl
  add #4,r2
  mov.l AH_DIRTY34,r2
  mov #1,r0
  mov.l r0,@r2
; redraw column 35
  mov.l AH_DIRTY,r2
  mov #1,r0
  rts
  mov.l r0,@r2
  .align 4
AH_ARR: .long 0x0C04F830
AH_FX: .long arrfx
AH_CNT: .long 0x0C04F834
AH_C39: .long 0x0C484CEC
AH_C38: .long 0x0C484C70
AH_C36F: .long 0x0C484BD4
AH_DIRTY: .long 0x0C4EADB0
AH_BAR: .long 0x0C484AB8
AH_RDY: .long 0x0C484A40
AH_DIRTY34: .long 0x0C4EADA8
AH_VBL: .long 0x0C002310
AH_RTXT: .long 0x46455645, 0x52205245, 0x41445920, 0x20200000
AH_RCOL: .long 0x80801000
AH_BLUE: .long 0x20408000
AH_RED: .long 0x80202000
AH_10K: .word 10000
AH_1250: .word 1250
  .align 4
AH_LCOL: .long 0x60308000
AH_YCOL: .long 0x80602000
AH_SCOL: .long 0x80808000
AH_BLANK: .long 0x80602020
AH_POW: .long 10000, 1000, 100, 10, 1
AH_FTXT: .long 0x46455645, 0x52200000

; ---------- Fever game speed: replaces the game loop's "skip the world update when 0C48A168 == -1" test
; (jumped to from 0C06F996, r7 = 0C48A168). Runs every frame the world could update, so nothing is left stale.
; In Fever an accumulator gives FEVER_SPEED percent: each frame acc += speed, updates = acc / 100;
; 0 updates -> skip, otherwise 0C48A168 = updates - 1 (the loop runs 0C48A168 + 1 times). ----------
fevspeed:
  mov.l SP_ARR,r0
  mov.l @r0,r0
  tst r0,r0
  bt sp_ton
  mov.l SP_FEV,r0
  mov.l @r0,r0
  tst r0,r0
  bf sp_fev
; after Fever ran out: 50% during the end window
  mov.l SP_KIND,r0
  mov.l @r0,r0
  cmp/eq #2,r0
  bf sp_ton
  mov.l SP_FADE,r0
  mov.l @r0,r0
  tst r0,r0
  bf sp_fev
sp_ton:
  bra sp_norm
  nop
sp_fev:
; Fever speed in tenths of a percent from the enemy bullets on screen (n, both bullet lists):
; n <= 100: 1000 - 3n, at most 990 (99% .. 70%), 100 < n < 150: 700 - 4(n - 100) (70% .. 50%), n >= 150: 500
  mov.l r3,@-r15
  mov.l r5,@-r15
  mov.l SP_BPOOL,r1
  mov.w SP_N1,r5
  mov #0,r3
sp_cnt:
  mov.l @r1,r0
  tst r0,r0
  bt sp_c1
  add #1,r3
sp_c1:
  dt r5
  bf/s sp_cnt
  add #92,r1
  mov.l SP_P2,r1
  mov.w SP_N2,r5
sp_cnt2:
  mov.l @r1,r0
  tst r0,r0
  bt sp_c2
  mov.l @(4,r1),r0
  mov.l SP_HLO,r2
  cmp/hs r2,r0
  bf sp_c2
  mov.l SP_HHI,r2
  cmp/hs r2,r0
  bt sp_c2
  add #1,r3
sp_c2:
  mov.w SP_S2,r0
  add r0,r1
  dt r5
  bf sp_cnt2
  mov #100,r0
  cmp/hi r0,r3
  bt sp_hi
  mov r3,r2
  add r2,r2
  add r3,r2
  mov.w SP_1000,r0
  sub r2,r0
; never above 99%
  mov.w SP_990,r2
  cmp/gt r2,r0
  bt sp_acc
  bra sp_acc
  mov r0,r2
sp_hi:
  mov.w SP_150,r0
  cmp/hs r0,r3
  bt sp_min
  add #-100,r3
  shll2 r3
  mov.w SP_700,r2
  bra sp_acc
  sub r3,r2
sp_min:
  mov.w SP_500,r2
sp_acc:
  mov.l @r15+,r5
  mov.l @r15+,r3
; first 4 seconds of Fever (the start window 0C04F87C): a straight 50%, slow motion for the medal burst
  mov.l SP_SWIN,r1
  mov.l @r1,r0
  tst r0,r0
  bf sp_slow
  mov.l SP_FEV,r1
  mov.l @r1,r0
  tst r0,r0
  bf sp_ease
sp_slow:
  mov.w SP_500,r2
  mov.l SP_CUR,r1
  mov.l r2,@r1
sp_ease:
; ease toward the target: the speed moves at most 1% (10 tenths) per call
  mov.l SP_CUR,r1
  mov.l @r1,r0
  mov r2,r4
  cmp/hi r0,r4
  bt sp_up
  add #-10,r0
  cmp/gt r4,r0
  bt sp_st
  bra sp_st
  mov r4,r0
sp_up:
  add #10,r0
  cmp/gt r4,r0
  bf sp_st
  mov r4,r0
sp_st:
  mov.l r0,@r1
  mov r0,r2
; real frames since the last call (vblank count 0C002310), 1..3: the game drops to 30 Hz when busy,
; so the speed is measured against real time, not against game frames
  mov.l SP_VBL,r0
  mov.l @r0,r0
  mov.l SP_LASTV,r1
  mov.l @r1,r4
  mov.l r0,@r1
  sub r4,r0
  mov #1,r4
  cmp/hs r4,r0
  bt sp_e1
  mov #1,r0
sp_e1:
  mov #3,r4
  cmp/hi r4,r0
  bf sp_e2
  mov #3,r0
sp_e2:
  mov r2,r4
sp_m:
  dt r0
  bt sp_md
  bra sp_m
  add r4,r2
sp_md:
  mov.l SP_ACC,r1
  mov.l @r1,r0
  add r2,r0
  mov #0,r2
  mov.w SP_1000,r4
sp_div:
  cmp/hs r4,r0
  bf sp_set
  sub r4,r0
  bra sp_div
  add #1,r2
sp_set:
  mov.l r0,@r1
  tst r2,r2
  bt sp_skip
; at most 2 updates per call
  mov #2,r0
  cmp/hi r0,r2
  bf sp_cap
  mov r0,r2
sp_cap:
  add #-1,r2
  bra sp_go
  mov.l r2,@r7
sp_norm:
; outside Fever the eased speed waits at 99% for the next Fever
  mov.l SP_CUR,r1
  mov.w SP_990,r0
  mov.l r0,@r1
  mov.l @r7,r0
  cmp/eq #-1,r0
  bt sp_skip
  mov #0,r0
  mov.l r0,@r7
sp_go:
  mov #0,r10
  mov.l SP_RUN,r0
  jmp @r0
  nop
sp_skip:
  mov #0,r10
  mov.l SP_SKIP,r0
  jmp @r0
  nop
  .align 4
SP_FEV: .long 0x0C04F838
SP_ARR: .long 0x0C04F830
SP_ACC: .long 0x0C04F850
SP_RUN: .long 0x0C06F99C
SP_SKIP: .long 0x0C06FA72
SP_BPOOL: .long 0x0C4C371C
SP_VBL: .long 0x0C002310
SP_LASTV: .long 0x0C04F870
SP_BCNT: .long 0x0C5108FC
SP_P2: .long 0x0C4EC6F8
SP_CUR: .long 0x0C04F880
SP_SWIN: .long 0x0C04F87C
SP_KIND: .long 0x0C04F88C
SP_FADE: .long 0x0C04F878
SP_HLO: .long 0x0C0D0000
SP_HHI: .long 0x0C0E0000
SP_1000: .word 1000
SP_700: .word 700
SP_500: .word 500
SP_150: .word 150
SP_990: .word 990
SP_N1: .word 1536
SP_N2: .word 256
SP_S2: .word 144
  .align 4

; ---------- ARRANGE+: player hit (tail-jumped to from 0C074486 / 0C074848, r4 = player). During Fever, or with
; the counter full, the hit does not kill: it asks arrfx to end (or start) Fever (same request as the bomb) and gives 90 steps of grace, so the bullet
; or enemy that hit cannot kill straight after. Otherwise the game's hit routine 0C07DDF0 runs as normal. ----------
hithook:
  mov.l HH_ARR,r0
  mov.l @r0,r0
  tst r0,r0
  bt hh_go
  tst r4,r4
  bf hh_go
  mov.l HH_GRACE,r1
  mov.l @r1,r0
  tst r0,r0
  bf hh_skip
  mov.l HH_FEV,r0
  mov.l @r0,r0
  tst r0,r0
  bf hh_req
; not in Fever: with the counter full the hit starts Fever instead
  mov.l HH_CNT,r0
  mov.l @r0,r0
  mov.l HH_MAX,r2
  cmp/hs r2,r0
  bf hh_go
hh_req:
  mov #90,r0
  mov.l r0,@r1
  mov.l HH_REQ,r1
  mov #1,r0
  mov.l r0,@r1
hh_skip:
  rts
  nop
hh_go:
  mov.l HH_HIT,r0
  jmp @r0
  nop
  .align 4
HH_ARR: .long 0x0C04F830
HH_FEV: .long 0x0C04F838
HH_REQ: .long 0x0C04F868
HH_GRACE: .long 0x0C04F86C
HH_HIT: .long 0x0C07DDF0
HH_CNT: .long 0x0C04F834
HH_MAX: .long 10000

; ---------- ARRANGE+: bomb button check (jumped to from 0C078302; r0 = buttons, r8 = player). In ARRANGE+, when the
; FEVER counter is full or Fever is on, C does not bomb: it sets the request flag 0C04F868 for arrfx instead.
; Only r0/r1 are used (the game keeps values in r2-r9 across this check). ----------
bombhook:
  tst #64,r0
  bt bh_none
  mov.l BH_ARR,r1
  mov.l @r1,r1
  tst r1,r1
  bt bh_bomb
  mov.l BH_FEV,r1
  mov.l @r1,r1
  tst r1,r1
  bf bh_req
  mov.l BH_CNT,r1
  mov.l @r1,r0
  mov.l BH_MAX,r1
  cmp/hs r1,r0
  bf bh_bomb
bh_req:
  mov.l BH_REQ,r1
  mov #1,r0
  mov.l r0,@r1
bh_none:
  mov.l BH_NO,r0
  jmp @r0
  nop
bh_bomb:
  mov.l BH_YES,r0
  jmp @r0
  nop
  .align 4
BH_ARR: .long 0x0C04F830
BH_FEV: .long 0x0C04F838
BH_CNT: .long 0x0C04F834
BH_MAX: .long 10000
BH_REQ: .long 0x0C04F868
BH_NO: .long 0x0C07839C
BH_YES: .long 0x0C078308

; ---------- ARRANGE: medal value -> FEVER counter (wraps the medal collect handler 0C090000; r4 = player, r5 = item slot) ----------
medcol:
  mov.l MC_ARR,r0
  mov.l @r0,r0
  tst r0,r0
  bt mc_go
  mov.l MC_FEV,r0
  mov.l @r0,r0
  tst r0,r0
  bf mc_go
  mov #120,r0
  mulu.w r0,r5
  sts macl,r1
  mov.l MC_POOL,r0
  add r0,r1
  mov.l @(8,r1),r1
  mov #18,r0
  cmp/hi r0,r1
  bt mc_go
  shll2 r1
  mova MC_ADD,r0
  add r0,r1
  mov.l @r1,r1
; r1 = tenths of a counter point (0.10% of the medal value); whole points move to the counter
  mov.l MC_FRAC,r3
  mov.l @r3,r0
  add r1,r0
  mov #0,r1
mc_div:
  mov #10,r2
  cmp/hs r2,r0
  bf mc_dd
  sub r2,r0
  bra mc_div
  add #1,r1
mc_dd:
  mov.l r0,@r3
  mov.l MC_CNT,r2
  mov.l @r2,r0
  add r1,r0
  mov.l MC_MAX,r1
  cmp/hi r1,r0
  bf mc_st
  mov r1,r0
mc_st:
  mov.l r0,@r2
mc_go:
  mov.l MC_ORIG,r0
  jmp @r0
  nop
  .align 4
MC_ARR: .long 0x0C04F830
MC_FEV: .long 0x0C04F838
MC_CNT: .long 0x0C04F834
MC_POOL: .long 0x0C52B648
MC_MAX: .long 10000
MC_ORIG: .long 0x0C090000
MC_FRAC: .long 0x0C04F854
MC_ADD: .long 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300

; ---------- ARRANGE per-step effects (called from ahud): Fever start/countdown/end, medal juggling, 10000 medals pulled to the player ----------
; patch RAM: 0C04F834 counter, 0C04F838 fever flag, 0C04F83C last step, 0C04F840 last player state byte, 0C04FA00.. per-item split step (word x 200)
arrfx:
  mov.l r8,@-r15
  mov.l r9,@-r15
  mov.l r10,@-r15
  mov.l r11,@-r15
  mov.l r12,@-r15
  mov.l r13,@-r15
  sts.l pr,@-r15
; bomb pressed during Fever (checked every frame, any bomb stock; the game skips its bomb check, and so
; bombhook, when no bombs are held). Ignored for the first 11 steps of Fever so the starting press can't end it.
  mov.l FX_FEV,r1
  mov.l @r1,r0
  tst r0,r0
  bt fx_ne
  mov.l FX_SWIN,r1
  mov.l @r1,r0
  mov #110,r1
  cmp/hs r1,r0
  bt fx_ne
  mov.l FX_EDGE,r1
  mov.b @r1,r0
  tst #64,r0
  bt fx_ne
  mov.l FX_BREQ,r1
  mov #1,r0
  mov.l r0,@r1
fx_ne:
; only once per game update step (not while paused)
  mov.l FX_STEP,r0
  mov.l @r0,r13
  mov.l FX_LAST,r1
  mov.l @r1,r2
  cmp/eq r13,r2
  bf fx_run
  bra fx_out
  nop
fx_run:
  mov.l r13,@r1
; only while playing: the player state byte is 00 before a game, 80/C0 on the start and character select
; screens (running here then interfered with the select screen, e.g. Rafute's select voice on a fresh boot)
  mov.l FX_P1,r0
  mov.b @r0,r0
  tst r0,r0
  bt fx_idle
  cmp/eq #-128,r0
  bt fx_idle
  cmp/eq #-64,r0
  bf fx_play
fx_idle:
  bra fx_out
  nop
fx_play:
; grace steps after a Fever-ending hit
  mov.l FX_GRACE,r1
  mov.l @r1,r0
  tst r0,r0
  bt fx_g0
  add #-1,r0
  mov.l r0,@r1
fx_g0:
  mov.l FX_P1,r12
; extends every 30,000,000: the game's next-extend score (+0x22C) is kept at the next multiple above the score
  mov.l FX_O228,r0
  mov.l @(r0,r12),r1
  mov.l FX_EXT,r2
  mov r2,r3
fx_ex:
  cmp/hi r1,r3
  bt fx_exd
  bra fx_ex
  add r2,r3
fx_exd:
  add #4,r0
  mov.l r3,@(r0,r12)
; ---- extra bomb on respawn: keep the bombs held at the moment of the hit, give them back +1 (max 4) ----
  mov.b @r12,r0
  extu.b r0,r0
  mov.l FX_RS,r6
  mov.b @r6,r1
  extu.b r1,r1
  mov.b r0,@r6
  mov #-50,r2
  extu.b r2,r2
  cmp/eq r2,r1
  bf fx_rs1
  cmp/eq r2,r0
  bt fx_rsx
; alive -> hit: remember the bombs
  mov.l FX_O214L,r0
  mov.b @(r0,r12),r0
  mov.b r0,@(1,r6)
  mov #1,r0
  bra fx_rsx
  mov.b r0,@(2,r6)
fx_rs1:
  cmp/eq r2,r0
  bf fx_rsx
  mov.b @(2,r6),r0
  tst r0,r0
  bt fx_rsx
; respawned: bombs = remembered + 1, max 4
  mov #0,r0
  mov.b r0,@(2,r6)
  mov.b @(1,r6),r0
  add #1,r0
  mov #4,r1
  cmp/gt r1,r0
  bf fx_rsb
  mov r1,r0
fx_rsb:
  mov.l FX_O214L,r1
  add r12,r1
; never fewer than the game's own respawn bombs
  mov.b @r1,r2
  extu.b r2,r2
  cmp/gt r0,r2
  bt fx_rsx
  mov.b r0,@r1
fx_rsx:
; ---- Fever start: counter full and C pressed this frame ----
  mov.l FX_FEV,r11
  mov.l @r11,r0
  tst r0,r0
  bf fx_infev
  mov.l FX_CNT,r1
  mov.l @r1,r0
  mov.l FX_MAX,r2
  cmp/hs r2,r0
  bf fx_juggle
  mov.l FX_BREQ,r1
  mov.l @r1,r0
  tst r0,r0
  bt fx_juggle
  mov #0,r0
  mov.l r0,@r1
  mov #1,r0
  mov.l r0,@r11
  mov.b @r12,r0
  mov.l FX_PST,r1
  mov.b r0,@r1
; lard meter full
  mov.l FX_LARD,r0
  mov #104,r1
  mov.w r1,@(r0,r12)
; bullets on screen become 10000 medals, then no enemy bullets for 4 seconds (121 steps at Fever's 50%)
  mov.l FX_SWIN,r1
  mov #121,r0
  bra fx_juggle
  mov.l r0,@r1
; ---- during Fever: count down 10 per step; a hit ends it ----
fx_infev:
  mov.b @r12,r0
  mov.l FX_PST,r1
  mov.b @r1,r2
  cmp/eq r0,r2
  bt fx_nohit
  mov.l FX_KIND,r1
  mov #1,r0
  mov.l r0,@r1
  mov.l FX_CNT,r1
  bra fx_fevend
  nop
fx_nohit:
; bomb pressed during Fever (the bomb itself was blocked by bombhook): Fever ends, counter 0, chain restarts
  mov.l FX_BREQ,r1
  mov.l @r1,r0
  tst r0,r0
  bt fx_nobomb
  mov #0,r0
  mov.l r0,@r1
  mov.l FX_KIND,r1
  mov #1,r0
  mov.l r0,@r1
  mov.l FX_CNT,r1
  bra fx_fevend
  nop
fx_nobomb:
  mov.l FX_CNT,r1
  mov.l @r1,r0
  mov #10,r2
  cmp/hi r2,r0
  bt fx_dec
; ran out
  mov.l FX_KIND,r2
  mov #2,r0
  mov.l r0,@r2
fx_fevend:
  mov #0,r0
  mov.l r0,@r1
  mov.l r0,@r11
; Fever over (ran out, bomb or hit): the medal chain starts over at 100; the end window (fxwin) turns the
; bullets into medals and keeps enemies from shooting for 4 seconds (121 steps at 50% after running out,
; 240 steps otherwise); 90 steps of grace
  mov.l FX_CHAIN,r1
  mov.l r0,@r1
  mov.l FX_SWIN,r1
  mov.l r0,@r1
  mov.l FX_EFIRST,r1
  mov #1,r0
  mov.l r0,@r1
  mov.l FX_KIND,r1
  mov.l @r1,r0
  cmp/eq #2,r0
  bt fx_fe2
  mov #120,r0
  bra fx_fe3
  add r0,r0
fx_fe2:
  mov #121,r0
fx_fe3:
  mov.l FX_FADE,r1
  mov.l r0,@r1
  mov.l FX_GRACE,r1
  mov #90,r0
  bra fx_juggle
  mov.l r0,@r1
fx_dec:
  sub r2,r0
  mov.l r0,@r1
; ---- medals: juggling with the lard beam, 10000 medals to the player, Fever makes every medal 10000 ----
fx_juggle:
  bsr fxwin
  nop
; r10 = beam on (lard form and lard shot firing)
  mov #0,r10
  mov.l @r12,r0
  mov.l FX_MECH,r1
  tst r1,r0
  bt fx_nob
  mov.l FX_O214L,r0
  add #-10,r0
  mov.b @(r0,r12),r0
  tst r0,r0
  bt fx_nob
  mov #1,r10
fx_nob:
; count medals on screen -> r9
  mov.l FX_IPOOL,r8
  mov #0,r9
  mov #100,r7
  add #100,r7
fx_cnt:
  mov.l @r8,r0
  tst r0,r0
  bt fx_cn
  mov.l @(4,r8),r0
  cmp/eq #5,r0
  bf fx_cn
  add #1,r9
fx_cn:
  dt r7
  bf/s fx_cnt
  add #120,r8
; walk the medals
  mov.l FX_IPOOL,r8
  mov #0,r11
fx_m:
  mov.l @r8,r0
  tst r0,r0
  bt fx_out_b
  mov.l @(4,r8),r0
  cmp/eq #5,r0
  bf fx_out_b
; Fever, or FEVER counter full: every medal is 10000
  mov.l FX_FEV,r0
  mov.l @r0,r0
  tst r0,r0
  bf fx_all
  mov.l FX_CNT,r0
  mov.l @r0,r0
  mov.l FX_MAX,r1
  cmp/hs r1,r0
  bf fx_nf
fx_all:
  mov.l @(8,r8),r0
  cmp/eq #18,r0
  bt fx_nf
  mov #18,r0
  mov.l r0,@(8,r8)
  bsr medgfx
  nop
fx_nf:
  mov.l @(8,r8),r0
  cmp/eq #18,r0
  bt fx_mn
fx_beam:
  tst r10,r10
  bt fx_out_b
; in the beam: above the player and within 40 pixels sideways
  mov.l @(44,r8),r0
  mov.l @(28,r12),r1
  cmp/gt r1,r0
  bf fx_out_b
  mov.l @(48,r8),r0
  mov.l @(32,r12),r1
  sub r1,r0
  mov.l FX_HALFW,r1
  add r1,r0
  add r1,r1
  cmp/hs r1,r0
  bt fx_out_b
; split only when the medal enters the beam: nothing more while the beam stays on it
  mov.l FX_INB,r1
  add r11,r1
  mov.b @r1,r0
  tst r0,r0
  bf fx_mn
  mov #1,r0
  mov.b r0,@r1
  bra fx_inb
  nop
fx_out_b:
  mov.l FX_INB,r1
  add r11,r1
  mov #0,r0
  bra fx_mn
  mov.b r0,@r1
fx_inb:
; cooldown: 8 steps since this medal last split
  mov r11,r0
  add r0,r0
  mov.l FX_CD,r1
  add r0,r1
  mov.w @r1,r2
  mov r13,r3
  sub r2,r3
  extu.w r3,r3
  mov #8,r2
  cmp/hs r2,r3
  bf fx_mn
  mov.w r13,@r1
; one step up
  mov.l @(8,r8),r0
  add #1,r0
  mov.l r0,@(8,r8)
  bsr medgfx
  nop
; split into two while there are fewer than 64 medals
  mov #64,r0
  cmp/hs r0,r9
  bt fx_solo
  bsr medclone
  nop
  bra fx_mn
  nop
; no room to split: the medal still pops up so every value change shows
fx_solo:
  mov r8,r4
  mov #1,r5
  bsr scatter
  and r13,r5
fx_mn:
  add #1,r11
  mov #100,r0
  add #100,r0
  cmp/hs r0,r11
  bf/s fx_m
  add #120,r8
fx_out:
  lds.l @r15+,pr
  mov.l @r15+,r13
  mov.l @r15+,r12
  mov.l @r15+,r11
  mov.l @r15+,r10
  mov.l @r15+,r9
  rts
  mov.l @r15+,r8

; medgfx: r8 = medal item; refresh its graphics after a level change (game's item init 0C080B40 keeps the position)
medgfx:
  sts.l pr,@-r15
  mov.l FX_IINIT,r0
  jsr @r0
  mov r8,r4
  lds.l @r15+,pr
  rts
  nop

; medclone: r8 = medal item, r11 = its slot, r13 = step. Copies it into a free slot and sends both flying.
medclone:
  sts.l pr,@-r15
  mov.l FX_ALLOC,r0
  jsr @r0
  mov #1,r4
  tst r0,r0
  bt mcl_solo
  mov.l FX_NEWIX,r0
  mov.l @r0,r5
  mov #120,r0
  mulu.w r0,r5
  sts macl,r6
  mov.l FX_IPOOL,r0
  add r0,r6
  mov r8,r1
  mov r6,r2
  mov #30,r3
mcl_cp:
  mov.l @r1+,r0
  mov.l r0,@r2
  dt r3
  bf/s mcl_cp
  add #4,r2
  mov r5,r0
  add r0,r0
  mov.l FX_CD,r1
  add r0,r1
  mov.w r13,@r1
  mov.l FX_INB,r1
  add r5,r1
  mov #1,r0
  mov.b r0,@r1
  add #1,r9
  mov.l r6,@-r15
  mov.l FX_IVEL,r0
  jsr @r0
  mov r5,r4
  mov.l FX_IVEL,r0
  jsr @r0
  mov r11,r4
; pop the two halves up toward the top of the screen (2-3 px/frame), one drifting left and one right (0.5-1 px/frame)
  mov.l @r15+,r4
  bsr scatter
  mov #0,r5
  mov r8,r4
  bsr scatter
  mov #1,r5
mcl_out:
  lds.l @r15+,pr
  rts
  nop
; no free item slot: pop the medal itself
mcl_solo:
  mov r8,r4
  mov #1,r5
  bsr scatter
  and r13,r5
  bra mcl_out
  nop

; mpkman: Manpuku attacks while the FEVER counter is full or Fever is on; the mode is saved when they start
; and put back when both are over
mpkman:
  mov.l FX_FEV,r1
  mov.l @r1,r0
  tst r0,r0
  bf mk_want
  mov.l FX_CNT,r1
  mov.l @r1,r0
  mov.l FX_MAX,r2
  cmp/hs r2,r0
  bt mk_want
  mov.l FX_MPK,r1
  mov.l @r1,r0
  tst r0,r0
  bt mk_out
  mov #0,r0
  mov.l r0,@r1
  mov.l FX_SAVE,r1
  bra mk_set
  mov.l @r1,r0
mk_want:
  mov.l FX_MPK,r1
  mov.l @r1,r0
  tst r0,r0
  bf mk_out
  mov #1,r0
  mov.l r0,@r1
  mov.l FX_MODE1,r1
  mov.l @r1,r0
  mov.l FX_SAVE,r1
  mov.l r0,@r1
  mov #1,r0
mk_set:
  mov.l FX_MODE1,r1
  mov.l r0,@r1
  mov.l FX_MODE2,r1
  mov.b r0,@r1
  mov.l FX_MODE3,r1
  mov.b r0,@r1
mk_out:
  rts
  nop

; fevrules: Fever on -> set mode r0 (1 = Manpuku); Fever off -> put back the mode saved at Fever start
fevrules:
  mov.l FX_FEV,r1
  mov.l @r1,r1
  tst r1,r1
  bf fr_set
  mov.l FX_SAVE,r1
  mov.l @r1,r0
fr_set:
  mov.l FX_MODE1,r1
  mov.l r0,@r1
  mov.l FX_MODE2,r1
  mov.b r0,@r1
  mov.l FX_MODE3,r1
  rts
  mov.b r0,@r1

; scatter: r4 = item, r5 = 0 right / 1 left. Random pop-up (+52) and sideways (+56) speed. Keeps r8-r13.
scatter:
  sts.l pr,@-r15
  mov.l r4,@-r15
  mov.l FX_RAND,r0
  jsr @r0
  nop
  mov.l @r15,r4
  mov.l FX_RMASK,r1
  and r1,r0
  mov.l FX_VMIN,r1
  add r1,r0
  mov.l r0,@(52,r4)
  mov.l FX_RAND,r0
  jsr @r0
  nop
  mov.l @r15+,r4
  mov.l FX_HMASK,r1
  and r1,r0
  mov.l FX_HOFF,r1
  add r1,r0
  tst r5,r5
  bt sc_r
  neg r0,r0
sc_r:
  mov.l r0,@(56,r4)
  lds.l @r15+,pr
  rts
  nop

  .align 4
FX_STEP: .long 0x0C4857C4
FX_RS: .long 0x0C04F844
FX_BREQ: .long 0x0C04F868
FX_GRACE: .long 0x0C04F86C
FX_KIND: .long 0x0C04F88C
FX_SMALL: .long 0x0C04F890
FX_EFIRST: .long 0x0C04F894
FX_MPK: .long 0x0C04F874
FX_FADE: .long 0x0C04F878
FX_FCOL: .long 0x02040000
FX_SWIN: .long 0x0C04F87C
FX_MODE1: .long 0x0C4EAC3C
FX_MODE2: .long 0x0C48227F
FX_MODE3: .long 0x0C516FDC
FX_SAVE: .long 0x0C04F860
FX_CHAIN: .long 0x0C53F4A4
FX_RAND: .long 0x0C06B450
FX_RMASK: .long 0x0000FFFF
FX_VMIN: .long 0x00020000
FX_HOFF: .long 0x00008000
FX_HMASK: .long 0x00007FFF
FX_LARD: .long 0x0000020E
FX_O214L: .long 0x00000214
FX_LAST: .long 0x0C04F83C
FX_PST: .long 0x0C04F840
FX_P1: .long 0x0C510B28
FX_O228: .long 0x00000228
FX_EXT: .long 30000000
FX_FEV: .long 0x0C04F838
FX_CNT: .long 0x0C04F834
FX_MAX: .long 10000
FX_EDGE: .long 0x0C481F3C
FX_P1IN: .long 0x0C481DF8, 0x0C481E38, 0x0C481E78, 0x0C481EFC, 0x0C481F3C, 0x0C481F7C
FX_BPOOL: .long 0x0C4C371C
FX_BCNT: .long 0x0C5108FC
FX_MECH: .long 0x00002000
FX_IPOOL: .long 0x0C52B648
FX_HALFW: .long 0x00280000
FX_CD: .long 0x0C04FA00
FX_INB: .long 0x0C04FB90
FX_IINIT: .long 0x0C080B40
FX_ALLOC: .long 0x0C07F6A0
FX_NEWIX: .long 0x0C4C24EC
FX_IVEL: .long 0x0C081330
FX_IFLAG: .long 0xC0800004
FX_O20A: .word 0x020A
FX_NSLOT: .word 200
  .align 4

; fxwin: the Fever start window (bullets -> pushed-up 10000 medals) and end window (bullets fade out)
fxwin:
  sts.l pr,@-r15
; ---- Fever start window: first step every enemy bullet becomes a 10000 medal bursting out, then for
; 4 seconds any new bullet is removed as soon as it appears (r10 = 1 on the first step); medals float ----
  mov.l W_SWIN,r1
  mov.l @r1,r0
  tst r0,r0
  bt fx_nosw
  add #-1,r0
  mov.l r0,@r1
  mov #0,r10
  cmp/eq #120,r0
  movt r10
  bsr b2med
  nop
  bsr p2pass
  nop
  bsr floatcap
  nop
fx_nosw:
; ---- Fever end window (4 seconds): on the first step every enemy bullet becomes a medal (100 after a hit or
; the bomb, 10000 when the counter ran out), later bullets are removed as soon as they appear. After the
; counter ran out the medals float (and fevspeed runs the window at 50%) ----
  mov.l W_FADE,r1
  mov.l @r1,r0
  tst r0,r0
  bt fw_out
  add #-1,r0
  mov.l r0,@r1
  mov.l W_EFIRST,r1
  mov.l @r1,r10
  mov #0,r0
  mov.l r0,@r1
  mov.l W_KIND,r1
  mov.l @r1,r0
  cmp/eq #2,r0
  movt r2
  mov #1,r0
  sub r2,r0
  mov.l W_SMALL,r1
  mov.l r0,@r1
  bsr b2med
  nop
  bsr p2pass
  nop
  mov.l W_SMALL,r1
  mov #0,r0
  mov.l r0,@r1
  mov.l W_KIND,r1
  mov.l @r1,r0
  cmp/eq #2,r0
  bf fw_out
  bsr floatcap
  nop
fw_out:
  lds.l @r15+,pr
  rts
  nop

; b2med: every live bullet in the main list is removed; with r10 = 1 a medal comes out where it was
b2med:
  sts.l pr,@-r15
  mov.l W_BPOOL,r8
  mov.w W_NSLOT,r9
b2_l:
  mov.l @r8,r0
  tst r0,r0
  bt b2_n
  mov #0,r0
  mov.l r0,@r8
  tst r10,r10
  bt b2_n
  mov.l @(32,r8),r4
  mov.l @(36,r8),r5
  bsr spawn10k
  nop
b2_n:
  dt r9
  bf/s b2_l
  add #92,r8
  lds.l @r15+,pr
  rts
  nop

; floatcap: medals fall at most 0.5 px per frame (slow-motion windows)
floatcap:
  mov.l W_IPOOL,r8
  mov.w W_NIT,r9
  mov.l W_FALL,r2
fw_fl:
  mov.l @r8,r0
  tst r0,r0
  bt fw_fn
  mov.l @(4,r8),r0
  cmp/eq #5,r0
  bf fw_fn
  mov.l @(52,r8),r0
  cmp/gt r0,r2
  bf fw_fn
  mov.l r2,@(52,r8)
fw_fn:
  dt r9
  bf/s fw_fl
  add #120,r8
  rts
  nop
  .align 4
W_SWIN: .long 0x0C04F87C
W_BPOOL: .long 0x0C4C371C
W_FADE: .long 0x0C04F878
W_EFIRST: .long 0x0C04F894
W_KIND: .long 0x0C04F88C
W_SMALL: .long 0x0C04F890
W_NSLOT: .word 1536
W_NIT: .word 200
  .align 4
W_IPOOL: .long 0x0C52B648
W_FALL: .long 0xFFFF8000

; spawn10k: r4/r5 = position (same axes as item +44/+48). New 10000 medal if there is room.
spawn10k:
  sts.l pr,@-r15
  mov.l r4,@-r15
  mov.l r5,@-r15
  mov.l S1_ALLOC,r0
  jsr @r0
  mov #1,r4
  mov.l @r15+,r5
  mov.l @r15+,r4
  tst r0,r0
  bt s10_out
  mov.l S1_NEWIX,r0
  mov.l @r0,r6
  mov.l r6,@-r15
  mov #120,r0
  mulu.w r0,r6
  sts macl,r7
  mov.l S1_IPOOL,r0
  add r0,r7
  mov.l S1_IFLAG,r0
  mov.l r0,@r7
  mov #5,r0
  mov.l r0,@(4,r7)
  mov.l S1_SMALL,r0
  mov.l @r0,r0
  tst r0,r0
  mov #18,r0
  bt s10_lv
  mov #0,r0
s10_lv:
  mov.l r0,@(8,r7)
  mov #0,r0
  mov.l r0,@(12,r7)
  mov.l r4,@(44,r7)
  mov.l r5,@(48,r7)
  mov.l r0,@(52,r7)
  mov.l r0,@(56,r7)
  mov.l r7,@-r15
  mov.l S1_IINIT,r0
  jsr @r0
  mov r7,r4
  mov.l @r15+,r7
  mov.l @r15+,r4
  mov.l r7,@-r15
  mov.l S1_IVEL,r0
  jsr @r0
  nop
; pushed up toward the top of the screen, random side, then it falls like any medal
  mov.l S1_RAND,r0
  jsr @r0
  nop
  mov #1,r5
  and r0,r5
  bsr scatterw
  mov.l @r15+,r4
s10_out:
  lds.l @r15+,pr
  rts
  nop
  .align 4
S1_ALLOC: .long 0x0C07F6A0
S1_IFLAG: .long 0xC0800004
S1_IINIT: .long 0x0C080B40
S1_IPOOL: .long 0x0C52B648
S1_IVEL: .long 0x0C081330
S1_NEWIX: .long 0x0C4C24EC
S1_RAND: .long 0x0C06B450
S1_SMALL: .long 0x0C04F890
  .align 4

; p2pass: the game's second enemy bullet list (0C4EC6F8, 144 bytes each: the green/blue capsule chains).
; Every live record (flag set, handler in 0C0D0000-0C0DFFFF) is removed; with r10 = 1 a 10000 medal
; comes out where it was (+48 vertical, +52 horizontal).
p2pass:
  sts.l pr,@-r15
  mov.l P2_BASE,r8
  mov.w P2_N,r9
p2l:
  mov.l @r8,r0
  tst r0,r0
  bt p2n
  mov.l @(4,r8),r0
  mov.l P2_HLO,r1
  cmp/hs r1,r0
  bf p2n
  mov.l P2_HHI,r1
  cmp/hs r1,r0
  bt p2n
  mov #0,r0
  mov.l r0,@r8
  tst r10,r10
  bt p2n
  mov.l @(48,r8),r4
  mov.l @(52,r8),r5
  bsr spawn10k
  nop
p2n:
  mov.w P2_S,r0
  add r0,r8
  dt r9
  bf p2l
  lds.l @r15+,pr
  rts
  nop
  .align 4
P2_BASE: .long 0x0C4EC6F8
P2_HLO: .long 0x0C0D0000
P2_HHI: .long 0x0C0E0000
P2_N: .word 256
P2_S: .word 144
  .align 4

; scatterw: scatter with a wide sideways push (2-4 px/frame), for the medals that come out of bullets at Fever start
scatterw:
  sts.l pr,@-r15
  mov.l r4,@-r15
  mov.l SW_RAND,r0
  jsr @r0
  nop
  mov.l @r15,r4
  mov.l SW_RMASK,r1
  and r1,r0
  mov.l SW_VMIN,r1
  add r1,r0
  mov.l r0,@(52,r4)
  mov.l SW_RAND,r0
  jsr @r0
  nop
  mov.l @r15+,r4
  mov.l SW_HMASK,r1
  and r1,r0
  mov.l SW_HOFF,r1
  add r1,r0
  tst r5,r5
  bt scw_r
  neg r0,r0
scw_r:
  mov.l r0,@(56,r4)
  lds.l @r15+,pr
  rts
  nop
  .align 4
SW_RAND: .long 0x0C06B450
SW_RMASK: .long 0x0000FFFF
SW_VMIN: .long 0x00020000
SW_HOFF: .long 0x00020000
SW_HMASK: .long 0x0001FFFF

; dblb: double enemy bullets while the FEVER counter is full or Fever is on (until the counter is back at 0).
; Every new bullet in the main list gets a twin about 8 degrees off and 15% slower. +64 of a bullet marks it as
; seen (0 on every slot the game frees). On the first active step the bullets already there are only marked.
dblb:
  mov.l DB_CNT,r0
  mov.l @r0,r0
  mov.l DB_MAX,r1
  cmp/hs r1,r0
  bt db_on
  mov.l DB_FEV,r0
  mov.l @r0,r0
  tst r0,r0
  bf db_on
  mov.l DB_ACT,r1
  mov #0,r0
  rts
  mov.l r0,@r1
db_on:
  sts.l pr,@-r15
  mov.l DB_ACT,r1
  mov.l @r1,r10
  mov #1,r0
  mov.l r0,@r1
  mov.l DB_POOL,r8
  mov #0,r9
db_l:
  mov r8,r7
  add #64,r7
  mov.l @r8,r0
  tst r0,r0
  bf db_live
  bra db_n
  mov.l r0,@r7
db_live:
  mov.l @r7,r0
  tst r0,r0
  bf db_n
  mov #1,r0
  mov.l r0,@r7
  tst r10,r10
  bt db_n
  bsr dbclone
  nop
db_n:
  add #1,r9
  mov.w DB_N,r0
  cmp/hs r0,r9
  bf/s db_l
  add #92,r8
  lds.l @r15+,pr
  rts
  nop

; dbclone: r8 = bullet, r9 = its index. Copies it into the next free slot of the same part of the list
; (0-383, 384-511, 512-1535) and turns the copy: vx' = 27/32 vx - vy/8, vy' = vx/8 + 27/32 vy
; (velocity at +40/+44: about 8 degrees and 0.85x the speed).
dbclone:
  mov r9,r2
  mov.w DB_P1,r0
  cmp/hs r0,r9
  bf dc_e
  mov.w DB_P2,r0
  cmp/hs r0,r9
  bf dc_e
  mov.w DB_N,r0
dc_e:
  mov r8,r3
dc_s:
  add #1,r2
  cmp/hs r0,r2
  bt dc_out
  add #92,r3
  mov.l @r3,r1
  tst r1,r1
  bf dc_s
  mov r8,r4
  mov r3,r5
  mov #23,r6
dc_cp:
  mov.l @r4+,r1
  mov.l r1,@r5
  dt r6
  bf/s dc_cp
  add #4,r5
  mov r3,r7
  add #64,r7
  mov #1,r0
  mov.l r0,@r7
  mov.l @(40,r3),r4
  mov.l @(44,r3),r5
  mov r4,r6
  add r6,r6
  add r4,r6
  mov r6,r1
  shll2 r1
  add r1,r1
  add r1,r6
  mov #-5,r1
  shad r1,r6
  mov r5,r7
  mov #-3,r1
  shad r1,r7
  sub r7,r6
  mov.l r6,@(40,r3)
  mov r5,r6
  add r6,r6
  add r5,r6
  mov r6,r1
  shll2 r1
  add r1,r1
  add r1,r6
  mov #-5,r1
  shad r1,r6
  mov r4,r7
  mov #-3,r1
  shad r1,r7
  add r7,r6
  mov.l r6,@(44,r3)
dc_out:
  rts
  nop
  .align 4
DB_CNT: .long 0x0C04F834
DB_MAX: .long 10000
DB_FEV: .long 0x0C04F838
DB_ACT: .long 0x0C04F884
DB_POOL: .long 0x0C4C371C
DB_N: .word 1536
DB_P1: .word 384
DB_P2: .word 512
  .align 4

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
    body = SRC.replace('CELL_TOP', hex(cell_top)).replace('DIRTY_BOTTOM', hex(dirty_bottom)).replace('#ARROW', f'#{ARROW}').replace('FEVER_SPEED', str(FEVER_SPEED))
    stub = '''romstub:
; boot entry (0x1C4 points here, in ROM): copy the whole patch into RAM and continue there, so none of it runs
; out of the program ROM during play
  mov.l RS_SRC,r1
  mov.l RS_DST,r2
  mov.l RS_LEN,r3
rs_l:
  mov.l @r1+,r0
  mov.l r0,@r2
  dt r3
  bf/s rs_l
  add #4,r2
  mov.l RS_GO,r0
  jmp @r0
  nop
  .align 4
RS_SRC: .long ROMADDR
RS_DST: .long RUNBASE
RS_LEN: .long CODELONGS
RS_GO: .long patcher
'''.replace('ROMADDR', hex(ROM_ADDR)).replace('RUNBASE', hex(RUN_BASE))
    body = stub + body
    src = body + table_src() + warn_src() + '  .align 4\nsites:\n' + ''.join(f'  .long 0x{a:08x}, 0x{o:08x}, {t}\n' for a, o, t in sites) + '  .long 0\n'
    code, labels = Asm(RUN_BASE).assemble(src.replace('CODELONGS', '0'))
    longs = (len(code) + 3) // 4
    code, labels = Asm(RUN_BASE).assemble(src.replace('CODELONGS', str(longs)))
    assert RUN_BASE + longs * 4 <= RUN_LIMIT, 'patch too big for its RAM area'
    assert labels['romstub'] == RUN_BASE

    z = zipfile.ZipFile(ORIG_ZIP)
    u4 = bytearray(z.read('u4'))
    be = bytearray(len(u4)); be[0::2] = u4[1::2]; be[1::2] = u4[0::2]
    assert all(b == 0xFF for b in be[ROM_OFF:ROM_OFF + len(code)]), 'target area not blank'
    assert struct.unpack('>I', be[0x1C4:0x1C8])[0] == MAIN
    be[ROM_OFF:ROM_OFF + len(code)] = code
    be[0x1C4:0x1C8] = struct.pack('>I', ROM_ADDR)   # romstub, run from ROM once at boot
    sw = bytearray(len(be)); sw[0::2] = be[1::2]; sw[1::2] = be[0::2]
    with zipfile.ZipFile(OUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as o:
        for n in z.namelist():
            o.writestr(n, bytes(sw) if n == 'u4' else z.read(n))
    print('code bytes', len(code), 'patcher at', hex(labels['patcher']), 'wrapper', hex(labels['wrapper']),
          'timer', hex(labels['timer']), 'u4 crc', hex(zlib.crc32(bytes(sw))))
    return labels

if __name__ == '__main__':
    main()
