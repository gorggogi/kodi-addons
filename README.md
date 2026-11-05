# gorggogi Kodi add-ons

Kodi add-ons by gorggogi, installed and updated through the gorggogi Repository. All of them need Kodi 19 or newer.

- Quality Check warns you if a video's real resolution is below 1080p, or if its bitrate is low for its resolution.
- My Lists shows only the add-on lists you choose, so a home screen widget can show just those.

## Install

1. In Kodi, go to Settings > System > Add-ons and turn on Unknown sources.
2. Go to Settings > File manager > Add source and enter `https://gorggogi.github.io/kodi-addons/`. Name it `gorggogi`.
3. Go to Add-ons, click the open box icon, and choose Install from zip file > gorggogi.
4. Select the `repository.gorggogi` zip.
5. Choose Install from repository > gorggogi Repository, then install the add-ons you want. Quality Check is under Services and My Lists is under Video add-ons.

## Update

Change the add-on, raise its version in `addon.xml`, run `python build.py`, then commit and push.

## Quality Check

A small add-on that warns you if a video's real resolution is below 1080p, or if its bitrate is low for its resolution, so you can spot results with a wrong quality label. It stays quiet otherwise, unless you set it to always show the resolution and bitrate.

### Timing

The notification shows as soon as Kodi reports the resolution, usually within a second of the picture appearing. If the stream steps up from a low resolution or the bitrate only arrives later, a second notification follows within 6 seconds.

### Limits

The bitrate comes from what Kodi reports, or from file size and running time if Kodi doesn't report one. If neither is available, there's no bitrate warning. The warning is a clue, not proof:

- A cinema recording or an upscale at a normal bitrate still passes.
- A simple, clean video can be flagged even though it looks fine.

### Settings

Go to Add-ons > My add-ons > Services > Quality Check > Configure. Changes apply to the next video you play.

- Warn when resolution is low. On by default.
- Lowest resolution. 1080p by default. Choose 720p to only warn below 720p.
- Warn when bitrate is low. On by default.
- Warning levels. 1.5 Mbps for 720p, 2.5 Mbps for 1080p and 8 Mbps for 4K by default. Set one to 0 to skip the bitrate check for that resolution.
- Lower levels for HEVC, AV1 and VP9. On by default. Lowers the warning levels by 40% for these codecs.
- Show. Warnings only by default, which stays quiet when a video is fine. Always shows the resolution and bitrate of every video, with a warning when it's low.
- Show notification for. 7 seconds by default.

## My Lists

My Lists lists only the add-on folders you pick, like Elementum's Trending and Popular movies. Point a FENtastic stacked widget at it, and the widget shows buttons for just those lists, with posters under the one you highlight. This also works for Elementum lists, which can't be used in library nodes.

### Set it up

1. Go to Add-ons > My add-ons > Video add-ons > My Lists > Configure > Manage lists.
2. Choose a list, or New list to make another one.
3. Choose Add entry, pick an add-on and browse to the list you want. Inside it, choose Add this list.
4. In FENtastic, set up the widget and browse to My Lists. Choose Use My Lists as path for the Main list, or open My Lists: NAME and choose Use NAME as path for another list. Show widget path gives the path to type in instead.

Select an entry to rename it, move it or remove it. Rename this list and Delete this list are at the bottom of each list except Main. A label of a single space gives a tile with no text.

To show a whole folder minus a few items, browse to it and choose Add everything in it, then tick the items to hide. Select that entry later and choose Choose hidden items to change them.

### Where the lists are kept

Lists are saved in `userdata/addon_data/plugin.video.mylists/`, one text file per list, so updates don't touch them. On the first run, the starter lists that come with the add-on are copied there.

### Limits

- Don't put a search entry in a stacked widget. The poster row opens whatever is highlighted, so it would start the search on its own. Use a plain widget for a search button.
- If a widget doesn't show a change, restart Kodi.
