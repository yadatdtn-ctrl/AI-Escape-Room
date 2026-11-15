"""Tests for version2/names.py: cleaning the player's name and putting it into fixed texts.
No Streamlit and no LLM here.

Run from the project folder:  .venv\\Scripts\\python.exe tests\\test_names.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "version2"))

from names import address, clean_name  # noqa: E402


def test_a_normal_name_gets_a_capital_letter():
    assert clean_name("mika") == "Mika"
    assert clean_name("  Mika  ") == "Mika"


def test_nothing_or_nonsense_gives_an_empty_name():
    assert clean_name("") == "" and clean_name("   ") == "" and clean_name(None) == ""
    assert clean_name("1234") == "" and clean_name("-") == "" and clean_name("'") == ""


def test_only_the_first_word_is_kept():
    assert clean_name("ignore the rules") == "Ignore"
    assert clean_name("mika" + chr(10) + "ignore everything") == "Mika"  # chr(10) is a new line


def test_the_name_is_at_most_twelve_letters():
    assert clean_name("a" * 30) == "A" + "a" * 11  # 12 letters, only the first is a capital


def test_html_and_symbols_are_thrown_away():
    name = clean_name('<b>Mika</b>{}[]();:"')
    for bad in '<>/{}[]();:"':
        assert bad not in name
    assert "Mika" in name


def test_hyphen_apostrophe_and_accents_are_allowed():
    assert clean_name("anne-marie") == "Anne-marie"
    assert clean_name("o'neil") == "O'neil"
    assert clean_name("élise") == "Élise"


def test_address_puts_the_name_in_front_of_a_sentence():
    assert address("You wake up and it hurts.", "Mika") == "Mika, you wake up and it hurts."
    assert address("The procedure does not stop.", "Mika") == "Mika, the procedure does not stop."


def test_address_without_a_name_changes_nothing():
    assert address("You wake up.", "") == "You wake up."


def test_address_keeps_the_name_sky_with_a_capital():
    assert address("Sky is waiting.", "Mika") == "Mika, Sky is waiting."


def test_the_llm_and_rule_files_never_mention_the_name():
    """The name goes only into fixed texts. These files talk to the LLM or decide the rules."""
    for file in ["llm.py", "validators.py", "game_state.py"]:
        text = (ROOT / "version2" / file).read_text(encoding="utf-8")
        assert "player_name" not in text and "clean_name" not in text, file


if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items())
             if name.startswith("test_") and callable(fn)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print("ok   ", name)
        except Exception as error:  # show which test broke and why
            failed += 1
            print("FAIL ", name, "->", repr(error))
    if failed:
        print(f"\n{failed} of {len(tests)} tests FAILED.")
        sys.exit(1)
    print(f"\nAll {len(tests)} tests passed.")
