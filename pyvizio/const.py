"""pyvizio constants."""

DEVICE_CLASS_SPEAKER = "speaker"
DEVICE_CLASS_TV = "tv"
DEVICE_CLASS_CRAVE360 = "crave360"

DEFAULT_DEVICE_ID = "pyvizio"
DEFAULT_DEVICE_CLASS = DEVICE_CLASS_TV
DEFAULT_DEVICE_NAME = "Python Vizio"
DEFAULT_PORTS = [7345, 9000]
DEFAULT_TIMEOUT = 5

MAX_VOLUME = {
    DEVICE_CLASS_TV: 100,
    DEVICE_CLASS_SPEAKER: 31,
    DEVICE_CLASS_CRAVE360: 100,
}

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
        "name": "A&E Crime Central",
        "country": ["usa"],
        "id": ["162"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "162", "MESSAGE": None}],
    },
    {
        "name": "AMC+",
        "country": ["usa"],
        "id": ["2218"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "218", "MESSAGE": None}],
    },
    {
        "name": "Acorn TV",
        "country": ["usa"],
        "id": ["97"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "74", "MESSAGE": None}],
    },
    {
        "name": "Adventure 2 Learning",
        "country": ["usa"],
        "id": ["106"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "83", "MESSAGE": None}],
    },
    {
        "name": "Adventure Sports Network",
        "country": ["usa", "can"],
        "id": ["244"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "44", "MESSAGE": None}],
    },
    {
        "name": "AfrolandTV",
        "country": ["usa", "can"],
        "id": ["144"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "144", "MESSAGE": None}],
    },
    {
        "name": "Amazon Music",
        "country": ["usa", "can"],
        "id": ["156"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "156", "MESSAGE": None}],
    },
    {
        "name": "Annoying Orange",
        "country": ["usa", "can"],
        "id": ["172"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "172", "MESSAGE": None}],
    },
    {
        "name": "Apple TV+",
        "country": ["usa"],
        "id": ["91"],
        "config": [{"NAME_SPACE": 3, "APP_ID": "4", "MESSAGE": None}],
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
        "name": "BET+",
        "country": ["usa"],
        "id": ["126"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "121", "MESSAGE": None}],
    },
    {
        "name": "BRB Travel & Food",
        "country": ["usa"],
        "id": ["207"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "207", "MESSAGE": None}],
    },
    {
        "name": "Baby Einstein",
        "country": ["usa", "can"],
        "id": ["175"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "175", "MESSAGE": None}],
    },
    {
        "name": "Beani.TV",
        "country": ["usa", "can"],
        "id": ["152"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "152", "MESSAGE": None}],
    },
    {
        "name": "Best of Roblox",
        "country": ["usa"],
        "id": ["208"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "208", "MESSAGE": None}],
    },
    {
        "name": "Blackdove",
        "country": ["usa", "can"],
        "id": ["71"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "66", "MESSAGE": None}],
    },
    {
        "name": "Bob Ross",
        "country": ["usa"],
        "id": ["120"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "106", "MESSAGE": None}],
    },
    {
        "name": "Bon App\u00e9tit",
        "country": ["usa", "can"],
        "id": ["158"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "158", "MESSAGE": None}],
    },
    {
        "name": "Boondock Nation",
        "country": ["usa", "can"],
        "id": ["136"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "136", "MESSAGE": None}],
    },
    {
        "name": "Brooke Burke Body",
        "country": ["usa", "can", "mex"],
        "id": ["114"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "118", "MESSAGE": None}],
    },
    {
        "name": "Brown Sugar",
        "country": ["usa"],
        "id": ["84"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "69", "MESSAGE": None}],
    },
    {
        "name": "CBS News",
        "country": ["usa", "can"],
        "id": ["56"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "42", "MESSAGE": None}],
    },
    {
        "name": "CBS Sports",
        "country": ["usa"],
        "id": ["109"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "112", "MESSAGE": None}],
    },
    {
        "name": "Canela.TV",
        "country": ["usa"],
        "id": ["113"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "119", "MESSAGE": None}],
    },
    {
        "name": "Chicken Soup For The Soul",
        "country": ["usa"],
        "id": ["168"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "168", "MESSAGE": None}],
    },
    {
        "name": "Christmas Plus",
        "country": ["usa"],
        "id": ["2228"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "228", "MESSAGE": None}],
    },
    {
        "name": "Cinehouse",
        "country": ["usa", "can"],
        "id": ["80"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "29", "MESSAGE": None}],
    },
    {
        "name": "CoCoMelon",
        "country": ["usa", "can"],
        "id": ["124"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "123", "MESSAGE": None}],
    },
    {
        "name": "Comedy Dynamics",
        "country": ["usa"],
        "id": ["276"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "76", "MESSAGE": None}],
    },
    {
        "name": "ConTV",
        "country": ["usa", "can"],
        "id": ["41"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "18", "MESSAGE": None}],
    },
    {
        "name": "Court TV",
        "country": ["usa"],
        "id": ["87"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "78", "MESSAGE": None}],
    },
    {
        "name": "Crackle",
        "country": ["usa"],
        "id": ["8"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "5", "MESSAGE": None}],
    },
    {
        "name": "Crime & Conspiracy",
        "country": ["usa", "can"],
        "id": ["133"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "133", "MESSAGE": None}],
    },
    {
        "name": "CuriosityStream",
        "country": ["usa", "can"],
        "id": ["37"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "12", "MESSAGE": None}],
    },
    {
        "name": "DAZN",
        "country": ["usa", "can"],
        "id": ["57"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "34", "MESSAGE": None}],
    },
    {
        "name": "Dan TDM",
        "country": ["usa"],
        "id": ["209"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "209", "MESSAGE": None}],
    },
    {
        "name": "Dark Matter TV",
        "country": ["usa"],
        "id": ["82"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "81", "MESSAGE": None}],
    },
    {
        "name": "Discovery Go",
        "country": ["usa"],
        "id": ["2222"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "222", "MESSAGE": None}],
    },
    {
        "name": "Disney+",
        "country": ["usa", "can", "mex"],
        "id": ["76"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "75", "MESSAGE": None}],
    },
    {
        "name": "Distro TV",
        "country": ["usa", "can"],
        "id": ["2178"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "178", "MESSAGE": None}],
    },
    {
        "name": "Docurama",
        "country": ["usa", "can"],
        "id": [None],
        "config": [{"NAME_SPACE": 2, "APP_ID": "137", "MESSAGE": None}],
    },
    {
        "name": "Dove Channel",
        "country": ["usa", "can"],
        "id": ["42"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "16", "MESSAGE": None}],
    },
    {
        "name": "ElectricNow",
        "country": ["usa", "can"],
        "id": ["290"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "90", "MESSAGE": None}],
    },
    {
        "name": "Estrella TV",
        "country": ["usa"],
        "id": ["165"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "165", "MESSAGE": None}],
    },
    {
        "name": "FOX NOW",
        "country": ["usa"],
        "id": ["110"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "109", "MESSAGE": None}],
    },
    {
        "name": "FOX Sports",
        "country": ["usa"],
        "id": ["2111"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "111", "MESSAGE": None}],
    },
    {
        "name": "FamilyTime",
        "country": ["usa", "can"],
        "id": ["2186"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "186", "MESSAGE": None}],
    },
    {
        "name": "Fandor",
        "country": ["usa", "can"],
        "id": ["2154"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "154", "MESSAGE": None}],
    },
    {
        "name": "Fawesome.tv",
        "country": ["usa"],
        "id": ["104"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "87", "MESSAGE": None}],
    },
    {
        "name": "FilmRise",
        "country": ["usa"],
        "id": ["47"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "24", "MESSAGE": None}],
    },
    {
        "name": "FitFusion",
        "country": ["usa", "can"],
        "id": ["54"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "39", "MESSAGE": None}],
    },
    {
        "name": "Fite TV",
        "country": ["usa", "can"],
        "id": ["83"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "82", "MESSAGE": None}],
    },
    {
        "name": "Flixfling",
        "country": ["*"],
        "id": ["49"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "36", "MESSAGE": None}],
    },
    {
        "name": "Food Network Go",
        "country": ["usa"],
        "id": ["2223"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "223", "MESSAGE": None}],
    },
    {
        "name": "Fox Nation",
        "country": ["usa"],
        "id": ["111"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "110", "MESSAGE": None}],
    },
    {
        "name": "Free Games by PlayWorks",
        "country": ["usa"],
        "id": ["101"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "104", "MESSAGE": None}],
    },
    {
        "name": "Free Movies+",
        "country": ["usa"],
        "id": ["2229"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "229", "MESSAGE": None}],
    },
    {
        "name": "Funimation",
        "country": ["usa", "can"],
        "id": ["59"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "59", "MESSAGE": None}],
    },
    {
        "name": "GoTraveler",
        "country": ["usa", "can"],
        "id": ["117"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "125", "MESSAGE": None}],
    },
    {
        "name": "Gravitas Movies",
        "country": ["usa"],
        "id": ["119"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "108", "MESSAGE": None}],
    },
    {
        "name": "HBO Max",
        "country": ["usa"],
        "id": ["128"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "128", "MESSAGE": None}],
    },
    {
        "name": "HGTV",
        "country": ["usa"],
        "id": ["2224"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "224", "MESSAGE": None}],
    },
    {
        "name": "Hallmark Movies Now",
        "country": ["usa"],
        "id": ["2203"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "203", "MESSAGE": None}],
    },
    {
        "name": "HappyKids.tv",
        "country": ["usa"],
        "id": ["103"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "85", "MESSAGE": None}],
    },
    {
        "name": "Haystack TV",
        "country": ["usa", "can"],
        "id": ["35"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "60", "MESSAGE": None}],
    },
    {
        "name": "Here TV",
        "country": ["usa", "can"],
        "id": ["188"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "188", "MESSAGE": None}],
    },
    {
        "name": "Hipstr",
        "country": ["usa", "can"],
        "id": ["153"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "153", "MESSAGE": None}],
    },
    {
        "name": "History Vault",
        "country": ["usa"],
        "id": ["160"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "160", "MESSAGE": None}],
    },
    {
        "name": "Hometalk TV",
        "country": ["usa"],
        "id": ["100"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "95", "MESSAGE": None}],
    },
    {
        "name": "Hulu",
        "country": ["usa"],
        "id": ["19"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "3", "MESSAGE": None}],
    },
    {
        "name": "Into The Outdoors",
        "country": ["usa"],
        "id": ["139"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "139", "MESSAGE": None}],
    },
    {
        "name": "Investigation Discovery (ID) Go",
        "country": ["usa"],
        "id": ["2225"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "225", "MESSAGE": None}],
    },
    {
        "name": "Journy",
        "country": ["usa", "can"],
        "id": ["2219"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "219", "MESSAGE": None}],
    },
    {
        "name": "KORTV",
        "country": ["usa", "can"],
        "id": ["157"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "157", "MESSAGE": None}],
    },
    {
        "name": "Kidoodle.tv",
        "country": ["usa", "can"],
        "id": ["92"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "92", "MESSAGE": None}],
    },
    {
        "name": "LEGO TV",
        "country": ["usa"],
        "id": ["123"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "122", "MESSAGE": None}],
    },
    {
        "name": "La Bocina Latina",
        "country": ["usa", "can"],
        "id": ["194"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "194", "MESSAGE": None}],
    },
    {
        "name": "Lava",
        "country": ["usa", "can"],
        "id": ["167"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "167", "MESSAGE": None}],
    },
    {
        "name": "Lifetime Movie Club",
        "country": ["usa"],
        "id": ["161"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "161", "MESSAGE": None}],
    },
    {
        "name": "Local Now",
        "country": ["usa"],
        "id": ["85"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "79", "MESSAGE": None}],
    },
    {
        "name": "Love Destination",
        "country": ["*"],
        "id": ["64"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "57", "MESSAGE": None}],
    },
    {
        "name": "Made It Myself TV",
        "country": ["usa", "can"],
        "id": ["2239"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "239", "MESSAGE": None}],
    },
    {
        "name": "MagellanTV",
        "country": ["usa", "can"],
        "id": ["74"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "67", "MESSAGE": None}],
    },
    {
        "name": "Midnight Pulp",
        "country": ["usa", "can"],
        "id": ["122"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "28", "MESSAGE": None}],
    },
    {
        "name": "Motorvision TV",
        "country": ["usa", "can"],
        "id": ["135"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "135", "MESSAGE": None}],
    },
    {
        "name": "Movies Anywhere",
        "country": ["usa"],
        "id": ["86"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "38", "MESSAGE": None}],
    },
    {
        "name": "MyOutdoorTV",
        "country": ["usa", "can"],
        "id": ["192"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "192", "MESSAGE": None}],
    },
    {
        "name": "NBC",
        "country": ["usa"],
        "id": ["43"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "10", "MESSAGE": None}],
    },
    {
        "name": "Netflix",
        "country": ["*"],
        "id": ["34"],
        "config": [{"NAME_SPACE": 3, "APP_ID": "1", "MESSAGE": None}],
    },
    {
        "name": "Newsy",
        "country": ["usa", "can"],
        "id": ["38"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "15", "MESSAGE": None}],
    },
    {
        "name": "Ninja Kidz TV",
        "country": ["usa"],
        "id": ["115"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "93", "MESSAGE": None}],
    },
    {
        "name": "Nosey",
        "country": ["usa", "can"],
        "id": ["179"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "179", "MESSAGE": None}],
    },
    {
        "name": "Novocomedy",
        "country": ["usa", "can"],
        "id": ["166"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "166", "MESSAGE": None}],
    },
    {
        "name": "Outdoor America",
        "country": ["usa", "can"],
        "id": ["170"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "170", "MESSAGE": None}],
    },
    {
        "name": "Outside TV",
        "country": ["usa", "can"],
        "id": ["163"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "163", "MESSAGE": None}],
    },
    {
        "name": "PBS",
        "country": ["usa"],
        "id": ["129"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "129", "MESSAGE": None}],
    },
    {
        "name": "PBS Kids",
        "country": ["usa"],
        "id": ["112"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "117", "MESSAGE": None}],
    },
    {
        "name": "Pandora",
        "country": ["usa"],
        "id": ["70"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "58", "MESSAGE": None}],
    },
    {
        "name": "Paramount+",
        "country": ["usa"],
        "id": ["9"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "37", "MESSAGE": None}],
    },
    {
        "name": "Party Tyme Karaoke",
        "country": ["usa", "can"],
        "id": ["77"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "70", "MESSAGE": None}],
    },
    {
        "name": "Passionflix",
        "country": ["usa", "can"],
        "id": ["176"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "176", "MESSAGE": None}],
    },
    {
        "name": "Peacock",
        "country": ["usa"],
        "id": ["88"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "88", "MESSAGE": None}],
    },
    {
        "name": "Phoenix TV",
        "country": ["usa", "can", "mex"],
        "id": ["116"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "114", "MESSAGE": None}],
    },
    {
        "name": "PlayWorks Kids",
        "country": ["usa", "can"],
        "id": ["171"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "171", "MESSAGE": None}],
    },
    {
        "name": "Plex",
        "country": ["usa", "can"],
        "id": ["40"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "9", "MESSAGE": None}],
    },
    {
        "name": "Pluto TV",
        "country": ["usa"],
        "id": ["12"],
        "config": [
            {
                "NAME_SPACE": 0,
                "APP_ID": "E6F74C01",
                "MESSAGE": '{"CAST_NAMESPACE":"urn:x-cast:tv.pluto","CAST_MESSAGE":{"command":"initializePlayback","channel":"","episode":"","time":0}}',
            }
        ],
    },
    {
        "name": "Popstar TV",
        "country": ["usa", "can"],
        "id": ["164"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "164", "MESSAGE": None}],
    },
    {
        "name": "Prime Video",
        "country": ["*"],
        "id": ["33"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "4", "MESSAGE": None}],
    },
    {
        "name": "ROW8",
        "country": ["usa"],
        "id": ["94"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "102", "MESSAGE": None}],
    },
    {
        "name": "RedBox",
        "country": ["usa"],
        "id": ["55"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "41", "MESSAGE": None}],
    },
    {
        "name": "RetroCrush",
        "country": ["usa", "can"],
        "id": ["102"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "105", "MESSAGE": None}],
    },
    {
        "name": "Run The Fut Market",
        "country": ["usa"],
        "id": ["210"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "210", "MESSAGE": None}],
    },
    {
        "name": "Run:Time en Espa\u00f1ol",
        "country": ["usa", "can"],
        "id": ["118"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "127", "MESSAGE": None}],
    },
    {
        "name": "STARZ",
        "country": ["usa"],
        "id": ["151"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "151", "MESSAGE": None}],
    },
    {
        "name": "Sanctuary Yoga",
        "country": ["usa"],
        "id": ["89"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "89", "MESSAGE": None}],
    },
    {
        "name": "Screambox",
        "country": ["usa", "can"],
        "id": ["2155"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "155", "MESSAGE": None}],
    },
    {
        "name": "Sensical",
        "country": ["usa"],
        "id": ["148"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "148", "MESSAGE": None}],
    },
    {
        "name": "Sesame Street",
        "country": ["usa", "can"],
        "id": ["73"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "68", "MESSAGE": None}],
    },
    {
        "name": "Shudder",
        "country": ["usa", "can"],
        "id": ["2142"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "142", "MESSAGE": None}],
    },
    {
        "name": "Sirius XM",
        "country": ["usa"],
        "id": ["2212"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "212", "MESSAGE": None}],
    },
    {
        "name": "Sling TV",
        "country": ["usa"],
        "id": ["150"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "150", "MESSAGE": None}],
    },
    {
        "name": "Smart Cinema",
        "country": ["usa"],
        "id": ["2101"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "101", "MESSAGE": None}],
    },
    {
        "name": "Space Channel",
        "country": ["usa", "can"],
        "id": ["121"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "126", "MESSAGE": None}],
    },
    {
        "name": "Ssundee",
        "country": ["usa", "can"],
        "id": ["132"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "132", "MESSAGE": None}],
    },
    {
        "name": "SundanceNOW",
        "country": ["usa", "can"],
        "id": ["2143"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "143", "MESSAGE": None}],
    },
    {
        "name": "TLC GO",
        "country": ["usa"],
        "id": ["2226"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "226", "MESSAGE": None}],
    },
    {
        "name": "The Archive",
        "country": ["usa", "can", "mex"],
        "id": ["93"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "71", "MESSAGE": None}],
    },
    {
        "name": "The CW",
        "country": ["usa"],
        "id": ["108"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "115", "MESSAGE": None}],
    },
    {
        "name": "The Daily Wire",
        "country": ["usa", "can"],
        "id": ["169"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "169", "MESSAGE": None}],
    },
    {
        "name": "The First",
        "country": ["usa", "can"],
        "id": ["149"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "149", "MESSAGE": None}],
    },
    {
        "name": "TikTok",
        "country": ["usa"],
        "id": ["184"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "184", "MESSAGE": None}],
    },
    {
        "name": "Toon Goggles",
        "country": ["usa", "can"],
        "id": ["46"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "21", "MESSAGE": None}],
    },
    {
        "name": "Tubi",
        "country": ["usa", "can"],
        "id": ["90"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "61", "MESSAGE": None}],
    },
    {
        "name": "URBN TV",
        "country": ["usa", "can"],
        "id": ["2230"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "230", "MESSAGE": None}],
    },
    {
        "name": "US Weekly TV",
        "country": ["usa", "can"],
        "id": ["146"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "146", "MESSAGE": None}],
    },
    {
        "name": "Very Local",
        "country": ["usa", "can"],
        "id": ["181"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "181", "MESSAGE": None}],
    },
    {
        "name": "Vevo",
        "country": ["usa", "can", "mex"],
        "id": ["105"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "107", "MESSAGE": None}],
    },
    {
        "name": "Vudu",
        "country": ["usa"],
        "id": ["6"],
        "config": [
            {
                "NAME_SPACE": 2,
                "APP_ID": "31",
                "MESSAGE": "https://my.vudu.com/castReceiver/index.html?launch-source=app-icon",
            }
        ],
    },
    {
        "name": "WatchFree+",
        "country": ["usa"],
        "id": ["48"],
        "config": [
            {
                "NAME_SPACE": 2,
                "APP_ID": "3014",
                "MESSAGE": "http://127.0.0.1:12345/scfs/sctv/main.html#/watchfreeplus",
            }
        ],
    },
    {
        "name": "WatchFree+ On Demand",
        "country": ["usa", "can"],
        "id": ["2145"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "145", "MESSAGE": None}],
    },
    {
        "name": "World Poker Tour",
        "country": ["usa"],
        "id": ["2185"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "185", "MESSAGE": None}],
    },
    {
        "name": "Wu Tang Collection",
        "country": ["usa", "can"],
        "id": ["78"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "72", "MESSAGE": None}],
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
        "name": "YouTube",
        "country": ["*"],
        "id": ["44"],
        "config": [{"NAME_SPACE": 5, "APP_ID": "1", "MESSAGE": None}],
    },
    {
        "name": "YouTube TV",
        "country": ["usa", "mex"],
        "id": ["45"],
        "config": [{"NAME_SPACE": 5, "APP_ID": "3", "MESSAGE": None}],
    },
    {
        "name": "Zoomi",
        "country": ["usa", "can"],
        "id": ["141"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "141", "MESSAGE": None}],
    },
    {
        "name": "discovery+",
        "country": ["usa"],
        "id": ["130"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "130", "MESSAGE": None}],
    },
    {
        "name": "fuboTV",
        "country": ["usa"],
        "id": ["138"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "138", "MESSAGE": None}],
    },
    {
        "name": "iFood.TV",
        "country": ["usa"],
        "id": ["2124"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "124", "MESSAGE": None}],
    },
    {
        "name": "iHeartRadio",
        "country": ["usa"],
        "id": ["11"],
        "config": [{"NAME_SPACE": 2, "APP_ID": "6", "MESSAGE": None}],
    },
]
