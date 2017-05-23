import htsp

TITLE = 'XZ'
PREFIX = '/video/xz'

ART = 'art-default.jpg'
ICON = 'tvheadend.png'
ICON_LIVE = 'televisions.png'
ICON_REC = 'rec.png'

tvh = None


def Start():
    ObjectContainer.art = R(ART)
    HTTP.CacheTime = 1
    Log.Debug('XZ start')
    global tvh
    tvh = TVheadend()
    ValidatePrefs()


@route(PREFIX + '/validate')
def ValidatePrefs():
    if not Prefs['tvheadend-url']:
        Log.Error('Please specify a URL to TVheadend in the settings')
        return False

    if not Prefs['tvheadend-http-port']:
        Log.Error('Please specify the TVheadend HTTP port in the settings')
        return False

    if not Prefs['tvheadend-login']:
        Log.Warning('Please specify your TVheadend username in the settings')
        login = ''
        # return False
    else:
        login = Prefs['tvheadend-login']

    if not Prefs['tvheadend-password']:
        Log.Warning('Please specify your TVheadend password in the settings')
        password = ''
        # return False
    else:
        password = Prefs['tvheadend-password']

    global tvh
    tvh.connect(Prefs['tvheadend-url'], int(Prefs['tvheadend-http-port'])+1)

    return tvh.login(login, password)


@handler(PREFIX, TITLE, ICON, ART)
def main_menu():
    main = ObjectContainer()
    main.title1 = 'XZ'
    main.no_cache = True
    main.header = None
    main.message = None
    main.add(DirectoryObject(
        key=Callback(epg_menu),
        title='EPG / Live TV',
        thumb=R(ICON_LIVE),
    ))
    main.add(DirectoryObject(
        key=Callback(dvr_menu),
        title='Rec Timers',
        thumb=R(ICON_REC),
    ))
    return main


@route(PREFIX + '/live')
def epg_menu():
    global tvh
    tvh.get_channel_list()
    epg = ObjectContainer(
    )
    return epg


@route(PREFIX + '/rec')
def dvr_menu():
    dvr = ObjectContainer(
    )
    return dvr


class TVheadend:

    tvh = None
    channels = {}
    channelNumbers = []

    def __init__(self):
        pass

    def connect(self, host, port):
        address = (host, port)
        self.tvh = htsp.HTSPClient(address, 'TVheadend Plex Client')

    def login(self, login, password):
        self.tvh.hello()
        response = self.tvh.authenticate(login, password)
        if 'noaccess' in response:
            Log.Error('Authentication with TVheadend server failed')
            return False
        else:
            return True

    def get_channel_list(self):
        self.tvh.send('enableAsyncMetadata')
        while True:
            msg = self.tvh.recv()
            if 'error' in msg:
                Log.Error(msg['error'])
                raise Exception(msg['Error'])
            elif 'method' in msg:
                Log.Info(msg)
                return msg['method']

