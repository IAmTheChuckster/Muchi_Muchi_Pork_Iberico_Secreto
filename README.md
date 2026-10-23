# # Muchi Muchi Pork! Ibérico Secreto
  
A patch for **Muchi Muchi Pork!** (2007/ 4/17 MASTER VER.)<br>
This repository holds only source, tools and notes. **No ROM data is included**; you patch your own legally owned dump.


## About this project
Why did I make this? Because it's fun and for my own personal research to see the capabilities of Claude.<br>
While Claude was used I put effort in making sure there are balanced gameplay.<br>
I did all the testing and planning.

## Patch Notes

- **Boss and midboss timer.** Shows the seconds left in every boss and midboss fight, under the hi-score. It stops while the game is paused.
- **Main-body health.** Shown under the timer and counts down to 0 when the part is destroyed.
- **Title menu.** After a coin is inserted, or straight away on free play, the title shows **ARCADE / HARAHARA / MANPUKU / V1.01+ / ARRANGE+**.
  - Move the arrow with the joystick and press Start.
  - The arrow starts on ARCADE every time.
  - Harahara and Manpuku are unlocked, so the codes aren't needed.
- **ARRANGE+ mode.** Starts as a copy of V1.01+ (all of the changes below), with "ARRANGE+" shown under the hi-score and a FEVER bar under the 1P lives icon: blue while it fills (and while it drains in Fever), yellow when the counter is full, with FEVER READY flashing in yellow below it.
  - One loop: after the last boss the ending plays and the game is over.
  - An extra life every 20,000,000 points (instead of the normal score extends).
  - Two players can play. Fever, juggling and the FEVER counter follow player 1.
  - **Medal juggling.** Hitting a medal with the lard shot splits it into two medals one value step higher (100 → 200 → … → 10000), which pop up toward the top of the screen and fall back down, one drifting to each side. Every value change pops, even when there is no room to split. A medal splits once as it enters the beam; it splits again only after leaving the beam and coming back (or when you fire a new lard beam). Up to 64 medals on screen.
  - **FEVER counter.** Every medal collected adds 0.3% of its value (100 adds 0.3, 10000 adds 30), up to 10000. It goes back to 0 when a new game starts (a continue keeps it). While the counter is full, every medal is a 10000 medal and enemies fire revenge bullets when destroyed (as in Manpuku).
  - **Fever mode.** With the counter at 10000, pressing bomb starts Fever instead of a bomb (getting hit with the counter at 10000 also starts Fever instead of losing a life): the lard meter is filled, every enemy bullet turns into a 10000 medal that bursts up and out across the screen, floats down slowly for 4 seconds and then falls normally, enemies can't shoot for 4 seconds, enemies keep firing revenge bullets when destroyed, the counter counts down 10 per frame and every medal is a 10000 medal. The first 4 seconds run in slow motion at 50%; after that the game slows down gradually with the number of enemy bullets on screen (99% with none, 85% at 50, 70% at 100, 50% at 150 or more), easing by at most 1% per frame. Fever ends when you are hit (you don't lose a life, and you get a moment of safety), when the counter reaches 0, or when you press bomb again (no bomb goes off, and it works even with no bombs in stock). When Fever ends every enemy bullet turns into a medal that bursts out across the screen: a 100 medal if you were hit or pressed bomb, a 10000 medal if the counter ran out (then the next 4 seconds run in 50% slow motion with the medals floating). Enemies can't shoot for 4 seconds, the counter goes to 0, and the medal chain starts over at 100.
  - **Extra bomb on respawn.** After losing a life you come back with one more bomb than you had when you were hit (up to 4), and never fewer than the game normally gives.
- **V1.01+ mode.** Arcade with these changes: 
  - Pigs fill the lard meter twice as fast, and the lard shot lasts twice as long.
  - Two loops, the second following the first whether or not you died or bombed; after loop 2 the ending plays.
  - Score extends follow your settings in every loop.
  - "V1.01+" is shown under the hi-score during play.
  - Scores go to the Arcade high-score table.
  - The lard shot only fires while B is held. Letting go ends it straight away, with an empty or a full meter, and whatever is left in the lard meter is kept.
  - Power-up and bomb pickups count twice.
  - Small enemies no longer drop the extra medal every 40th kill; that drop is a power-up like the other drops.
- **Warning screen.** Shows a disclaimer that this is an unofficial project, `HAVE FUN!!!` (red) and `2026/10/24 IBERICO SECRETO` (centred).
- **Title screen.** `SALE BY AMI` is replaced with `NOT FOR SALE`.
## Patching the game
You need your own **mmpork.zip** (MAME set, 2007/ 4/17 MASTER VER.) with the original u4 (CRC `d06cfa42`), u2, u23 and u24. Both patchers check the input and give identical files: `iberico_u4` (CRC `3ca26133`), the complete romset `mmporkibc.zip` (u2, u23, u24, iberico_u4) and `Muchi Muchi Pork! Iberico Secreto.mra` for MiSTer.

### Web patcher
1. Open the [web patcher](https://iamthechuckster.github.io/Muchi_Muchi_Pork_Iberico_Secreto/).
2. Load your `mmpork.zip` (or the loose u4 file). Everything runs in your browser; nothing is uploaded.
3. Check that the files are shown as OK.
4. Download what you need: **mmporkibc.zip** (complete romset), **Muchi Muchi Pork! Iberico Secreto.mra**, **iberico_u4.zip** or **iberico_u4**.

### Python script
Needs Python 3 only (no extra packages). Download `mmpork_patch.py` from this repository, then run:
```
python3 mmpork_patch.py mmpork.zip --zip --mra
```
- `--zip` also writes `mmporkibc.zip` (the input must be the zip).
- `--mra` also writes `Muchi Muchi Pork! Iberico Secreto.mra`.
- `-o FILE` sets where `iberico_u4` is written.
- A loose u4 can be given instead of the zip: `python3 mmpork_patch.py u4`.

### Using the patched files
- **MAME:** put `mmporkibc.zip` in your roms folder next to `mmpork.zip`, or replace u4 in a copy of the mmpork set with `iberico_u4` (renamed to u4); MAME will report a checksum mismatch, which is expected.
- **MiSTer (CV1k core):** copy `mmporkibc.zip` to your `games/mame` folder and the `.mra` to `_Arcade`.

## Testing
This patch was tested with MAME 0.289 and [CV1k core for the MiSTer FPGA by Raki](https://www.patreon.com/c/ikamusume/posts)<br>
It may even work on a PCB but do so on your own risk.

## Credits

- [IAmTheChuckster](https://github.com/IAmTheChuckster)  project, testing
- [Claude](https://claude.ai) (Anthropic)  reverse engineering and patcher code
- Tested on the CV1k core for the MiSTer FPGA by [Raki](https://www.patreon.com/c/ikamusume/posts)

## Disclaimer

This repository contains a fan-made patch for research and technical analysis. The repository does not intentionally distribute the original game ROM, executable, or game assets. Users must obtain their own copy of the original game. This project is unofficial and is not affiliated with, endorsed by, or authorized by CAVE. All rights to the original game and its associated intellectual property remain with their respective rights holders. No license to third-party copyrighted material is granted by this repository.
