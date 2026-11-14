# Design: a more game-like look for Version 2 (M12)

Date: 2026-11-14. Status: built (M12), checked headless; waiting for Yada to play it in the browser.

## Why

Yada wants the game to look and feel more like a game ("more visual"), in the existing pixel style.
This is only about what the player **sees**. The rules (Python) and the two LLM jobs (interpreter,
narrator) do not change, so the assignment's focus on the LLM stays the same.

## Goals

1. **Memories found:** three cards, one per cutscene (The Pier, The Rooftop, That Night). Locked
   (dark, blurred picture, title "???") until the memory has played; then the real picture and its
   title. A button on an unlocked card opens the memory again in a small window (free, no move,
   no LLM).
2. **Game HUD:** the status panel keeps its three numbers and gets pictures: a bar for the time left,
   a bar for the moves used, and the wrong codes as three lock icons (closed = try left,
   open = used). Every bar and icon also has text, so nothing depends on color alone.
3. **Typewriter story:** the newest narrator message appears word by word, once. Older messages
   show at once. It takes at most about 1.5 seconds, and that time is given back to the clock.
4. **Item cards:** the "Items" line becomes small cards with a picture of each item. Until Yada's
   pictures exist, a card shows an icon (key, record) and the name.
5. **Ending stats:** the ending screen shows the run: time used, moves, wrong codes, memories found.

## Non-goals

- No change to rules, limits, the interpreter, the narrator or the config texts.
- No JavaScript or custom component (the clickable room was dropped for this reason).
- No sound, no animation besides the typewriter text and the existing cutscene fade-in.
- Version 1 is not changed.

## Anti-goals (would make this a failure even if it works)

- The look gives away a solution (for example a card or icon that names the next step).
- A player's typed text is lost or the clock takes time the player did not spend.
- The page becomes slower or the tests stop being able to check it.

## Approaches considered

| Approach | Trade-off | Chosen? |
|---|---|---|
| **Native Streamlit parts** (`st.progress`, `st.image`, `st.dialog`, `st.write_stream`, Material icons) | Limited look, but no new package, works with the theme, testable with AppTest | **Yes** |
| Custom HTML/CSS cards with `st.html` | Freer look, but against the Streamlit guide, harder to test, may break with the theme | No |
| A custom component (JavaScript) | Most freedom, but not testable by AppTest (lesson from the clickable-room prototype) | No |

## Decisions (calls by Claude, Yada can change them)

- Locked memory picture = the real picture, blurred and darkened by Python at display time
  (files in `assets/` are not changed). Shows the shape, not the content.
- Typewriter speed: about 0.03 s per word, capped at 1.5 s per message. Turned off in the tests
  with an environment variable so the tests stay fast. The text is marked as shown *before* it
  starts, so a fast next message cannot lose it (lesson from test 20).
- Item pictures: `assets/Item_brass_key.png` and `assets/Item_vinyl_record.png` (Yada makes them);
  fallback icons `:material/key:` and `:material/album:`.
- Ending stats are saved once, at the moment the ending starts, so they do not change later.
- The diary page button stays as it is.

## Tests (written first)

AppTest, mock mode: locked cards before a memory, unlocked after; replay costs no move; HUD bars
and lock icons match the state; the newest message is shown in full after the run; item card
fallback; the ending shows the stats; all old tests still pass.

## What is left to the builder

Exact layout spacing, captions and icon choice, following `developing-with-streamlit`.
