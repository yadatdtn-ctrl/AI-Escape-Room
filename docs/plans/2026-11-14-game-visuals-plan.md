# M12 Game-like Look Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Version 2 page look and feel more like a game (memory cards, HUD, typewriter text, item cards, ending stats) without changing any rule or LLM job.

**Architecture:** Display-only changes in `version2/app.py`, plus one picture helper in `version2/pictures.py`. Game rules stay in `validators.py`/`game_state.py`; the state already records played cutscenes (`game["cutscenes"]`). Everything uses native Streamlit elements, so `AppTest` can check it.

**Tech Stack:** Python, Streamlit 1.67 (`st.progress`, `st.image`, `st.dialog`, `st.write_stream`, Material icons), Pillow.

**Spec:** `docs/plans/2026-11-14-game-visuals-design.md` (approved by Yada on 2026-11-14).

## Global Constraints

- No change to rules, limits, the interpreter, the narrator or the config texts. Version 1 is not changed.
- No JavaScript, no custom component, no `st.html` cards. Follow `developing-with-streamlit` (Material icons, `width="stretch"`, `alt=` on images, sentence case).
- Nothing may depend on color alone: every bar and icon also has text.
- Files in `assets/` are never changed by code.
- Typewriter: about 0.03 s per word, at most 1.5 s per message; its time is given back to the clock; off when the environment variable `SKY_NO_TYPEWRITER` is `"true"` (set in the tests).
- Item pictures: `assets/Item_brass_key.png`, `assets/Item_vinyl_record.png` (made by Yada later); fallback icons `:material/key:` and `:material/album:`.
- Tests are written first and run with `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/<file>.py`. All existing 91 tests must still pass after every task.
- Yada's git rules: no commit until Yada says OK; no Co-Authored-By line; `.env` never added.

## Review Focus

1. The player sends a new message while the typewriter is still typing: the earlier story must not be lost (it is marked as shown before typing starts).
2. The typewriter runs while a cutscene is playing: the clock is already paused, so no time may be given back twice.
3. Play again / Restart: memory cards are locked again and the old ending stats are gone.
4. The bad ending by time: "time used" shows the full 5:00, never more and never a negative number.
5. A memory card is opened during play: no move is used and the clock keeps running.

---

### Task 1: Memory cards

**Files:**
- Modify: `version2/pictures.py` (new `locked()`), `version2/app.py` (cards under the Items line, new dialog)
- Test: `tests/test_version2.py`

**Interfaces:**
- Produces: `pictures.locked(path, blur=12, darkness=0.35) -> PIL.Image.Image` (blurred, darkened copy).
- Produces: `app.memory_page(number: int)` (an `@st.dialog` showing `CUTSCENE_IMAGES[number]`, title and caption).
- Consumes: `game["cutscenes"]`, `CUTSCENES`, `CUTSCENE_IMAGES`.

- [ ] **Step 1: Write the failing tests**

```python
def test_memory_cards_are_locked_at_the_start():
    at = new_game()
    alts = [str(n.proto) for n in at.get("image")]
    assert sum("locked memory" in a for a in alts) == 3
    assert not any(b.label.startswith("See again") for b in at.button)

def test_a_played_memory_unlocks_its_card_and_can_be_seen_again_for_free():
    at = new_game()
    say(at, "read the diary")          # plays memory 1
    end_cutscene(at)
    alts = [str(n.proto) for n in at.get("image")]
    assert sum("locked memory" in a for a in alts) == 2
    moves = game(at)["moves"]
    click(at, "See again: The Pier")
    assert game(at)["moves"] == moves  # Review Focus 5

def test_locked_picture_is_blurred_and_the_file_is_unchanged():
    from PIL import Image
    from pictures import locked
    path = ROOT / "assets" / "The Pier.jpeg"
    before = path.stat().st_mtime
    assert locked(path).size == Image.open(path).size
    assert path.stat().st_mtime == before
```

- [ ] **Step 2: Run, expect the 3 new tests to FAIL** (`locked` missing, no "locked memory" images).
- [ ] **Step 3: Implement.** `locked()` uses `ImageFilter.GaussianBlur(blur)` and `ImageEnhance.Brightness(darkness)`; cache it in the app with `@st.cache_data`. Cards: one `st.container(horizontal=True)` of three `st.container(border=True)`; locked card = blurred image with `alt="A locked memory"` and caption "???"; unlocked = real image with its title as alt and a small `st.button(f"See again: {title}", icon=":material/replay:")` that calls `memory_page(number)`. Hide the "See again" buttons while a cutscene plays.
- [ ] **Step 4: Run all four test files, expect all PASS.**

### Task 2: Game HUD

**Files:**
- Modify: `version2/app.py` (`live_clock()` and the status panel)
- Test: `tests/test_version2.py`

**Interfaces:**
- Produces: `app.lock_icons(wrong: int, allowed: int) -> str` (markdown, e.g. `":material/lock: :material/lock: :material/lock_open: 2 tries left"`).

- [ ] **Step 1: Write the failing tests**

```python
def test_hud_shows_bars_for_time_and_moves():
    at = new_game()
    say(at, "hello")
    texts = [str(n.proto) for n in at.get("progress")]
    assert any("Time" in t for t in texts) and any("Moves" in t for t in texts)

def test_wrong_codes_are_shown_as_lock_icons_with_text():
    at = new_game()
    play_until_record_played(at)
    say(at, "type 1410")
    assert any("lock_open" in m.value and "2 tries left" in m.value for m in at.markdown)
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement.** In `live_clock()`, under the metric: `st.progress(seconds_left / LIMITS["time_seconds"], text=...)` with text like "Time 4:12". When paused (cutscene) or stopped (door open) show the same bar frozen. Moves: `st.progress(moves / max_moves, text="Moves used 3 / 30")`. Wrong codes: `st.markdown(lock_icons(...))`. Keep the three `st.metric` cards (old tests read them).
- [ ] **Step 4: Run all four test files, expect all PASS.**

### Task 3: Typewriter story

**Files:**
- Modify: `version2/app.py` (chat loop; new message dicts get `"fresh": True`)
- Modify: `tests/test_version2.py` (top: `os.environ["SKY_NO_TYPEWRITER"] = "true"`)

**Interfaces:**
- Produces: `app.words(text: str, delay: float)` generator yielding words with spaces (used by `st.write_stream`).
- Produces: `app.TYPE_DELAY = 0.03`, `app.TYPE_MAX_SECONDS = 1.5`.

- [ ] **Step 1: Write the failing tests**

```python
def test_newest_story_is_marked_shown_before_typing():   # Review Focus 1
    at = new_game()
    say(at, "examine the raincoat")
    assert at.session_state["messages"][-1].get("fresh") is False
    assert any("brass key" in m.value for m in at.markdown)

def test_typewriter_gives_the_time_back_but_not_during_a_cutscene():  # Review Focus 2
    os.environ["SKY_NO_TYPEWRITER"] = "false"
    try:
        at = new_game()
        say(at, "examine the bed")          # no cutscene: deadline moves later
        assert game(at)["deadline"] - time.time() > 300 - 5   # 5 minutes, almost nothing lost
        before = game(at)["deadline"]
        say(at, "read the diary")           # cutscene starts: only the 8 s pause is added
        assert game(at)["deadline"] - before < 8 + 3
    finally:
        os.environ["SKY_NO_TYPEWRITER"] = "true"
```

- [ ] **Step 2: Run, expect FAIL** (no `fresh` key).
- [ ] **Step 3: Implement.** Every new assistant message gets `"fresh": True`. In the chat loop, for a message with `fresh` True: set it to `False` first, then if typing is on, `st.write_stream(words(...))` with the per-word delay chosen so the whole message takes at most `TYPE_MAX_SECONDS`; afterwards add the elapsed seconds to `game["deadline"]` only when no cutscene is playing. Otherwise `st.write` as now.
- [ ] **Step 4: Run all four test files, expect all PASS.**

### Task 4: Item cards

**Files:**
- Modify: `version2/pictures.py` (`ITEM_IMAGES`), `version2/app.py` (replace the Items line)
- Test: `tests/test_version2.py`

**Interfaces:**
- Produces: `pictures.ITEM_IMAGES = {"brass_key": assets/Item_brass_key.png, "vinyl_record": assets/Item_vinyl_record.png}`; `app.ITEM_ICONS = {"brass_key": ":material/key:", "vinyl_record": ":material/album:"}`.

- [ ] **Step 1: Write the failing tests**

```python
def test_item_cards_show_an_icon_and_the_name_when_there_is_no_picture():
    at = new_game()
    say(at, "examine the raincoat")
    say(at, "take the key")
    assert any(":material/key:" in m.value and "brass key" in m.value for m in at.markdown)

def test_empty_backpack_says_so():
    at = new_game()
    assert any("No items yet" in c.value for c in at.caption)
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement.** A row (`st.container(horizontal=True)`) with one small bordered card per item: the picture (`pick()`-style: file if it exists, `alt=` item name) or the icon line, plus the name. Empty: `st.caption("No items yet")`. The existing test `test_examine_and_take_fill_the_items_line` must still pass.
- [ ] **Step 4: Run all four test files, expect all PASS.**

### Task 5: Ending stats

**Files:**
- Modify: `version2/app.py` (`reset_game()`, `lose()`, the Remember/Forget buttons, the ending screen)
- Test: `tests/test_version2.py`

**Interfaces:**
- Produces: `app.save_stats()` storing `st.session_state.stats = {"time_used": int seconds, "moves": int, "wrong_codes": int, "memories": int}` once; `reset_game()` sets `stats = None`.

- [ ] **Step 1: Write the failing tests**

```python
def test_ending_shows_the_run():
    at = new_game()
    play_until_record_played(at)
    say(at, "type 0211")
    click(at, "Remember")
    values = {m.label: m.value for m in at.metric}
    # the quick play-through never reads the diary: memories 2 and 3 only
    assert values["Memories found"] == "2 / 3" and values["Moves"] == "6 / 30"

def test_time_out_shows_full_time_used_never_more():     # Review Focus 4
    at = new_game()
    g = game(at); g["deadline"] = time.time() - 1; at.session_state["game"] = g
    at.run()
    assert {m.label: m.value for m in at.metric}["Time used"] == "5:00"

def test_play_again_clears_stats_and_locks_memories():   # Review Focus 3
    at = new_game()
    play_until_record_played(at)
    say(at, "type 0211"); click(at, "Forget"); click(at, "Play again")
    assert at.session_state["stats"] is None and game(at)["cutscenes"] == []
```

- [ ] **Step 2: Run, expect FAIL.**
- [ ] **Step 3: Implement.** `save_stats()` computes time used as `min(limit, limit - max(0, deadline - now))` (door open: use the moment the door opened, stored as `game["opened_at"]` when the ending choice appears). Call it from `lose()` and both final buttons. Ending screen: a row of four `st.metric` cards ("Time used", "Moves", "Wrong codes", "Memories found") under the ending text.
- [ ] **Step 4: Run all four test files, expect all PASS.**

### Task 6: Check, docs, hand-over

**Files:**
- Modify: `README.md` (test counts), `docs/plans/2026-11-14-game-visuals-design.md` (status: built)

- [ ] **Step 1:** Run all four test files; expected: all pass, about 104 tests.
- [ ] **Step 2:** Start the app headless with the agent API (`--server.enableAgentApi=true`, port 8765), load it, send one chat message in mock mode, check `status: ready`, no exception element, and no new warnings in the console. Stop it.
- [ ] **Step 3:** Update the README test counts and the design status line.
- [ ] **Step 4:** Ask Yada to play once in the browser (mock or real Gemini) and look at all five changes. Fix what Yada finds (test first).
- [ ] **Step 5:** Show `git status`, the files and the commit message; commit only after Yada's OK:

```
M12: game-like look for Version 2 (memory cards, HUD, typewriter story, item cards, ending stats)
```
