# # Muchi Muchi Pork! Smoked Bacon
## To Do
1. update warning page
2. Remove lard attack lag for v1.01+
3. Double bombu and powerup items x 2
4. New Arrange mode using v1.01+ as a base and based off of the 360 mode
   a. lard attack splits items doubles them and they get sucked in when they reach 10000<br>
   b. fever meter from 0-10000<br>
   c. grazing fills fever meter<br>
   d. pressing on the bombu, or getting hit sets off the fever meter at this point the mode is manpuku difficulty, getting hit in fever mode cancels out of it and resets the meter.<br>
   
A patch for **Muchi Muchi Pork!** (2007/ 4/17 MASTER VER.)<br>
This repository holds only source, tools and notes. **No ROM data is included**; you patch your own legally owned dump.


## About this project
Why did I make this? Because it's fun and for my own personal research to see the capabilities of Claude.<br>
While Claude was used I put effort in making sure there are balanced gameplay.<br>
I did all the testing and planning.

## Patch notes

- **Boss and midboss timer.** Shows the seconds left in every boss and midboss fight, under the hi-score. It stops while the game is paused.
- **Main-body health.** Shown under the timer and counts down to 0 when the part is destroyed.
- **Title menu.** After a coin is inserted, or straight away on free play, the title shows **ARCADE / HARAHARA / MANPUKU / V1.01+**.
  - Move the arrow with the joystick and press Start.
  - The arrow starts on ARCADE every time.
  - Harahara and Manpuku are unlocked, so the codes aren't needed.
- **V1.01+ mode.** Arcade with these changes: 
  - Pigs fill the lard meter twice as fast, and the lard shot lasts twice as long.
  - Three loops, each one following the last whether or not you died or bombed. Loop 3 plays with Manpuku rules.
  - Score extends follow your settings in every loop.
  - "V1.01+" is shown under the hi-score during play.
  - Scores go to the Arcade high-score table. A game over during loop 3 goes to the Manpuku table.
- **Warning screen.** Shows `MUCHI MUCHI PORK! ROPPAKU` (cyan), `CAVE OWNS!!!` (red) and `2026/10/14 ROPPAKU`.
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
