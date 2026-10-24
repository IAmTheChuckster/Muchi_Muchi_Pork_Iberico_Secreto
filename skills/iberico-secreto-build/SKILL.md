---
name: "iberico-secreto-build"
description: "Rebuild or extend the Muchi Muchi Pork! Iberico Secreto patch (SH-3 routines, Python and browser patchers, MiSTer MRA) from an original mmpork.zip and test it in MAME."
---

# Muchi Muchi Pork! Iberico Secreto: build and extend

Recreates and extends everything in https://github.com/IAmTheChuckster/Muchi_Muchi_Pork_Iberico_Secreto
from the user's own `mmpork.zip`. **Never put ROM data in the repo, the web page or anything shared**;
only new code, new text and changed-byte tables. Commits: author `Claude <noreply@anthropic.com>`,
co-author `I Am The Chuckster <lancebukkake@protonmail.com>`. The README wording belongs to the user;
only update its Patch notes. Confirm every change with the user before building; when interrupted,
stop and wait.

## 0. Inputs and outputs
| File | CRC32 | Notes |
|---|---|---|
| u4 (original) | d06cfa42 | 2 MiB program NOR, 16-bit word-swapped |
| u2 / u23 / u24 | 1ee961b8 / 4a4b36df / ce83d07b | copied unchanged |

Output: `iberico_u4` (build 62: **f76a2ef8**) inside `mmporkibc.zip` (u2, u23, u24, iberico_u4), and
`Muchi Muchi Pork! Iberico Secreto.mra` (setname mmporkibc; rom 1 u2 @0x34400000; rom 2 @0x3C800000
u23 + 0x400000 zeros + u24 + 0x400000 zeros; nvram index 3 size 135680; rom 0 iberico_u4 listed twice).

## 1. Repo layout and build
- `src/build.py ORIGINAL_mmpork.zip OUT.zip RAM_DUMP` assembles all routines (`SRC` string, SH-3
  syntax) with `src/shasm.py`, applies them, prints the u4 CRC. RAM_DUMP is a dump of the unpacked
  program (8 MB from 0x0C000000 after boot) used only to assert the expected original longs.
- `src/update_patchers.py ORIG.zip NEW.zip BUILD` embeds the changed bytes (0x1C4 and the 0x1F0000
  block) into `mmpork_patch.py` and `index.html` and fixes the iberico_u4 CRC in the MRA files.
- `mmpork_patch.py IN.zip --zip --mra` (stdlib only) and `index.html` (browser) must give identical
  files. Test the web page headless with Playwright (upload mmpork.zip, click each download button,
  check names and CRCs).
- `src/README.md` holds "Build N gives `u4` CRC `xxxxxxxx`"; bump it with every build.
- shasm only knows the instructions used so far; add encodings (e.g. shad 0x400C, cmp/pl 0x4015,
  shll8 0x4018) as needed. `mov.l @(disp,PC)` reaches 1020 bytes forward only, `mov.w` 510,
  bt/bf ±256 bytes: when a routine's literal pool goes out of range, move a helper (with its own
  literals) after another pool.

## 2. How the patch runs
- ROM 0x1C4 normally points at the game's main (0x0C0603D0). It now points at `romstub` in ROM
  (0x801F0000), which copies the whole patch to RAM 0x0C04C000 (limit 0x0C04F800) and jumps to
  `patcher`. **All patch code must run from RAM**: running it straight from the program ROM caused
  crashes, missing voices (Rafute) and music drop-outs on the MiSTer core (MAME never showed it).
- `patcher` zeroes the patch RAM 0x0C04F800-0x0C04FFFF (a test-button reset keeps RAM), applies the
  `sites` table (address, expected original long, new long) to the unpacked program, then jumps to
  main. The original game never touches 0x0C04C000-0x0C050FFF.
- Hooks replace literals/calls in the unpacked program; see `patch_sites()` in build.py for the full
  list with comments (title menu, warning text, lard, item collect table, bomb check, game-loop skip
  test, player-hit tail calls, revenge-bullet mode test, loop checks).

## 3. Modes and features
| Mode | Changes |
|---|---|
| All | Warning screen disclaimer, `HAVE FUN!!!`, bottom line `2026/10/24 IBERICO SECRETO` centred; title `NOT FOR SALE`; Harahara/Manpuku unlocked; menu ARCADE/HARAHARA/MANPUKU/V1.01+/ARRANGE+ in yellow; boss timer on the line under the hi-score (column 37, no mode name in any mode) and a 64 px health bar under it for the boss part being hit (column 36 rows 11-18; green full, blue, yellow at half, red at 15 or less; per-slot starting/last health at 0x0C04FD00/+384, shown part 0x0C04F898, main body 0x0C04F89C, 30-step switch hold 0x0C04F8A0); boss timers stop while paused. |
| V1.01+ | Lard fills twice as fast and lasts twice as long; releasing B ends the lard shot and keeps the meter; power-up and bomb pickups count double; no 40th-kill medal; two loops then the ending. |
| ARRANGE+ | V1.01+ plus: one loop; 2P allowed; extends follow the DIP settings; extra bomb on respawn; medal juggling (a medal splits one value step as it enters the lard beam, halves pop up, max 64 medals); FEVER counter (0.3% of each medal's value, max 10000) shown as a 64 px bar under the 1P lives (blue, yellow when full, `FEVER READY` flashing below); full counter: all medals 10000, revenge bullets, a hit starts Fever; Fever (bomb with a full counter): bullets of both lists become 10000 medals that burst out and float during 4 s of 50% slow motion with no enemy fire, counter -10 per step, speed eases with the bullet count (99% .. 50%), revenge bullets; ends by hit or bomb (bullets -> 100 medals, no life lost) or by running out (bullets -> 10000 medals, 4 s of 50% slow motion); counter resets on a new game, kept on continue. |

## 4. Key addresses (unpacked program / RAM)
- Player 1 block 0x0C510B28 (P2 +0x200): +0 state (top byte 0xCE alive, 0xA0 dead, 0x80/0xC0 start
  and select screens, 00 before a game; bit 0x2000 lard form), +28/+32 position (16.16, up larger),
  +0x203 lives, +0x20A lard firing, +0x20E lard meter (104 max), +0x214 bombs, +0x228 score,
  +0x22C next extend.
- Items 0x0C52B648, 200 x 120 bytes: +4 type (5 medal), +8 value step 0-18 (100..1000, 2000..10000),
  +44/+48 position, +52/+56 speed, +116 motion state. Alloc 0x0C07F6A0, init 0x0C080B40 (clears
  +116), random velocity 0x0C081330, RNG 0x0C06B450.
- Enemy bullets: list 1 at 0x0C4C371C, 92-byte records, 1536 enemy slots (parts of 384/128/1024),
  then 192 non-bullet objects; position +32/+36, velocity +40/+44. List 2 (green/blue capsule chains)
  at 0x0C4EC6F8, 144-byte records, 256 slots, handler (+4) in 0x0C0D0000-0x0C0DFFFF.
- Player-hit routine 0x0C07DDF0 (tail-called from two places); revenge-bullet routine 0x0C0D74E0;
  game-loop updates 0x0C48A168 (+1 per frame), step counter 0x0C4857C4, vblank count 0x0C002310.
- Text layer 0x0C483A50 + (column*30 + row)*4, column 39 = top line, 0 = bottom; cell =
  tint 0xRRGGBB00 | bank<<8 | char (bank 0x80 font, 0x85 icons); redraw flag 0x0C4EAC98 + column*8.
  Font codes 16-23 are blocks 1-8 px wide (used for the bar).
- Patch RAM map: see the `; patch RAM` comments in build.py (0x0C04F824 menu .. 0x0C04F894, medal
  split timers 0x0C04FA00, in-beam bytes 0x0C04FB90).

## 5. Testing in MAME
- Use the `cv1000-learn-game` skill for the MAME set-up. Lua scripts in `src/mame_tests/` drive the
  game (`dofile("work/common.lua")` autoplay: coin, start, menu Down x4 = ARRANGE+, fire; common.lua
  is in the same folder).
- Screen capture without video: `manager.machine.screens[":screen"]:pixels()` (320x240 BGRA, rotate 90).
- Watchpoints don't fire on this RAM; breakpoints do (`-debug -debugger none`, `bpset addr,1,{printf ...; g}`).
  Instruction traces need `-nodrc` (DRC trace segfaults).
- A hit with a full counter starts Fever by itself: fill the counter just before the test press.
- Before pushing: all modes start, Fever start/end (bomb, hit, run-out), juggling, extends, reset
  clears the patch RAM, long Fever soak without a freeze, RAM copy of the patch unchanged afterwards,
  Python == web output, MRA CRC updated. Then ask the user to test on MiSTer.
