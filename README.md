# Kodi Quality Check

A small Kodi add-on that shows the real resolution of a video a few seconds after it starts playing, so you can spot results with a wrong quality label.

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

The add-on reads the size of the video stream, so it can't detect a low-quality video that was upscaled. A low bitrate is the clue for those.
