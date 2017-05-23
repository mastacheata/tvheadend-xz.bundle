from tvheadend import htsp

TITLE = "XZ"
PREFIX = "/video/tvheadend-xz"

ART = 'art-default.jpg'
ICON = 'tvheadend.png'
ICON_LIVE = "televisions.png"
ICON_REC = "rec.png"


def Start():
    ObjectContainer.art = R(ART)
    HTTP.CacheTime = 1
    Log.Debug("XZ start")


@handler(PREFIX, TITLE, ICON, ART)
def main_menu():
    main = ObjectContainer()
    main.title1 = "XZ"
    main.no_cache = True
    main.header = None
    main.message = None
    main.add(DirectoryObject(
        key=Callback(epg_menu),
        title="EPG / Live TV",
        thumb=R(ICON_LIVE),
    ))
    main.add(DirectoryObject(
        key=Callback(dvr_menu),
        title="Rec Timers",
        thumb=R(ICON_REC),
    ))
    return main


def epg_menu():
    epg = ObjectContainer(
    )
    return epg


def dvr_menu():
    dvr = ObjectContainer(
    )
    return dvr


def ValidatePrefs():
    if not Prefs["tvheadend-url"]:
        Log.Error("Please specify a URL to TVheadend in the settings")
        return False
    if not Prefs["tvheadend-http-port"]:
        Log.Error("Please specify the TVheadend HTTP port in the settings")
        return False
    if not Prefs["tvheadend-login"]:
        Log.Error("Please specify your TVheadend username in the settings")
        return False
    if not Prefs["tvheadend-password"]:
        Log.Error("Please specify your TVheadend password in the settings")
        return False

    tvh = htsp.HTSPClient(Prefs["tvheadend-url"], int(Prefs["tvheadend-http-port"])+1)
    tvh.hello()
    # tvh = tvheadend.HTSPClient(Prefs["tvheadend-url"], int(Prefs["tvheadend-http-port"])+1)
    # tvh.hello()
    # tvh.authenticate(Prefs["tvheadend-login"], Prefs["tvheadend-password"])
    # error = tvh.recv()
    # if 'noaccess' in error:
    #     Log.Error("Bad credentials used to log in at HTSP API of TVheadend")
    #     return False
    return True