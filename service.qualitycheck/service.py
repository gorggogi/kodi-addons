import json

import xbmc
import xbmcgui

DELAY_MS = 5000
SHOW_MS = 7000


def tier(width, height):
    # Width decides the tier, because widescreen movies have a reduced height.
    if width >= 3200 or height >= 1800:
        return '4K'
    if width >= 1800 or height >= 1000:
        return '1080p'
    if width >= 1200 or height >= 680:
        return '720p'
    return 'SD'


def video_size():
    request = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'Player.GetProperties',
        'params': {'playerid': 1, 'properties': ['currentvideostream']},
    }
    try:
        reply = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
        stream = reply['result']['currentvideostream']
        return int(stream.get('width') or 0), int(stream.get('height') or 0)
    except Exception as error:
        xbmc.log('[Quality Check] could not read stream: %s' % error, xbmc.LOGWARNING)
        return 0, 0


def bitrate_text():
    raw = xbmc.getInfoLabel('Player.Process(videobitrate)') or xbmc.getInfoLabel('VideoPlayer.VideoBitrate')
    digits = ''.join(ch for ch in raw if ch.isdigit())
    if not digits:
        return ''
    # Kodi reports this value in kilobits per second.
    return '%.1f Mbps' % (int(digits) / 1000.0)


class Watcher(xbmc.Player):
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor

    def onAVStarted(self):
        if not self.isPlayingVideo():
            return
        if self.monitor.waitForAbort(DELAY_MS / 1000.0) or not self.isPlayingVideo():
            return
        width, height = video_size()
        if not width:
            return
        message = '%dx%d' % (width, height)
        rate = bitrate_text()
        if rate:
            message += ' at ' + rate
        heading = 'Real quality: ' + tier(width, height)
        xbmcgui.Dialog().notification(heading, message, xbmcgui.NOTIFICATION_INFO, SHOW_MS)
        xbmc.log('[Quality Check] %s %s' % (heading, message), xbmc.LOGINFO)


if __name__ == '__main__':
    monitor = xbmc.Monitor()
    watcher = Watcher(monitor)
    monitor.waitForAbort()
