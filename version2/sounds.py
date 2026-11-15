"""Version 2: the music file and the small helpers that make it quiet and hide the grey browser player.
No Streamlit and no LLM in this file."""
from pathlib import Path

ASSETS = Path(__file__).parent.parent / "assets"
MUSIC_FILE = ASSETS / "Music.mp3"  # "JRPG Piano" by Joth, CC0 (opengameart.org/content/jrpg-piano)
MUSIC_VOLUME = 0.12                # 12 %: the game starts the music very quietly


def hide_player_css():
    """The browser's grey audio bar does not fit the pixel theme, so it is hidden.
    The music still plays; the player switches it on and off with the Music switch."""
    return '<style>[data-testid="stAudio"] { display: none; }</style>'


def quiet_script(level):
    """A tiny script: set the volume of the music player in the sidebar ONCE, when it appears."""
    return f"""<script>
(function () {{
  var level = {level};
  var tries = 0;
  function quiet() {{
    document.querySelectorAll('[data-testid="stSidebar"] audio').forEach(function (a) {{
      if (!a.dataset.quiet) {{
        a.volume = level;
        a.dataset.quiet = "1";
        a.addEventListener("playing", function () {{ a.dataset.playing = "1"; }});
      }}
    }});
  }}
  quiet();
  var timer = setInterval(function () {{ quiet(); tries += 1; if (tries > 20) clearInterval(timer); }}, 250);
}})();
</script>"""
