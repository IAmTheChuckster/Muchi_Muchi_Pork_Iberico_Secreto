# Source

Everything needed to rebuild the patch from your own `mmpork.zip`. No ROM or RAM data is included.

| File | What it is |
|---|---|
| `build.py` | The whole patch: SH-3 assembly for the new routines, the list of RAM patch sites, the warning and title text. Builds a patched `mmpork.zip`. |
| `shasm.py` | Small SH-3 assembler used by `build.py` (only the instructions the patch needs). |
| `update_patchers.py` | Copies a new build's bytes and CRC into `../index.html`, `../mmpork_patch.py` and the bacon_u4 CRC in `../Muchi Muchi Pork! Smoked Bacon.mra`. |
| `mame_tests/` | MAME Lua scripts used for testing (autoplay, lard/pickup trace, title menu, warning screen, three loops, pause). |

## Rebuild

```
python3 build.py mmpork.zip mmpork_patched.zip
python3 update_patchers.py mmpork.zip mmpork_patched.zip 29
```

`mmpork.zip` must hold the original `u4` (CRC `d06cfa42`). Build 43 gives `u4` CRC `6761cfa3`; the patchers save it as `bacon_u4`.

## Run a MAME test

From a folder with a `roms/` directory holding the patched set (run from the repo root so `src/mame_tests/common.lua` resolves):

```
mame mmpork -rompath roms -video none -sound none -nothrottle -autoboot_script src/mame_tests/arr.lua
```

`v16.lua` reads the environment variable `V101=1` to pick V1.01+ instead of Arcade.
