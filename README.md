# # Muchi Muchi Pork! Smoked Bacon
  
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
- **ARRANGE+ mode.** Starts as a copy of V1.01+ (all of the changes below), with "ARRANGE+" shown under the hi-score.
  - One player only: 2P can't join, the 2P prompts are hidden, "2P" reads FEVER and the 2P score shows the FEVER counter.
  - **Medal juggling.** Hitting a medal with the lard shot splits it into two medals one value step higher (100 → 200 → … → 10000), at most once every 15 frames per medal and up to 64 medals on screen. 10000 medals are collected automatically.
  - **FEVER counter.** Every medal collected adds a tenth of its value (100 adds 10 … 10000 adds 1000), up to 10000.
  - **Fever mode.** With the counter at 10000, pressing bomb starts Fever instead of a bomb: the lard meter is filled, every enemy bullet turns into a 10000 medal, the counter counts down 10 per frame, and every medal is a 10000 medal. Fever ends when the counter reaches 0 or when you are hit (the counter stops where it was).
  - **Fever speed.** The game runs at 75% speed during Fever.
  - **Extra bomb on respawn.** After losing a life you come back with one more bomb than you had when you were hit (up to 4), and never fewer than the game normally gives.
- **V1.01+ mode.** Arcade with these changes: 
  - Pigs fill the lard meter twice as fast, and the lard shot lasts twice as long.
  - Three loops, each one following the last whether or not you died or bombed. Loop 3 plays with Manpuku rules.
  - Score extends follow your settings in every loop.
  - "V1.01+" is shown under the hi-score during play.
  - Scores go to the Arcade high-score table. A game over during loop 3 goes to the Manpuku table.
  - The lard shot only fires while B is held. Letting go ends it straight away, with an empty or a full meter, and whatever is left in the lard meter is kept.
  - Power-up and bomb pickups count twice.
  - Small enemies no longer drop the extra medal every 40th kill; that drop is a power-up like the other drops.
- **Warning screen.** Shows a disclaimer that this is an unofficial project, `HAVE FUN!!!` (red) and `2026/10/23 SMOKED BACON`.
- **Title screen.** `SALE BY AMI` is replaced with `NOT FOR SALE`.
## Patching the game

## Testing
This patch was tested with MAME 0.289 and [CV1k core for the MiSTer FPGA by Raki](https://www.patreon.com/c/ikamusume/posts)<br>
It may even work on a PCB but do so on your own risk.

## Credits

- [IAmTheChuckster](https://github.com/IAmTheChuckster)  project, testing
- [Claude](https://claude.ai) (Anthropic)  reverse engineering and patcher code
- Tested on the CV1k core for the MiSTer FPGA by [Raki](https://www.patreon.com/c/ikamusume/posts)

## Disclaimer

This repository contains a fan-made patch for research and technical analysis. The repository does not intentionally distribute the original game ROM, executable, or game assets. Users must obtain their own copy of the original game. This project is unofficial and is not affiliated with, endorsed by, or authorized by CAVE. All rights to the original game and its associated intellectual property remain with their respective rights holders. No license to third-party copyrighted material is granted by this repository.
