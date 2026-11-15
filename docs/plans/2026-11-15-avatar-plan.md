# Pixel Avatar (M13) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A pixel avatar stands in front of the object of the last successful action in Version 2's room picture.

**Architecture:** A new small module `version2/avatar.py` (no Streamlit, no LLM) decides where the avatar goes and pastes the sprite onto the room picture with Pillow. `version2/app.py` keeps `st.session_state.avatar` and, after Python's referee decided, asks `avatar.py` for the new place. The LLM never sees the position.

**Tech Stack:** Python, Streamlit 1.67, Pillow, `streamlit.testing.v1.AppTest`, plain-python test runners.

**Spec:** `docs/plans/2026-11-15-avatar-design.md`

## Global Constraints
- No new packages. No changes to the LLM prompts, `validators.py` or `game_config.json`.
- Short, simple code with plain-English comments (Yada is a beginner).
- Mock mode in tests: `USE_MOCK_LLM=true`, `SKY_NO_TYPEWRITER=true`. Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/<file>.py`.
- Sprite file: `assets/Sprite_you.png`, faces right. Missing file = no avatar, no error.
- Commit only after Yada's OK; no Co-Authored-By line.

## Review Focus
1. A refused action (e.g. `use the key on the door`) must not move the avatar. → test in Task 2.
2. An action whose target the referee knows but has no spot must not crash. → test in Task 1 (`goal` returns `None`).
3. The sprite file is missing (today's state): the room still shows, no error. → test in Task 2.
4. Restart / Play again puts the avatar back at `start`, facing right. → test in Task 2.
5. The open-drawer room picture also gets the avatar. → checked in the Task 3 screenshot round.

---

### Task 1: `version2/avatar.py`, the rules and the drawing

**Files:**
- Create: `version2/avatar.py`
- Create: `tests/test_avatar.py` (plain-python runner, same `__main__` block as `tests/test_version2.py`)

**Interfaces:**
- Produces:
  - `AVATAR_SPOTS: dict[str, tuple[float, float]]`: spot id → feet position (x %, y %) of the trimmed room picture. Keys: `start` and the 10 object ids `raincoat, diary, corkboard, drawer, record_player, door, calendar, desk, bed, window`. First guesses: start (50, 92), door (17, 92), raincoat (22, 90), drawer (30, 93), diary (34, 93), desk (38, 93), window (48, 86), record_player (55, 86), corkboard (66, 84), calendar (78, 84), bed (64, 93).
  - `AVATAR_HEIGHT = 0.40`: sprite height as a share of the room picture's height.
  - `goal(action: dict, allowed: bool, objects: dict) -> str | None`: the spot id to walk to, or `None` to stay. Uses `validators.find_id` on `action["target"]` for `examine` and `use`; returns `"door"` for `enter_code`; `None` if not allowed, for other actions, or if the id has no spot.
  - `facing(old_spot: str, new_spot: str, current: str) -> str`: `"left"` / `"right"` by comparing x of the two spots; same x keeps `current`.
  - `place_avatar(room: Image, sprite: Image, spot: str, side: str) -> Image`: a new RGB picture; the sprite is scaled to `AVATAR_HEIGHT` of the room with `Image.NEAREST` (keeps pixels sharp), mirrored with `ImageOps.mirror` when `side == "left"`, pasted with its own alpha so the bottom-middle of the sprite sits on the spot. The `room` passed in is not changed.

- [ ] **Step 1: Write the failing tests** in `tests/test_avatar.py`
  - `test_examine_goes_to_the_object`: `goal({"action": "examine", "target": "bed"}, True, CONFIG["objects"]) == "bed"`; also the alias `"pillow"` → `"bed"`.
  - `test_use_goes_to_the_target_object`: `goal({"action": "use", "item": "brass_key", "target": "drawer"}, True, ...) == "drawer"`.
  - `test_enter_code_goes_to_the_door`: `goal({"action": "enter_code", "target": "keypad", "code": "1111"}, True, ...) == "door"`.
  - `test_refused_or_other_actions_stay`: `goal(examine bed, False, ...) is None`; `goal({"action": "look_around"}, True, ...) is None`; `goal({"action": "take", "target": "brass_key"}, True, ...) is None`; `goal({"action": "examine", "target": "moon"}, True, ...) is None`.
  - `test_every_object_has_a_spot`: `set(CONFIG["objects"]) <= set(AVATAR_SPOTS)` and `"start" in AVATAR_SPOTS`; every value has `0 <= x <= 100 and 0 <= y <= 100`.
  - `test_facing`: `facing("start", "door", "right") == "left"`; `facing("door", "bed", "left") == "right"`; `facing("desk", "desk", "left") == "left"`.
  - `test_place_avatar_paints_at_the_feet_and_keeps_the_room`: room = 200×100 black RGB; sprite = 10×20 RGBA, solid red. Result at pixel just above the feet of spot `bed` is red; a far corner pixel is still black; the original `room` is unchanged (still all black).
  - `test_place_avatar_mirrors_for_left`: sprite 10×20 with only its right half red. With `"right"` the pixel right of the feet is red; with `"left"` the pixel left of the feet is red.
  - CONFIG is loaded from `version2/game_config.json` (UTF-8) at the top of the test file.

- [ ] **Step 2: Run them to see them fail**
  Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/test_avatar.py`
  Expected: `ModuleNotFoundError: No module named 'avatar'`

- [ ] **Step 3: Implement `version2/avatar.py`** with the interfaces above.

- [ ] **Step 4: Run them to see them pass**
  Run: same command. Expected: `All 8 tests passed.`

### Task 2: the avatar in `version2/app.py`

**Files:**
- Modify: `version2/app.py` (constants near `ROOM_OPEN_IMAGE`; `reset_game()`; the room branches of the left column; the player flow after `handle_action`)
- Test: `tests/test_version2.py`

**Interfaces:**
- Consumes: `AVATAR_SPOTS`, `goal`, `facing`, `place_avatar` from Task 1.
- Produces: `st.session_state.avatar = {"at": str, "facing": str}` (start: `{"at": "start", "facing": "right"}`); constant `SPRITE_IMAGE = ASSETS / "Sprite_you.png"`; cached `room_with_avatar(drawer_open: bool, spot: str, side: str)` that returns `room_picture(drawer_open)` alone if `SPRITE_IMAGE` does not exist, else `place_avatar(...)`.

- [ ] **Step 1: Write the failing tests** in `tests/test_version2.py`
  - `test_avatar_starts_in_the_middle`: after `new_game()`, `at.session_state["avatar"] == {"at": "start", "facing": "right"}`.
  - `test_avatar_walks_to_an_examined_object`: `say(at, "examine the raincoat")` → `avatar["at"] == "raincoat"` (raincoat x 22 < start x 50, so `facing == "left"`).
  - `test_refused_action_does_not_move_the_avatar`: after examine the raincoat, `say(at, "use the key on the door")` (no key yet → refused) → still `"raincoat"`.
  - `test_code_at_the_door_moves_the_avatar_there`: use `play_until_record_played(at)`, then `say(at, "enter 1111")` → `avatar["at"] == "door"`.
  - `test_play_again_puts_the_avatar_back`: walk to raincoat, `click(at, "Restart")` (sidebar button) → `avatar == {"at": "start", "facing": "right"}`.
  - `test_room_still_shows_without_a_sprite_file`: after `new_game()`, `len(at.get("image")) >= 1` and no exception (today `Sprite_you.png` does not exist).
  - Check each mock sentence against the mock interpreter in `version2/llm.py` first; if the mock reads a sentence differently, use the sentence the existing tests use for the same action.

- [ ] **Step 2: Run them to see them fail**
  Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/test_version2.py`
  Expected: the new tests FAIL with `KeyError`/`AttributeError` on `avatar`; the 47 old tests still pass.

- [ ] **Step 3: Implement**: set `avatar` in `reset_game()`; in the player flow, right after `outcome = handle_action(...)`, call `goal(action, outcome["allowed"], CONFIG["objects"])` and, if not `None`, update `facing` then `at`; in the two room branches (closed and open drawer) show `room_with_avatar(...)` instead of `room_picture(...)`, with the same alt text plus ", you stand by the <object name>" when the avatar is not at `start`.

- [ ] **Step 4: Run all suites**
  Run: the four test files. Expected: `test_validators` 29, `test_llm` 25, `test_version2` 53, `test_version1` 8, `test_avatar` 8, all passed.

### Task 3: look at it, tune, document

**Files:**
- Modify: `version2/avatar.py` (`AVATAR_SPOTS`, `AVATAR_HEIGHT` values only), `README.md` (test counts, one line about the avatar), `docs/plans/2026-11-15-avatar-design.md` (status line)

- [ ] **Step 1:** With a **throwaway** placeholder sprite in the scratchpad (never in `assets/`), take headless Chrome screenshots of the room with the avatar at `start`, `door`, `desk`, `window`, `bed`, `calendar`, and once with the open drawer. Adjust the spots and the height until the feet stand on the floor.
- [ ] **Step 2:** Show Yada the screenshots; one correction round. When Yada's real `assets/Sprite_you.png` exists, repeat the screenshots with it.
- [ ] **Step 3:** Run all test files again. Expected: all passed (same counts as Task 2 Step 4).
- [ ] **Step 4:** Show `git status`, the files and the message; commit only after Yada's OK:
  `M13: pixel avatar in the room (walks to the object of the last successful action)`
