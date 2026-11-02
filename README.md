# Kodi Quality Check

A small Kodi add-on that warns you if a video's real resolution is below 1080p, or if its bitrate is low for its resolution, so you can spot results with a wrong quality label. It stays quiet otherwise.

Requires Kodi 19 or newer.

## Install

1. In Kodi, go to Settings > System > Add-ons and turn on Unknown sources.
2. Go to Settings > File manager > Add source and enter `https://gorggogi.github.io/kodi-quality-check/`. Name it `gorggogi`.
3. Go to Add-ons, click the open box icon, and choose Install from zip file > gorggogi.
4. Select the `repository.gorggogi` zip.
5. Choose Install from repository > gorggogi Repository > Services > Quality Check > Install.

## Update

Change the add-on, raise its version in `addon.xml`, run `python build.py`, then commit and push.

## Limits

The bitrate comes from what Kodi reports, or from file size and running time if Kodi doesn't report one. If neither is available, there's no bitrate warning. The warning is a clue, not proof:

- A cinema recording or an upscale at a normal bitrate still passes.
- A simple, clean video can be flagged even though it looks fine.

Warning levels are 2.5 Mbps for 1080p and 8 Mbps for 4K. They're lowered by 40% for HEVC, AV1 and VP9.
