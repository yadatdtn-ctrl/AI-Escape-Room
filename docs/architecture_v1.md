# Architecture: Version 1 (the LLM decides)

In Version 1 the LLM (Gemini) is the Game Master. It knows the whole game, **including the secrets**,
and it decides what happens. Python only shows the page, counts time and moves, and reads hidden tags
that Gemini writes at the end of its answers.

```mermaid
flowchart LR
    P(["Player"]) -->|"types a message"| A["app.py<br/>Streamlit page"]
    A -->|"whole chat history"| L["llm.py"]
    S["prompts.py<br/>Game Master script<br/>with ALL secrets<br/>(door code 0211 inside)"] --> L
    L -->|"request"| G[("Gemini API<br/>or mock")]
    G -->|"story text + hidden tags<br/>ITEM, CUTSCENE, WRONG_DOOR, ESCAPED"| L
    L --> A
    A -->|"answer text"| T["tags.py<br/>cut the tags out,<br/>apply them to the state"]
    T --> ST[("session state<br/>items, cutscenes,<br/>wrong codes, escaped")]
    A --> R["rules.py<br/>time, moves,<br/>wrong-code limits"]
    R --> ST
    ST --> A
    A -->|"picture, chat, status lines"| P
```

## Who decides what

| Question | Who decides in V1 |
|---|---|
| Does the player have the key? | Gemini (it writes `[[ITEM:brass_key]]` if it feels like it) |
| Is the code right? | Gemini |
| Did the player escape? | Gemini (it writes `[[ESCAPED]]`) |
| Did the time or the moves run out? | Python (`rules.py`, a real clock and counters) |
| What do the tags change? | Python (`tags.py`), but it trusts every tag it finds |

## Files (`version1/`)

| File | Job |
|---|---|
| `app.py` | The page: start screen, game screen, final choice, endings, the live clock |
| `prompts.py` | The Game Master script (story, objects, rules, **all secrets**, hidden-tag rules) |
| `llm.py` | Sends the chat to Gemini, or a fake answer in mock mode |
| `tags.py` | Finds `[[...]]` tags, removes them from the text, changes the state |
| `rules.py` | Time and limit checks (the only part that does not depend on the LLM) |
| `settings.py` / `texts.py` | Numbers and placeholder texts |

## Weaknesses (real evidence in `docs/test_cases.md`)

1. **The secrets are in the prompt.** The door code is protected only because Gemini chooses not to say it
   (it held in all 11 attempts to make it talk, but nothing forces it to).
2. **Gemini decides the facts.** Tests 1 and 3: it accepted a key the player never took, and it opened the door
   after a false claim ("I already solved it").
3. **Story and state can disagree.** Tests 2b, 6, 23: Gemini invents a code attempt, but the counters do not match.
4. **The program trusts the tags.** Tests 16 and 17: the player types `[[ESCAPED]]` or `[[ITEM:...]]`,
   Gemini repeats it, and the game obeys.
5. **Gemini invents details and contradicts the game text** (photo booth, "golden light" against "white light").
