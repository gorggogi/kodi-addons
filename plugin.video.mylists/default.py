# -*- coding: utf-8 -*-
"""My Lists: handpicked addon folders for home screen widgets.

plugin://plugin.video.mylists/              lists the entries in lists.txt
plugin://plugin.video.mylists/?list=NAME    lists the entries in lists_NAME.txt
plugin://plugin.video.mylists/?mode=manage  opens the Manage menu (Configure button)

An entry can be a single folder, or everything in a folder minus the items you hide.
"""
import glob
import json
import os
import re
import sys
from urllib.parse import parse_qsl, unquote

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

ADDON = xbmcaddon.Addon()
ADDON_DIR = xbmcvfs.translatePath(ADDON.getAddonInfo("path"))
# Lists live in addon_data so addon updates don't wipe them.
DATA_DIR = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
TITLE = "My Lists"
dialog = xbmcgui.Dialog()


def seed_data_dir():
    """On first run, copy the starter lists shipped with the addon into addon_data."""
    if os.path.exists(os.path.join(DATA_DIR, "lists.txt")):
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    for src in glob.glob(os.path.join(ADDON_DIR, "lists*.txt")):
        dst = os.path.join(DATA_DIR, os.path.basename(src))
        if not os.path.exists(dst):
            with open(src, encoding="utf-8") as f, open(dst, "w", encoding="utf-8") as g:
                g.write(f.read())
    if not os.path.exists(os.path.join(DATA_DIR, "lists.txt")):
        open(os.path.join(DATA_DIR, "lists.txt"), "w", encoding="utf-8").close()


# ---------- list files ----------

def clean_name(name):
    return "".join(c for c in name.lower().replace(" ", "_") if c.isalnum() or c in "_-")


def list_file(name):
    return os.path.join(DATA_DIR, "lists_%s.txt" % name if name else "lists.txt")


def widget_path(name):
    return "plugin://plugin.video.mylists/" + ("?list=%s" % name if name else "")


def all_list_names():
    names = [""]
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "lists_*.txt"))):
        names.append(os.path.basename(path)[6:-4])
    return names


def list_title(name):
    return name.replace("_", " ").capitalize() if name else "Main"


def read_entries(name):
    entries = []
    path = list_file(name)
    if not os.path.exists(path):
        return entries
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("-"):
                # hides one item of the "everything" entry above it
                if entries and entries[-1]["all"]:
                    entries[-1]["hide"].append(line[1:].strip())
                continue
            is_all = line.startswith("+")
            if is_all:
                line = line[1:]
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 2 or not parts[1]:
                continue
            entries.append({"label": parts[0], "path": parts[1], "icon": parts[2] if len(parts) > 2 else "",
                            "all": is_all, "hide": []})
    return entries


def write_entries(name, entries):
    lines = [
        "# Used by %s" % widget_path(name),
        "# One entry per line:  Label | path | icon (icon is optional)",
        "# A line starting with + adds everything in that folder.",
        "# Lines starting with - under it hide an item by its name.",
        "# Elementum paths must NOT end with a slash.",
    ]
    for e in entries:
        label = e["label"].replace("|", "/")
        line = "%s%s | %s" % ("+ " if e.get("all") else "", label, e["path"])
        if e.get("icon"):
            line += " | %s" % e["icon"]
        lines.append(line)
        if e.get("all"):
            lines += ["- %s" % h for h in e.get("hide", [])]
    with open(list_file(name), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ---------- widget listing ----------

def show_list(handle, name):
    for e in read_entries(name):
        if e["all"]:
            add_everything(handle, e)
            continue
        item = xbmcgui.ListItem(label=e["label"])
        if e["icon"]:
            item.setArt({"icon": e["icon"], "thumb": e["icon"]})
        xbmcplugin.addDirectoryItem(handle, e["path"], item, isFolder=True)
    if not name and xbmc.getCondVisibility("Window.IsActive(skinsettings)"):
        # FENtastic's widget browser runs from Skin Settings, widgets run on Home.
        # So only there, offer the other lists as folders to pick instead of typing their path.
        for other in all_list_names()[1:]:
            item = xbmcgui.ListItem(label="My Lists: %s" % list_title(other))
            item.setArt({"icon": "DefaultFolder.png", "thumb": "DefaultFolder.png"})
            xbmcplugin.addDirectoryItem(handle, widget_path(other), item, isFolder=True)
    xbmcplugin.endOfDirectory(handle, cacheToDisc=False)


def add_everything(handle, e):
    """List every item in the entry's folder, except the hidden ones."""
    hide = set(h.lower() for h in e["hide"])
    for f in get_dir(e["path"]):
        if strip_tags(f["label"]).lower() in hide:
            continue
        item = xbmcgui.ListItem(label=f["label"])
        icon = clean_icon(f.get("art", {}), f.get("thumbnail", ""))
        if icon:
            item.setArt({"icon": icon, "thumb": icon})
        is_folder = f.get("filetype") == "directory"
        if not is_folder:
            item.setProperty("IsPlayable", "true")
        xbmcplugin.addDirectoryItem(handle, clean_path(f["file"]) if is_folder else f["file"], item, isFolder=is_folder)


# ---------- browsing addons to pick a folder ----------

def rpc(method, params):
    req = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    return json.loads(xbmc.executeJSONRPC(json.dumps(req))).get("result", {})


def get_dir(path):
    def fetch(p):
        return rpc("Files.GetDirectory", {"directory": p, "media": "files", "properties": ["art", "thumbnail"]}).get("files", []) or []
    files = fetch(path)
    # Elementum's top folders (/movies/, /shows/) only answer WITH the slash, the ones inside only WITHOUT it.
    if not files and path.startswith("plugin://") and "?" not in path and not path.endswith("/"):
        files = fetch(path + "/")
    return files


def pick_hidden(labels, hidden):
    """Tick the items to hide. Returns the new hidden list, or None if cancelled."""
    current = set(h.lower() for h in hidden)
    pre = [i for i, l in enumerate(labels) if l.lower() in current]
    sel = dialog.multiselect("Tick the items to hide", labels, preselect=pre)
    if sel is None:
        return None
    # keep hidden names that aren't showing right now, so they stay hidden if they come back
    shown = set(l.lower() for l in labels)
    return [labels[i] for i in sel] + [h for h in hidden if h.lower() not in shown]


def strip_tags(text):
    return re.sub(r"\[/?(B|I|COLOR[^\]]*|UPPERCASE|LOWERCASE|CAPITALIZE|LIGHT)\]", "", text or "").strip()


def clean_path(path):
    # Elementum can't open its folders with a trailing slash, so drop it (but keep plugin roots).
    if path.startswith("plugin://") and "?" not in path and path.count("/") > 3:
        path = path.rstrip("/")
    return path


def clean_icon(art, thumbnail=""):
    icon = art.get("thumb") or art.get("icon") or art.get("poster") or thumbnail or ""
    if icon.startswith("image://"):
        icon = unquote(icon[8:]).rstrip("/")
    return icon


def pick_addon():
    addons = rpc("Addons.GetAddons", {"type": "xbmc.addon.video", "enabled": True, "properties": ["name"]}).get("addons", [])
    addons = [a for a in addons if a["addonid"] != "plugin.video.mylists"]
    addons.sort(key=lambda a: strip_tags(a["name"]).lower())
    choices = ["Enter path manually"] + [strip_tags(a["name"]) for a in addons]
    choice = dialog.select("Add entry: choose an addon", choices)
    if choice < 0:
        return None
    if choice == 0:
        path = dialog.input("Path").strip()
        if not path:
            return None
        label = dialog.input("Label").strip() or path
        return {"label": label, "path": clean_path(path), "icon": "", "all": False, "hide": []}
    addon = addons[choice - 1]
    return browse("plugin://%s/" % addon["addonid"], strip_tags(addon["name"]), "")


def browse(path, label, icon):
    """Walk an addon's folders. Returns the chosen folder as an entry, or None."""
    trail = [(path, label, icon)]
    while trail:
        cur_path, cur_label, cur_icon = trail[-1]
        progress = xbmcgui.DialogProgressBG()
        progress.create(TITLE, "Loading %s" % cur_label)
        try:
            files = get_dir(cur_path)
        finally:
            progress.close()
        folders = [f for f in files if f.get("filetype") == "directory"]
        choices, actions = [], []
        if len(trail) > 1:
            choices.append("[B]Add this list: %s[/B]" % cur_label)
            actions.append("one")
        if files:
            choices.append("[B]Add everything in %s, then pick what to hide[/B]" % cur_label)
            actions.append("all")
        choices.append("..")
        actions.append("up")
        for f in folders:
            choices.append(strip_tags(f["label"]))
            actions.append(f)
        choice = dialog.select(cur_label, choices)
        if choice < 0:
            return None
        act = actions[choice]
        if act == "one":
            return {"label": cur_label, "path": clean_path(cur_path), "icon": cur_icon, "all": False, "hide": []}
        if act == "all":
            hide = pick_hidden([strip_tags(f["label"]) for f in files], [])
            if hide is None:
                continue
            return {"label": cur_label, "path": clean_path(cur_path), "icon": cur_icon, "all": True, "hide": hide}
        if act == "up":
            trail.pop()
            continue
        trail.append((act["file"], strip_tags(act["label"]), clean_icon(act.get("art", {}), act.get("thumbnail", ""))))
    return None


# ---------- Manage menu ----------

def manage():
    while True:
        names = all_list_names()
        choices = ["%s  (%d entries)" % (list_title(n), len(read_entries(n))) for n in names]
        choices.append("[B]New list[/B]")
        choice = dialog.select("%s: choose a list" % TITLE, choices)
        if choice < 0:
            return
        if choice == len(names):
            new = clean_name(dialog.input("Name for the new list").strip())
            if not new:
                continue
            if new in names:
                dialog.ok(TITLE, "A list called %s already exists." % list_title(new))
                continue
            write_entries(new, [])
            manage_list(new)
        else:
            manage_list(names[choice])


def manage_list(name):
    changed = False
    while True:
        entries = read_entries(name)
        choices = [("%d. Everything in %s  (%d hidden)" % (i + 1, e["label"], len(e["hide"])) if e["all"]
                    else "%d. %s" % (i + 1, e["label"])) for i, e in enumerate(entries)]
        choices += ["[B]Add entry[/B]", "Show widget path"]
        if name:
            choices += ["Rename this list", "Delete this list"]
        choice = dialog.select("%s list" % list_title(name), choices)
        if choice < 0:
            break
        n = len(entries)
        if choice < n:
            if edit_entry(name, entries, choice):
                changed = True
        elif choice == n:
            entry = pick_addon()
            if entry:
                entries.append(entry)
                write_entries(name, entries)
                changed = True
        elif choice == n + 1:
            dialog.ok(TITLE, "Use this path for the widget:[CR][CR][B]%s[/B]" % widget_path(name))
        elif choice == n + 2:
            new = clean_name(dialog.input("New name for the list", defaultt=list_title(name)).strip())
            if not new or new == name:
                continue
            if new in all_list_names():
                dialog.ok(TITLE, "A list called %s already exists." % list_title(new))
                continue
            write_entries(new, entries)  # writes the header with the new widget path
            os.remove(list_file(name))
            name = new
            changed = True
            dialog.ok(TITLE, "Renamed. Any widget using this list needs the new path:[CR][CR][B]%s[/B]" % widget_path(name))
        elif dialog.yesno(TITLE, "Delete the %s list?" % list_title(name)):
            os.remove(list_file(name))
            changed = True
            break
    if changed:
        xbmcgui.Dialog().notification(TITLE, "Saved. Restart Kodi if a widget doesn't update.", xbmcgui.NOTIFICATION_INFO, 4000)


def edit_entry(name, entries, i):
    e = entries[i]
    actions = ["Rename", "Move up", "Move down", "Remove"]
    if e["all"]:
        actions.insert(0, "Choose hidden items")
    choice = dialog.select(e["label"], actions)
    if choice < 0:
        return False
    act = actions[choice]
    if act == "Choose hidden items":
        files = get_dir(e["path"])
        if not files:
            dialog.ok(TITLE, "Couldn't load %s. Make sure the add-on is running, then try again." % e["label"])
            return False
        hide = pick_hidden([strip_tags(f["label"]) for f in files], e["hide"])
        if hide is None:
            return False
        e["hide"] = hide
    elif act == "Rename":
        label = dialog.input("Label", defaultt=e["label"])
        if label == "" or label == e["label"]:
            return False
        e["label"] = label  # a single space is allowed, for a tile with no text
    elif act == "Move up" and i > 0:
        entries[i - 1], entries[i] = entries[i], entries[i - 1]
    elif act == "Move down" and i < len(entries) - 1:
        entries[i + 1], entries[i] = entries[i], entries[i + 1]
    elif act == "Remove" and dialog.yesno(TITLE, "Remove %s?" % e["label"]):
        entries.pop(i)
    else:
        return False
    write_entries(name, entries)
    return True


# ---------- entry point ----------

if __name__ == "__main__":
    seed_data_dir()
    params = dict(parse_qsl(sys.argv[2].lstrip("?"))) if len(sys.argv) > 2 else {}
    if params.get("mode") == "manage":
        manage()
    else:
        show_list(int(sys.argv[1]), clean_name(params.get("list", "")))
