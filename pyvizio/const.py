"""pyvizio constants."""

DEVICE_CLASS_SPEAKER = "speaker"
DEVICE_CLASS_TV = "tv"

DEFAULT_DEVICE_ID = "pyvizio"
DEFAULT_DEVICE_CLASS = DEVICE_CLASS_TV
DEFAULT_DEVICE_NAME = "Python Vizio"
DEFAULT_PORTS = [7345, 9000]
DEFAULT_TIMEOUT = 5

MAX_VOLUME = {DEVICE_CLASS_TV: 100, DEVICE_CLASS_SPEAKER: 31}

# Current Input when app is active
INPUT_APPS = ["SMARTCAST", "CAST"]

# App name returned when it is not in app dictionary
UNKNOWN_APP = "_UNKNOWN_APP"
NO_APP_RUNNING = "_NO_APP_RUNNING"
SMARTCAST_HOME = "SmartCast Home"

APP_CAST = "Cast"

# NAME_SPACE values that appear to be equivalent
EQUIVALENT_NAME_SPACES = (2, 4)

APP_HOME = {
    "name": SMARTCAST_HOME,
    "country": ["*"],
    "config": [
        {
            "NAME_SPACE": 4,
            "APP_ID": "1",
            "MESSAGE": "http://127.0.0.1:12345/scfs/sctv/main.html",
        }
    ],
}

# No longer needed but kept around in case the external source for APPS is unavailable
APPS = [
    {
        "name": "Prime Video",
        "country": ["*"],
        "id": ["33"],
        "config": [
            {
                "APP_ID": "4",
                "NAME_SPACE": 4,
                "MESSAGE": "https://atv-ext.amazon.com/blast-app-hosting/html5/index.html?deviceTypeID=A3OI4IHTNZQWDD",
            },
            {"NAME_SPACE": 2, "APP_ID": "4", "MESSAGE": "None"},
        ],
    },
    {
        "name": "CBS All Access",
        "country": ["usa"],
        "id": ["9"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "37", "MESSAGE": "None"}],
    },
    {
        "name": "CBS News",
        "country": ["usa", "can"],
        "id": ["56"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "42", "MESSAGE": "None"}],
    },
    {
        "name": "Crackle",
        "country": ["usa"],
        "id": ["8"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "5", "MESSAGE": "None"}],
    },
    {
        "name": "Curiosity Stream",
        "country": ["usa", "can"],
        "id": ["37"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "12", "MESSAGE": "None"}],
    },
    {
        "name": "Fandango Now",
        "country": ["usa"],
        "id": ["24"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "7", "MESSAGE": "None"}],
    },
    {
        "name": "FilmRise",
        "country": ["usa"],
        "id": ["47"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "24", "MESSAGE": "None"}],
    },
    {
        "name": "Flixfling",
        "country": ["*"],
        "id": ["49"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "36", "MESSAGE": "None"}],
    },
    {
        "name": "Haystack TV",
        "country": ["usa", "can"],
        "id": ["35"],
        "config": [
            {
                "NAME_SPACE": 0,
                "APP_ID": "898AF734",
                "MESSAGE": '{"CAST_NAMESPACE":"urn:x-cast:com.google.cast.media","CAST_MESSAGE":{"type":"LOAD","media":{},"autoplay":true,"currentTime":0,"customData":{"platform":"sctv"}}}',
            }
        ],
    },
    {
        "name": "Hulu",
        "country": ["usa"],
        "id": ["19"],
        "config": [
            {
                "APP_ID": "3",
                "NAME_SPACE": 4,
                "MESSAGE": "https://viziosmartcast.app.hulu.com/livingroom/viziosmartcast/1/index.html#initialize",
            },
            {"NAME_SPACE": 2, "APP_ID": "3", "MESSAGE": "None"},
        ],
    },
    {
        "name": "iHeartRadio",
        "country": ["usa"],
        "id": ["11"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "6", "MESSAGE": "None"}],
    },
    {
        "name": "NBC",
        "country": ["usa"],
        "id": ["43"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "10", "MESSAGE": "None"}],
    },
    {
        "name": "Netflix",
        "country": ["*"],
        "id": ["34"],
        "config": [{"NAME_SPACE": 3, "APP_ID": "1", "MESSAGE": "None"}],
    },
    {
        "name": "Plex",
        "country": ["usa", "can"],
        "id": ["40"],
        "config": [
            {
                "APP_ID": "9",
                "NAME_SPACE": 4,
                "MESSAGE": "https://plex.tv/web/tv/vizio-smartcast",
            },
            {"NAME_SPACE": 2, "APP_ID": "9", "MESSAGE": "None"},
        ],
    },
    {
        "name": "Pluto TV",
        "country": ["usa"],
        "id": ["12"],
        "config": [
            {"APP_ID": "65", "NAME_SPACE": 4, "MESSAGE": "https://smartcast.pluto.tv"},
            {
                "NAME_SPACE": 0,
                "APP_ID": "E6F74C01",
                "MESSAGE": '{"CAST_NAMESPACE":"urn:x-cast:tv.pluto","CAST_MESSAGE":{"command":"initializePlayback","channel":"","episode":"","time":0}}',
            },
        ],
    },
    {
        "name": "RedBox",
        "country": ["usa"],
        "id": ["55"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "41", "MESSAGE": "None"}],
    },
    {
        "name": "TasteIt",
        "country": ["*"],
        "id": ["52"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "26", "MESSAGE": "None"}],
    },
    {
        "name": "Toon Goggles",
        "country": ["usa", "can"],
        "id": ["46"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "21", "MESSAGE": "None"}],
    },
    {
        "name": "Vudu",
        "country": ["usa"],
        "id": ["6"],
        "config": [
            {
                "APP_ID": "31",
                "NAME_SPACE": 4,
                "MESSAGE": "https://my.vudu.com/castReceiver/index.html?launch-source=app-icon",
            }
        ],
    },
    {
        "name": "XUMO",
        "country": ["usa"],
        "id": ["27"],
        "config": [
            {
                "NAME_SPACE": 0,
                "APP_ID": "36E1EA1F",
                "MESSAGE": '{"CAST_NAMESPACE":"urn:x-cast:com.google.cast.media","CAST_MESSAGE":{"type":"LOAD","media":{},"autoplay":true,"currentTime":0,"customData":{}}}',
            }
        ],
    },
    {
        "name": "YouTubeTV",
        "country": ["usa", "mexico"],
        "id": ["45"],
        "config": [{"NAME_SPACE": 5, "APP_ID": "3", "MESSAGE": "None"}],
    },
    {
        "name": "YouTube",
        "country": ["*"],
        "id": ["44"],
        "config": [{"NAME_SPACE": 5, "APP_ID": "1", "MESSAGE": "None"}],
    },
    {
        "name": "Baeble",
        "country": ["usa"],
        "id": ["39"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "11", "MESSAGE": "None"}],
    },
    {
        "name": "DAZN",
        "country": ["usa", "can"],
        "id": ["57"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "34", "MESSAGE": "None"}],
    },
    {
        "name": "FitFusion by Jillian Michaels",
        "country": ["usa", "can"],
        "id": ["54"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "39", "MESSAGE": "None"}],
    },
    {
        "name": "Newsy",
        "country": ["usa", "can"],
        "id": ["38"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "15", "MESSAGE": "None"}],
    },
    {
        "name": "Cocoro TV",
        "country": ["usa", "can"],
        "id": ["63"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "55", "MESSAGE": "None"}],
    },
    {
        "name": "ConTV",
        "country": ["usa", "can"],
        "id": ["41"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "18", "MESSAGE": "None"}],
    },
    {
        "name": "Dove Channel",
        "country": ["usa", "can"],
        "id": ["42"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "16", "MESSAGE": "None"}],
    },
    {
        "name": "Love Destination",
        "country": ["*"],
        "id": ["64"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "57", "MESSAGE": "None"}],
    },
    {
        "name": "WatchFree",
        "country": ["usa"],
        "id": ["48"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "22", "MESSAGE": "None"}],
    },
    {
        "name": "AsianCrush",
        "country": ["usa", "can"],
        "id": ["50"],
        "config": [
            {
                "NAME_SPACE": 2,
                "APP_ID": "27",
                "MESSAGE": "https://html5.asiancrush.com/?ua=viziosmartcast",
            }
        ],
    },
    {
        "name": "Disney+",
        "country": ["usa"],
        "id": ["51"],
        "config": [
            {
                "NAME_SPACE": 4,
                "APP_ID": "75",
                "MESSAGE": "https://cd-dmgz.bamgrid.com/bbd/vizio_tv/index.html",
            }
        ],
    },
]
