"""Version 2: the referee. Python checks every action against the rules.

The LLM only PROPOSES an action (a small dict). Here we decide if it is allowed,
change the state, and build the "facts" that the narrator may describe.
No Streamlit and no LLM in this file.
"""
from game_state import add_item, play_cutscene, reveal

ACTIONS = ["look_around", "examine", "take", "use", "enter_code", "inventory"]


# ---------- small helpers ----------
def find_id(word, table):
    """Find an id by its id, its name or an alias. Returns None if unknown."""
    if not isinstance(word, str):
        return None
    word = word.strip().lower()
    for entry_id, entry in table.items():
        names = [entry_id, entry.get("name", "")] + entry.get("aliases", [])
        if word in [n.lower() for n in names]:
            return entry_id
    return None


def item_names(state, config):
    """Names of the items the player carries."""
    return [config["items"][i]["name"] for i in state["inventory"]]


def result(state, config, action, allowed, reason, about=None, text=None, cutscene=None,
           must_include=None):
    """One answer of the referee. 'facts' is all the narrator is allowed to know."""
    if text is None:
        text = config["plain_messages"].get(reason, "")
    facts = {
        "outcome": "success" if allowed else "refused",
        "action": action,
        "reason": reason,
        "about": about,
        "text": text,  # a sentence from the config, never the player's words
        "must_include": must_include or [],  # clue phrases the story has to keep word for word
        "inventory": item_names(state, config),
    }
    return {"allowed": allowed, "reason": reason, "facts": facts, "cutscene": cutscene}


def refuse(state, config, action, reason, about=None):
    return result(state, config, action, False, reason, about)


# ---------- one function per action ----------
def do_look_around(action, state, config):
    names = [obj["name"] for obj in config["objects"].values()]
    text = "In the room you see: " + ", ".join(names) + "."
    return result(state, config, "look_around", True, None, text=text)


def do_inventory(action, state, config):
    names = item_names(state, config)
    text = "You carry: " + ", ".join(names) + "." if names else "You carry nothing."
    return result(state, config, "inventory", True, None, text=text)


def do_examine(action, state, config):
    target = action.get("target")
    object_id = find_id(target, config["objects"])
    if object_id is not None:
        obj = config["objects"][object_id]
        if object_id not in state["examined"]:
            state["examined"].append(object_id)
        reveal(state, obj.get("reveals", []))
        text = obj["examine"]
        clues = obj.get("must_include", [])
        if object_id == "drawer" and state["drawer_open"]:
            text = obj["examine_when_open"]
            clues = []
        cutscene = play_cutscene(state, obj.get("cutscene_on_first_examine"))
        return result(state, config, "examine", True, None, obj["name"], text, cutscene, clues)
    item_id = find_id(target, config["items"])
    if item_id is None:
        return refuse(state, config, "examine", "UNKNOWN_TARGET")
    item = config["items"][item_id]
    if item_id not in state["revealed"]:
        return refuse(state, config, "examine", "NOT_VISIBLE", item["name"])
    return result(state, config, "examine", True, None, item["name"], item["description"],
                  must_include=item.get("must_include", []))


def do_take(action, state, config):
    item_id = find_id(action.get("target"), config["items"])
    if item_id is None:
        return refuse(state, config, "take", "UNKNOWN_TARGET")
    item = config["items"][item_id]
    if item_id not in state["revealed"]:
        return refuse(state, config, "take", "NOT_VISIBLE", item["name"])
    if item_id in state["inventory"]:
        return refuse(state, config, "take", "ALREADY_HAVE", item["name"])
    add_item(state, item_id)
    return result(state, config, "take", True, None, item["name"], f"You take the {item['name']}.")


def do_use(action, state, config):
    item_id = find_id(action.get("item"), config["items"])
    if item_id is None:
        return refuse(state, config, "use", "UNKNOWN_TARGET")
    item = config["items"][item_id]
    if item_id not in state["inventory"]:
        return refuse(state, config, "use", "NOT_IN_INVENTORY", item["name"])
    object_id = find_id(action.get("target"), config["objects"])
    if object_id is None:
        return refuse(state, config, "use", "UNKNOWN_TARGET")
    obj = config["objects"][object_id]
    if obj.get("opened_by") != item_id and obj.get("accepts") != item_id:
        return refuse(state, config, "use", "WRONG_TOOL", obj["name"])

    if object_id == "drawer":  # the brass key opens the drawer
        if state["drawer_open"]:
            return refuse(state, config, "use", "ALREADY_DONE", obj["name"])
        state["drawer_open"] = True
        reveal(state, obj["when_opened"]["reveals"])
        cutscene = play_cutscene(state, obj["when_opened"]["cutscene"])
        opened = obj["when_opened"]
        return result(state, config, "use", True, None, obj["name"], opened["text"], cutscene,
                      opened.get("must_include", []))

    # the only other case: the vinyl record on the record player
    if state["record_played"]:
        return refuse(state, config, "use", "ALREADY_DONE", obj["name"])
    state["record_played"] = True
    cutscene = play_cutscene(state, obj["when_used"]["cutscene"])
    return result(state, config, "use", True, None, obj["name"], obj["when_used"]["text"], cutscene)


def do_enter_code(action, state, config):
    object_id = find_id(action.get("target"), config["objects"])
    if object_id is None:
        return refuse(state, config, "enter_code", "UNKNOWN_TARGET")
    obj = config["objects"][object_id]
    if not obj.get("code_lock"):
        return refuse(state, config, "enter_code", "NO_CODE_LOCK", obj["name"])
    if state["door_open"]:
        return refuse(state, config, "enter_code", "ALREADY_DONE", obj["name"])
    code = action.get("code")
    if not (isinstance(code, str) and len(code) == 4 and code.isascii() and code.isdigit()):
        return refuse(state, config, "enter_code", "BAD_FORMAT", obj["name"])  # not counted
    if not state["record_played"]:  # the door ignores every code until the record was played
        return refuse(state, config, "enter_code", "NOT_READY", obj["name"])  # not counted
    if code != config["solutions"]["door_code"]:
        state["wrong_codes"] += 1
        return refuse(state, config, "enter_code", "WRONG_CODE", obj["name"])
    state["door_open"] = True
    return result(state, config, "enter_code", True, None, obj["name"],
                  config["plain_messages"]["DOOR_OPENS"])


HANDLERS = {
    "look_around": do_look_around,
    "examine": do_examine,
    "take": do_take,
    "use": do_use,
    "enter_code": do_enter_code,
    "inventory": do_inventory,
}


# ---------- the main entry ----------
def handle_action(action, state, config):
    """Check one action from the interpreter, update the state if allowed."""
    name = action.get("action") if isinstance(action, dict) else None
    if not isinstance(name, str) or name not in HANDLERS:
        return refuse(state, config, "invalid", "UNKNOWN_ACTION")
    return HANDLERS[name](action, state, config)


# ---------- limits ----------
def time_is_up(state, now):
    """True if the clock ran out. 'now' is a time in seconds (time.time())."""
    return (not state["door_open"]) and now >= state["deadline"]


def check_limits(state, config):
    """Return why the player lost ("codes" or "moves"), or None if the game goes on."""
    if state["door_open"]:
        return None  # the player already opened the door
    if state["wrong_codes"] >= config["limits"]["max_wrong_codes"]:
        return "codes"
    if state["moves"] >= config["limits"]["max_moves"]:
        return "moves"
    return None
