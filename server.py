from __future__ import annotations

import json
import mimetypes
import os
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, quote_plus, urlparse


ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "tierlist.json"
HOST = "127.0.0.1"
PORT = 8000


# Verified Spotify track IDs. Keeping these in the catalog source means a
# Ctrl+click can open the exact track in the Spotify desktop app instead of
# making Spotify search for the song title.
SPOTIFY_TRACK_IDS = {
    "Carolina": "3Dwq1oiOFys6Sxr5SslmXw",
    "Meet Me in the Hallway": "4u9Y4Z9i9VaAbBK7rW1Rha",
    "Two Ghosts": "4B1rpPmQXwj78wk6aIGwwU",
    "Sweet Creature": "5kRPPEWFJIMox5qIkQkiz5",
    "Only Angel": "5Lbsc65org0b85kNsPkluY",
    "Kiwi": "33SNO8AaciGbNaQFkxvPrW",
    "Ever Since New York": "5LABCxgmP7DATATIJXOh6n",
    "Woman": "33bURv895AN4FkBvgFo2dx",
    "From the Dining Table": "1IF5UcqRO42D12vYwceOY6",
    "Sign of the Times": "5Ohxk2dO5COHF1krpoPigN",
    "Golden": "45S5WTQEGOB1VHr1Q4FuPl",
    "Watermelon Sugar": "6UelLqGlWMcVH1E5c4H7lY",
    "Adore You": "3jjujdWJ72nww5eGnfs2E7",
    "Lights Up": "2plLJpUcYPFrl1sW2pMG63",
    "Cherry": "2IOFZdYYkFxEHVz1w34PoL",
    "Falling": "1ZMiCix7XSAbfAJlEZWMCp",
    "To Be So Lonely": "5JiH89mHrv9oWHlD0T326z",
    "She": "6SQLk9HSNketfgs2AyIiMs",
    "Sunflower, Vol. 6": "6iYMfxznTBlcVOgRHab2W0",
    "Canyon Moon": "5IhzJOXNE7ki0IIJbZbnGq",
    "Treat People with Kindness": "03mMSLEJCPoGJwQhHpN5y0",
    "Fine Line": "6VzcQuzTNTMFnJ6rBSaLH9",
    "Music for a Sushi Restaurant": "4VqPOruhp5EdPBeR92t6lQ",
    "Late Night Talking": "1qEmFfgcLObUfQm0j1W2CK",
    "Grapejuice": "4j6kId9QIqhoXvqHKgSKa0",
    "As It Was": "4LRPiXqCikLlN15c3yImP",
    "Daylight": "51Zw1cKDgkad0CXv23HCMU",
    "Little Freak": "1qMMYpVatbRITKCfq1gasi",
    "Matilda": "6uvh0In7u1Xn4HgxOfAn8O",
    "Cinema": "35TyJIMR3xRouUuo2sjS6v",
    "Daydreaming": "69w5X6uTrOaWM32IetSzvO",
    "Keep Driving": "2NcQic8JxdjAlAHuNbOIRE",
    "Satellite": "0rzaRSujxA0bKyjJl6vHYq",
    "Love of My Life": "1mw0RgNXIpYRyyCdBQbLgA",
    "Boyfriends": "6qj02zSeEJGWZ4c0dn5QzJ",
    "Aperture": "45Z3m6yazmAi4jZuW0tzW0",
    "American Girls": "7gtG45ieyQzKtNKobfLd49",
    "Ready, Steady, Go!": "0i4qKfuKJ3juUsEwnJAxk3",
    "Are You Listening Yet?": "7s7v5EoNLD6TwDu4Nw51Oy",
    "Taste Back": "3xClevycpBON8bkyxFbAna",
    "Girl Crush": "4YutJsNwBBInE8vemufpQ8",
    "Dance No More": "0VV0AMmgLBUhzuFedr3F3e",
    "Coming Up Roses": "0QPdjsMOUhwouq1NS3HwfQ",
    "Paint by Numbers": "56k68P3bFQvnKw89hizJFZ",
    "The Waiting Game": "0tV6LXuVzJR4yifqwQuNwN",
    "Pop": "028i7HBfp8uE5epmx5ieMA",
}


def default_tiers() -> list[dict]:
    return [
        {"id": "tier-s", "label": "S", "color": "#ff7f7f", "items": []},
        {"id": "tier-a", "label": "A", "color": "#ffbf7f", "items": []},
        {"id": "tier-b", "label": "B", "color": "#ffdf7f", "items": []},
        {"id": "tier-c", "label": "C", "color": "#ffff7f", "items": []},
        {"id": "tier-d", "label": "D", "color": "#bfff7f", "items": []},
        {"id": "tier-f", "label": "F", "color": "#7fbfff", "items": []},
    ]


def default_state() -> dict:
    tab_id = "tab-main"
    return {
        "activeTabId": tab_id,
        "tabs": [{"id": tab_id, "name": "Tierlist 1", "tiers": default_tiers(), "unranked": []}],
        "items": {},
    }


def restored_catalog_state() -> dict:
    catalog = [
        ("Carolina", "Harry Styles"), ("Two Ghosts", "Harry Styles"), ("Sweet Creature", "Harry Styles"),
        ("Only Angel", "Harry Styles"), ("Kiwi", "Harry Styles"), ("Ever Since New York", "Harry Styles"),
        ("Woman", "Harry Styles"), ("From the Dining Table", "Harry Styles"), ("Meet Me in the Hallway", "Harry Styles"),
        ("Sign of the Times", "Harry Styles"),
        ("Golden", "Fine Line"), ("Watermelon Sugar", "Fine Line"), ("Adore You", "Fine Line"),
        ("Lights Up", "Fine Line"), ("Cherry", "Fine Line"), ("Falling", "Fine Line"),
        ("To Be So Lonely", "Fine Line"), ("She", "Fine Line"), ("Sunflower, Vol. 6", "Fine Line"),
        ("Canyon Moon", "Fine Line"), ("Treat People with Kindness", "Fine Line"), ("Fine Line", "Fine Line"),
        ("Music for a Sushi Restaurant", "Harry's House"), ("Late Night Talking", "Harry's House"),
        ("Grapejuice", "Harry's House"), ("As It Was", "Harry's House"), ("Daylight", "Harry's House"),
        ("Little Freak", "Harry's House"), ("Matilda", "Harry's House"), ("Cinema", "Harry's House"),
        ("Daydreaming", "Harry's House"), ("Keep Driving", "Harry's House"), ("Satellite", "Harry's House"),
        ("Boyfriends", "Harry's House"), ("Love of My Life", "Harry's House"),
        ("Trouble", "Kiss All the Time. Disco, Occasionally."), ("Lay Down", "Kiss All the Time. Disco, Occasionally."),
        ("Are You Listening Yet?", "Kiss All the Time. Disco, Occasionally."), ("Aperture", "Kiss All the Time. Disco, Occasionally."),
        ("Dance No More", "Kiss All the Time. Disco, Occasionally."), ("American Girls", "Kiss All the Time. Disco, Occasionally."),
        ("Taste Back", "Kiss All the Time. Disco, Occasionally."), ("Coming Up Roses", "Kiss All the Time. Disco, Occasionally."),
        ("Paint by Numbers", "Kiss All the Time. Disco, Occasionally."), ("Ready, Steady, Go!", "Kiss All the Time. Disco, Occasionally."),
        ("The Waiting Game", "Kiss All the Time. Disco, Occasionally."), ("Pop", "Kiss All the Time. Disco, Occasionally."),
        ("Girl Crush", "Spotify Singles", "https://i1.sndcdn.com/artworks-000250497136-n2qfo1-t1080x1080.jpg"),
        ("Medicine", "Unreleased", "/assets/unreleased/medicine.png"), ("Anna", "Unreleased", "/assets/unreleased/anna.png"),
        ("Complicated Freak", "Unreleased", "/assets/unreleased/complicated-freak.png"), ("Baby Honey", "Unreleased", "/assets/unreleased/baby-honey.png"),
        ("Already Home", "Unreleased", "/assets/unreleased/already-home.png"), ("Him", "Unreleased", "/assets/unreleased/him.png"),
    ]
    items = {}
    unranked = []
    for index, entry in enumerate(catalog, start=1):
        text, album, *art = entry
        item_id = f"song-{index:02d}"
        search_text = f"Harry Styles {text}"
        link = (
            f"https://www.youtube.com/results?search_query={quote_plus(search_text)}"
            if album == "Unreleased"
            else f"spotify:track:{SPOTIFY_TRACK_IDS[text]}"
            if text in SPOTIFY_TRACK_IDS
            else f"spotify:search:{quote(search_text)}"
        )
        item = {"id": item_id, "text": text, "album": album, "link": link}
        if art:
            item["art"] = art[0]
        items[item_id] = item
        unranked.append(item_id)
    state = default_state()
    state["items"] = items
    state["tabs"][0]["unranked"] = unranked
    return state


def ensure_item_links(state: dict) -> bool:
    changed = False
    for item in state.get("items", {}).values():
        search_text = f"Harry Styles {item.get('text', '')}"
        track_id = SPOTIFY_TRACK_IDS.get(item.get("text", ""))
        expected_link = (
            f"https://www.youtube.com/results?search_query={quote_plus(search_text)}"
            if item.get("album") == "Unreleased"
            else f"spotify:track:{track_id}"
            if track_id
            else f"spotify:search:{quote(search_text)}"
        )
        if item.get("link") == expected_link:
            continue
        item["link"] = expected_link
        changed = True
    return changed


def migrate_state(state: dict) -> dict:
    if "tabs" in state:
        return state
    if {"tiers", "unranked", "items"}.issubset(state):
        tab_id = "tab-main"
        return {
            "activeTabId": tab_id,
            "tabs": [{"id": tab_id, "name": "Tierlist 1", "tiers": state["tiers"], "unranked": state["unranked"]}],
            "items": state["items"],
        }
    return state


def load_state() -> dict:
    try:
        with STATE_FILE.open("r", encoding="utf-8") as file:
            raw_state = json.load(file)
        state = migrate_state(raw_state)
        validate_state(state)
        links_added = ensure_item_links(state)
        if state != raw_state or links_added:
            save_state(state)
        return state
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        state = default_state()
        save_state(state)
        return state


def validate_state(state: dict) -> None:
    if not isinstance(state, dict) or not isinstance(state.get("items"), dict):
        raise ValueError("State is missing items")
    tabs = state.get("tabs")
    if not isinstance(tabs, list) or not tabs:
        raise ValueError("State is missing tabs")
    tab_ids = set()
    if state.get("activeTabId") not in {tab.get("id") for tab in tabs if isinstance(tab, dict)}:
        raise ValueError("Active tab does not exist")
    expected_items = set(state["items"])
    for tab in tabs:
        if not isinstance(tab, dict) or not tab.get("id") or not tab.get("name"):
            raise ValueError("Invalid tab")
        if tab["id"] in tab_ids:
            raise ValueError("Duplicate tab id")
        tab_ids.add(tab["id"])
        if not isinstance(tab.get("tiers"), list) or not isinstance(tab.get("unranked"), list):
            raise ValueError("Invalid tab board")
        tier_ids = set()
        locations = set()
        for tier in tab["tiers"]:
            if not isinstance(tier, dict) or not tier.get("id") or not isinstance(tier.get("items"), list):
                raise ValueError("Invalid tier")
            if tier["id"] in tier_ids:
                raise ValueError("Duplicate tier id")
            tier_ids.add(tier["id"])
            for item_id in tier["items"]:
                if item_id in locations:
                    raise ValueError("Item appears more than once in a tab")
                locations.add(item_id)
        for item_id in tab["unranked"]:
            if item_id in locations:
                raise ValueError("Item appears more than once in a tab")
            locations.add(item_id)
        if locations != expected_items:
            raise ValueError("Every item must have exactly one location in every tab")


def save_state(state: dict) -> None:
    validate_state(state)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix="tierlist-", suffix=".json", dir=STATE_FILE.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            json.dump(state, file, indent=2, ensure_ascii=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_name, STATE_FILE)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/state":
            self.send_json(load_state())
            return
        if path == "/":
            self.serve_file("index.html", "text/html; charset=utf-8")
            return
        if path in {"/app.js", "/style.css"}:
            content_type = "application/javascript; charset=utf-8" if path.endswith(".js") else "text/css; charset=utf-8"
            self.serve_file(path[1:], content_type)
            return
        if path.startswith("/assets/"):
            asset_path = (ROOT / path.lstrip("/")).resolve()
            assets_root = (ROOT / "assets").resolve()
            try:
                asset_path.relative_to(assets_root)
            except ValueError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            content_type = mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream"
            self.serve_file(str(asset_path), content_type)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/state":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            state = json.loads(self.rfile.read(length).decode("utf-8"))
            save_state(state)
            self.send_json({"ok": True})
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except OSError as error:
            self.send_json({"error": f"Could not save tierlist: {error}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def serve_file(self, name: str, content_type: str) -> None:
        file_path = Path(name) if Path(name).is_absolute() else ROOT / name
        try:
            content = file_path.read_bytes()
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")


if __name__ == "__main__":
    print(f"Tierlist running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
