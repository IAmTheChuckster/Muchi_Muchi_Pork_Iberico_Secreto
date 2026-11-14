# Source

Everything needed to rebuild the patch from your own `mmpork.zip`. No ROM or RAM data is included.

| File | What it is |
|---|---|
| `build.py` | The whole patch: SH-3 assembly for the new routines, the list of RAM patch sites, the warning and title text. Builds a patched `mmpork.zip`; `--god` adds the FEVER counter digits from a 360 GOD package. |
| `god_glyphs.py` | Reads the 360 GOD package (`.zip` or `.7z`), decodes graphic 1610 of `MPD100.bin` (the same compression as the arcade NAND graphics) shrinks the 10 digits and builds a gold glow for each. Standard library only; `update_patchers.py` copies it into `../patch.py`, and `../index.html` has the same code in JavaScript. |
| `shasm.py` | Small SH-3 assembler used by `build.py` (only the instructions the patch needs). |
| `update_patchers.py` | Copies a new build's code bytes (never the digits) and CRC into `../index.html`, `../patch.py` and the iberico_u4 CRC in `../mister/Muchi Muchi Pork! Iberico Secreto.mra`. Without a build number it uses the one in `../index.html` plus 1. |
| `mame_tests/` | MAME Lua scripts used for testing (autoplay, lard/pickup trace, title menu, warning screen, three loops, pause). |

## Rebuild

```
python3 build.py mmpork.zip mmpork_patched.zip --god 435A07DE.zip
python3 update_patchers.py mmpork.zip mmpork_patched.zip
```

`mmpork.zip` must hold the original `u4` (CRC `d06cfa42`). Build 77 gives `u4` CRC `7673bc4b`; the patchers save it as `iberico_u4`.

The FEVER counter digits sit at u4 0x1F3800, right after the 14 KB code area (16,320 bytes: the 10 digits and a glow image per digit, all in 24 px wide rows, as the blitter upload width must be a multiple of 8). The game draws them by appending, just before each frame's blitter list is closed (literal 0C062748), for each digit an upload of its glow (VRAM x 392) and an additive draw of it, then an upload of the digit to a scratch slot in the gap between the two framebuffers (VRAM x 368, y 136 + 24 per slot) and a tinted draw of it.

## Run a MAME test

From a folder with a `roms/` directory holding the patched set (run from the repo root so `src/mame_tests/common.lua` resolves):

```
mame mmpork -rompath roms -video none -sound none -nothrottle -autoboot_script src/mame_tests/arr.lua
```

`v16.lua` reads the environment variable `V101=1` to pick V1.01+ instead of Arcade.
