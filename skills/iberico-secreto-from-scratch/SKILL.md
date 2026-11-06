---
name: "iberico-secreto-from-scratch"
description: "Recreate the whole Muchi Muchi Pork! Iberico Secreto project from nothing: SH-3 patch (modes, Fever, boss health bar), Python and web patchers, MiSTer MRA, README, tests and GitHub release, starting from the user's own mmpork.zip."
---

# Muchi Muchi Pork! Iberico Secreto: build the project from scratch

Use when the user wants the project rebuilt, ported or started again in a new repo. It records what the finished
project does, how it is wired into the game and how it was tested. The reference implementation is
https://github.com/IAmTheChuckster/Muchi_Muchi_Pork_Iberico_Secreto (`src/build.py` has every routine); read it
when a detail here is not enough. For small edits to the existing project use `iberico-secreto-build`.
Learn the game with `cv1000-learn-game` and follow `cv1000-patch-dev` for the general method.

## 0. House rules (always)
- **No ROM data** in any repo, web page, artifact or shared file. Only new code, new text and changed-byte tables.
  The user supplies `mmpork.zip` (MAME set, Japan 2007/4/17 MASTER VER.); work on a copy.
- Confirm every change with the user before building; they often say "don't do anything yet". When interrupted,
  stop and wait. Show a MAME mock-up for anything visual first.
- README wording belongs to the user: only update the Patch notes and the CRC in the patching section.
  The user edits README on GitHub, so `git pull --rebase` before every push.
- Commits: author `Claude <noreply@anthropic.com>`; trailers `Co-Authored-By: I Am The Chuckster
  <341332324+IAmTheChuckster@users.noreply.github.com>` (never a personal email), the Claude model line and the
  `Claude-Session:` line the session gives. Check the history for personal emails before publishing.
- The user's own MRA file is the template; its name is exactly `Muchi Muchi Pork! Iberico Secreto.mra`.
- Keep a to-do list out of the README unless asked; drop items the user says to forget.

## 1. Inputs and outputs
| File | CRC32 | Notes |
|---|---|---|
| u4 (original program NOR) | d06cfa42 | 2 MiB, 16-bit word-swapped |
| u2 / u23 / u24 | 1ee961b8 / 4a4b36df / ce83d07b | copied unchanged |

Outputs: `iberico_u4` (patched), `mmporkibc.zip` (u2, u23, u24, iberico_u4), `Muchi Muchi Pork! Iberico Secreto.mra`
(setname `mmporkibc`). Build 64 gives u4 CRC **0fd4b1b1**; the number changes with every build, so record it in
`src/README.md` ("Build N gives `u4` CRC `xxxxxxxx`"), the README patching section, the MRA and both patchers.

## 2. Repository layout
`src/build.py` (assembly source string + site table + packer), `src/shasm.py` (a small SH-3 assembler: add
encodings when needed, e.g. shad 0x400C, cmp/pl 0x4015, shll8 0x4018), `src/update_patchers.py ORIG.zip NEW.zip BUILD`
(embeds the changed bytes and fixes CRCs), `mmpork_patch.py` (stdlib Python patcher, `--zip --mra -o FILE`),
`index.html` (browser patcher, same output), the MRA, `README.md`, `src/README.md`, `src/mame_tests/*.lua`,
`skills/`, `.gitignore`, `.nojekyll`, GPL v3 licence. GitHub Pages serves `index.html`.
Build: `python3 src/build.py mmpork.zip OUT.zip [RAM_DUMP]` (dump only asserts the expected original longs).
Python and web patchers must give byte-identical files; test the page headless with Playwright.

## 3. Architecture of the patch
- The program is copied to RAM at boot. ROM word 0x1C4 normally points at game main (0x0C0603D0); it now points at
  `romstub` in ROM (0x801F0000, blank area). `romstub` copies the whole patch to RAM 0x0C04C000 (limit 0x0C04F800) and
  jumps to `patcher`, which zeroes patch RAM 0x0C04F800-0x0C04FFFF (the test button reset keeps RAM), applies the
  site table (address, expected original long, new long) and jumps to main.
- **All patch code runs from RAM.** Running it from the program ROM crashed only on MiSTer (missing voices, music
  cutting out, a crash in a routine); MAME never showed it.
- Hooks: replace a literal used by `jsr`, or overwrite 4 bytes with `mov.l @(disp,PC),Rn / jmp @Rn / nop` plus a
  literal in dead padding (nops after `rts`/`bra` nothing targets). Replay overwritten instructions, keep PR and
  callee-saved registers. Reach limits: `mov.l @(disp,PC)` 1020 bytes forward, `mov.w` 510, `bt/bf` +-256; move a
  helper after another literal pool when it runs out.

### Site table (RAM address, original long -> new)
Wrapper 0C06FC4C (text redraw call) -> `wrapper`; unlock 0C06D29C; menu draw 0C06D044; menu jump 0C06CF04/08/0C;
pig pickup 0C090828/2C/48 (`lardadd`); loop decision 0C076AC8/CC/B40 (`loopchk`) and 0C0965C0/C4/F4 (`loopchk2`);
in-game mode name 0C070184 -> `modelabel` (now draws nothing); warning screen 0C067AA8 (table), 0C067AB4
(`datestr`), 0C0679D4 (start column), 0C067AC4 (`verstr`, empty), 0C067A20; title text 0C06D038 (`nfsstr`);
lard button check 0C0785A8/AC/778 (`hookB`); item collect table 0C0E2B24/44/64/84 (power-up and bomb pickups),
0C0E2BC4 (`medcol`); bomb check 0C078300/04/3AC (`bombhook`); game-loop skip test 0C06F994/98/FC78 (`fevspeed`);
player-hit calls 0C074598 and 0C0748FC (`hithook`, original target 0C07DDF0); revenge-bullet mode literal
0C0D7528 -> 0C04F888 (our own flag). Every original long is asserted before it is changed.

## 4. Game facts used
- Player 1 block 0x0C510B28 (P2 +0x200): +0 state byte (CE alive, A0 dead, 80/C0 select screens, 00 before a game),
  +0x1C/+0x20 position 16.16 (66,464 at the bottom start), +0x203 lives, +0x20A lard firing, +0x20E lard meter
  (104 max), +0x214 bombs, +0x228 score, +0x22C next extend.
- Items 0x0C52B648, 200 x 120 bytes: +4 type (5 = medal), +8 value step 0-18 (100..1000, 2000..10000), +44/+48
  position, +52/+56 speed, +116 motion state. Alloc 0C07F6A0, init 0C080B40, random velocity 0C081330, RNG 0C06B450.
- Enemy bullets list 1: 0x0C4C371C, 92-byte records, 1536 enemy slots; position +32/+36, velocity +40/+44. List 2
  (capsule chains): 0x0C4EC6F8, 144-byte records, 256 slots, position +48/+52.
- Counters: vblank 0x0C002310, game step 0x0C4857C4, updates 0x0C48A168. Text layer 0x0C483A50 + (column*30+row)*4,
  column 39 = top line; cell = tint | bank<<8 | char (bank 0x80 font, 0x85 icons); redraw flag 0x0C4EAC98+column*8.
  Font codes 16-23 are blocks 1-8 px wide (bars); `_`, `|` and the overline exist but no 1-pixel box lines.
- Colours (tint): yellow 80602000, pure yellow 80800000, white 80808000, purple 60308000, cyan 20708000, red
  70201000 / 80201000, blue 20408000, green 20802000. Channels run 0-0x80.
- The game runs at 60 fps; in MAME it keeps 60 updates a second even with hundreds of bullets. Time anything
  against the real vblank count, never against game steps (the game lags on hardware).

## 5. Features to rebuild (see the repo README Patch notes for the exact text)
- **Everywhere:** warning screen with the unofficial disclaimer, `HAVE FUN!!!` in red and `2026/11/7 IBERICO SECRETO`
  centred (update the date to the release date); title `NOT FOR SALE`; title menu ARCADE / HARAHARA / MANPUKU /
  V1.01+ / ARRANGE+ in pure yellow with Harahara and Manpuku unlocked; the in-game mode label removed.
- **Boss timer and boss health bar (all modes):** timer on the line under the hi-score (column 37, rows 12-16),
  stops while paused. Health bar = 8 text cells, column 36 rows 11-18, 64 px, fills from the left. A per-enemy table
  (stage, handler, health field, mask, rules) lists the main body; every slot of the boss keeps its starting and last
  health (word tables at 0x0C04FD00 and +384). The bar shows the part that last took damage (held 30 steps),
  else the main body. Main body: green when full, blue, yellow at half or less, red at 15 or less. Other parts:
  always cyan. Cleared when the fight ends. Stage 4 midboss A needs a mask to skip an undamageable object.
- **V1.01+:** lard fills twice as fast and lasts twice as long, only fires while B is held (release keeps the meter),
  power-up and bomb pickups count double, no 40th-kill medal, two loops then the ending, scores go to the Arcade table.
- **ARRANGE+** = V1.01+ plus: one loop; two players; score extends follow the DIP settings; extra bomb on respawn
  (one more than at the hit, max 4, never fewer than the game gives); **medal juggling** (a medal splits one value
  step as it enters the lard beam, halves pop up, max 64 medals); **FEVER counter** (0.3% of each medal's value,
  max 10000, bar under the 1P lives, `FEVER READY` flashing yellow below, reset on a new game, kept on continue;
  full counter: all medals 10000 and revenge bullets); **Fever** (bomb with a full counter, or a hit): lard meter
  full, enemy bullets of both lists become 10000 medals that burst up and float, 4 s of 50% slow motion with no enemy
  fire, then speed eases with the bullet count (99% none .. 50% at 150+, at most 1% per frame), counter -10 per step;
  ends by hit or bomb (bullets -> 100 medals, no life lost, safety window) or by running out (bullets -> 10000
  medals, 4 s of 50% slow motion). Cancel all 1536 + 256 bullet slots, not just a subset; keep volleys from
  returning with a no-shoot window.
- **Patch RAM map** (0x0C04F8xx): 24 menu choice, 28 V1.01 flag, 2C loop index, 30 ARRANGE flag, 34 FEVER counter,
  38 fever flag, 3C last step, 40 player state, 44-46 respawn, 50 speed accumulator, 54 counter fraction, 60 saved
  mode, 68 bomb request, 6C grace, 70 last vblank, 78 end window, 7C start window, 80 eased speed, 88 revenge flag,
  8C end kind, 90 small-medal flag, 94 end-first, 98 shown part, 9C main-body part, A0 switch hold; split cooldown
  words at 0C04FA00, in-beam bytes at 0C04FB90, per-slot health at 0C04FD00.

## 6. Pitfalls learned
- The Manpuku revenge routine tests a mode word; point its literal at our own flag so revenge bullets only run when
  asked (during play only, reset at the menu and at boot).
- A bomb with 0 stock skips the game's check: read the bomb-press byte directly.
- Zero the patch RAM at every boot; a reset from the test button keeps RAM.
- Fever speed: use the real vblank counter; the game itself lags.
- Literal pools run out of range: move helpers with their own literals.
- Text-layer addresses are easy to typo; check with a MAME screenshot.

## 7. MAME testing (0.289 only)
Use `-video none -sound none -nothrottle -nodrc -seconds_to_run 200`, Lua `autoplay` (coin, start, menu Down x4 =
ARRANGE+, fire; Right presses before the select confirm pick Momo/Ikuo/Rafute). Screenshot with
`manager.machine.screens[":screen"]:pixels()` (320x240 BGRA, rotate 90). Watchpoints don't fire on this RAM;
breakpoints do (`-debug -debugger none`). Checklist before pushing: all modes start; title menu; Fever start and
end by bomb, hit and run-out; juggling; extends follow the DIP; respawn bomb; boss bar colours on a boss and a
midboss; reset clears patch RAM; long Fever soak with no freeze; Python == web output; MRA CRC updated.
Then ask the user to test on MiSTer and expect reports about Rafute's voices and crashes.

## 8. Release
1. Build, note the CRC, run the checklist, take screenshots.
2. `python3 src/update_patchers.py ORIG.zip NEW.zip BUILD`; run Python and Playwright patchers; compare the MRA.
3. Update README Patch notes (and CRC), `src/README.md`, skills; `git pull --rebase`; commit; push to main.
4. Tell the user what changed and what was tested; remind them to re-patch (the CRC changed) and that Pages
   updates after the push.
