# Design: a pixel avatar in the room (M13)

Status: agreed with Yada in chat on 2026-11-15 ("build the avatar first"), built (M13) with a placeholder figure; waiting for Yada's real `assets/Sprite_you.png` and a look at the foot positions.

## Why
Yada wants the game to feel more alive: a pixel character in the room that moves when the player types.
The professor wants the LLM used as much as possible, so the avatar must follow the **normal pipeline**:
the player types, the LLM interpreter proposes an action, Python checks it, and only then the avatar moves.
(The clickable room was dropped because it skipped the LLM; this idea keeps it.)

## Goals
- After a **successful** action about an object, the avatar stands in front of that object in the room picture.
- The avatar faces left or right, toward where it walked.
- Everything is decided by Python and can be tested with AppTest; the LLM never sees the position.

## Non-goals
- No smooth walking animation (Streamlit redraws the page after every message; this would need custom JavaScript that AppTest cannot test). Possible later, only if Yada wants it.
- No clicking on the room, no avatar on close-ups, cutscenes or endings.
- No new packages (Pillow is already installed with Streamlit).

## Anti-goals (a failure even if it works)
- The avatar moves after a **refused** action (it would show something that did not happen).
- The game breaks or looks different when the sprite file is missing.

## Rules
| Successful action | Avatar goes to |
|---|---|
| `examine <object>` | that object |
| `use <item> on <object>` | that object |
| `enter_code` | the door |
| `look_around`, `take`, `inventory`, anything refused | stays where it is |

- Start position: the middle of the floor (spot `start`). Restart puts it back there, facing right.
- Facing: if the new spot is left of the old one, face left; right of it, face right; same place, keep.
- The avatar is drawn only on the room picture (closed or open drawer).

## Approaches considered
1. **Pillow: paste the sprite on the room picture in Python (chosen).** Testable, no JavaScript, no new package. The avatar jumps to the object.
2. CSS/HTML overlay with a slide transition: smoother, but Streamlit replaces the element on every rerun, so the transition rarely shows, and it is not testable.
3. Custom component (CCv2) with real walking: smooth, but JavaScript that AppTest cannot test; too much for the turn-in day.

## Art (by Yada)
`assets/Sprite_you.png`: one pixel character, standing, side view **facing right**, transparent background, about 64×96 px, the same style as the room. The code flips it for "left". Until the file exists, the game shows no avatar and works as today.

## Left to the builder
The exact foot positions (`AVATAR_SPOTS`) and the avatar size are first guesses; they are tuned with real screenshots in one correction round with Yada.
