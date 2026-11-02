import json

import xbmc
import xbmcgui
import xbmcvfs

CHECK_SECONDS = 1
MAX_CHECKS = 5
SHOW_MS = 7000
GOOD_TIERS = ('1080p', '4K')

# Bitrate below which a video of this tier is likely to look soft.
LOW_MBPS = {'4K': 8.0, '1080p': 2.5}
# These codecs look the same at a lower bitrate than H264.
EFFICIENT_CODECS = ('hevc', 'h265', 'hvc1', 'av1', 'vp9')
EFFICIENT_FACTOR = 0.6
# A smaller result means the size wasn't the video's, so the bitrate stays unknown.
MIN_BELIEVABLE_MBPS = 0.1


def tier(width, height):
    # Width decides the tier, because widescreen movies have a reduced height.
    if width >= 3200 or height >= 1800:
        return '4K'
    if width >= 1800 or height >= 1000:
        return '1080p'
    if width >= 1200 or height >= 680:
        return '720p'
    return 'SD'


def video_stream():
    request = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'Player.GetProperties',
        'params': {'playerid': 1, 'properties': ['currentvideostream']},
    }
    try:
        reply = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
        stream = reply['result']['currentvideostream']
        width = int(stream.get('width') or 0)
        height = int(stream.get('height') or 0)
        return width, height, str(stream.get('codec') or '').lower()
    except Exception as error:
        xbmc.log('[Quality Check] could not read stream: %s' % error, xbmc.LOGWARNING)
        return 0, 0, ''


def reported_mbps():
    """Reads the bitrate Kodi reports, given in kilobits per second."""
    raw = xbmc.getInfoLabel('VideoPlayer.VideoBitrate')
    return int(raw) / 1000.0 if raw.isdigit() else 0.0


def file_mbps(player):
    """Works out the bitrate from file size and running time, audio included."""
    try:
        seconds = player.getTotalTime()
        video_file = xbmcvfs.File(player.getPlayingFile())
        try:
            size = video_file.size()
        finally:
            video_file.close()
    except Exception as error:
        xbmc.log('[Quality Check] could not read size: %s' % error, xbmc.LOGWARNING)
        return 0.0
    if seconds <= 0 or size <= 0:
        return 0.0
    mbps = size * 8 / seconds / 1000000.0
    return mbps if mbps >= MIN_BELIEVABLE_MBPS else 0.0


def is_low_bitrate(quality, mbps, codec):
    limit = LOW_MBPS.get(quality)
    if limit is None or not mbps:
        return False
    if any(name in codec for name in EFFICIENT_CODECS):
        limit *= EFFICIENT_FACTOR
    return mbps < limit


class Watcher(xbmc.Player):
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor

    def warn(self, heading, message):
        xbmcgui.Dialog().notification(heading, message, xbmcgui.NOTIFICATION_WARNING, SHOW_MS)
        xbmc.log('[Quality Check] %s %s' % (heading, message), xbmc.LOGINFO)

    def read_mbps(self):
        # Kodi can take a moment to report the bitrate after playback starts.
        for _ in range(MAX_CHECKS):
            mbps = reported_mbps()
            if mbps:
                return mbps
            if self.monitor.waitForAbort(CHECK_SECONDS) or not self.isPlayingVideo():
                return 0.0
        return file_mbps(self)

    def check_bitrate(self, width, height, codec):
        mbps = self.read_mbps()
        if is_low_bitrate(tier(width, height), mbps, codec):
            self.warn('Low bitrate: %.1f Mbps' % mbps, '%dx%d, may look soft' % (width, height))
            return
        rate = '%.1f Mbps' % mbps if mbps else 'bitrate unknown'
        xbmc.log('[Quality Check] OK %dx%d %s %s' % (width, height, codec, rate), xbmc.LOGINFO)

    def onAVStarted(self):
        if not self.isPlayingVideo():
            return
        width = height = 0
        # Streams can start low and step up, so only warn if it stays low.
        for _ in range(MAX_CHECKS):
            if self.monitor.waitForAbort(CHECK_SECONDS) or not self.isPlayingVideo():
                return
            read_width, read_height, codec = video_stream()
            if read_width:
                width, height = read_width, read_height
                if tier(width, height) in GOOD_TIERS:
                    self.check_bitrate(width, height, codec)
                    return
        if width:
            self.warn('Low quality: ' + tier(width, height), '%dx%d' % (width, height))


if __name__ == '__main__':
    monitor = xbmc.Monitor()
    watcher = Watcher(monitor)
    monitor.waitForAbort()
