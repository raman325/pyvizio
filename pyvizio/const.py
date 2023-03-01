"""pyvizio constants."""

DEVICE_CLASS_SPEAKER = "speaker"
DEVICE_CLASS_TV = "tv"
DEVICE_CLASS_CRAVE360 = "crave360"

DEFAULT_DEVICE_ID = "pyvizio"
DEFAULT_DEVICE_CLASS = DEVICE_CLASS_TV
DEFAULT_DEVICE_NAME = "Python Vizio"
DEFAULT_PORTS = [7345, 9000]
DEFAULT_TIMEOUT = 5

MAX_VOLUME = {DEVICE_CLASS_TV: 100, DEVICE_CLASS_SPEAKER: 31, DEVICE_CLASS_CRAVE360: 100}

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
		"name": "YouTube",
		"country": ["*"],
		"id": ["44"],
		"config": [
			{
				"NAME_SPACE": 5,
				"APP_ID": "1",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "YouTube TV",
		"country": ["usa", "mex"],
		"id": ["45"],
		"config": [
			{
				"NAME_SPACE": 5,
				"APP_ID": "3",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Smart Cinema",
		"country": ["usa"],
		"id": ["2101"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "101",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "ROW8",
		"country": ["usa"],
		"id": ["94"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "102",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Free Games by PlayWorks",
		"country": ["usa"],
		"id": ["101"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "104",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "RetroCrush",
		"country": ["usa", "can"],
		"id": ["102"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "105",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Bob Ross",
		"country": ["usa"],
		"id": ["120"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "106",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Vevo",
		"country": ["usa", "can", "mex"],
		"id": ["105"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "107",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Gravitas Movies",
		"country": ["usa"],
		"id": ["119"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "108",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "FOX NOW",
		"country": ["usa"],
		"id": ["110"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "109",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "NBC",
		"country": ["usa"],
		"id": ["43"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "10",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Fox Nation",
		"country": ["usa"],
		"id": ["111"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "110",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "FOX Sports",
		"country": ["usa"],
		"id": ["2111"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "111",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "CBS Sports",
		"country": ["usa"],
		"id": ["109"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "112",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Phoenix TV",
		"country": ["usa", "can", "mex"],
		"id": ["116"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "114",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "The CW",
		"country": ["usa"],
		"id": ["108"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "115",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "PBS Kids",
		"country": ["usa"],
		"id": ["112"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "117",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Brooke Burke Body",
		"country": ["usa", "can", "mex"],
		"id": ["114"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "118",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Canela.TV",
		"country": ["usa"],
		"id": ["113"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "119",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "BET+",
		"country": ["usa"],
		"id": ["126"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "121",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "LEGO TV",
		"country": ["usa"],
		"id": ["123"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "122",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "CoCoMelon",
		"country": ["usa", "can"],
		"id": ["124"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "123",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "iFood.TV",
		"country": ["usa"],
		"id": ["2124"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "124",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "GoTraveler",
		"country": ["usa", "can"],
		"id": ["117"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "125",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Space Channel",
		"country": ["usa", "can"],
		"id": ["121"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "126",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Run:Time en Espa\u00f1ol",
		"country": ["usa", "can"],
		"id": ["118"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "127",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "HBO Max",
		"country": ["usa"],
		"id": ["128"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "128",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "PBS",
		"country": ["usa"],
		"id": ["129"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "129",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "CuriosityStream",
		"country": ["usa", "can"],
		"id": ["37"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "12",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "discovery+",
		"country": ["usa"],
		"id": ["130"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "130",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Ssundee",
		"country": ["usa", "can"],
		"id": ["132"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "132",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Crime & Conspiracy",
		"country": ["usa", "can"],
		"id": ["133"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "133",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Motorvision TV",
		"country": ["usa", "can"],
		"id": ["135"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "135",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Boondock Nation",
		"country": ["usa", "can"],
		"id": ["136"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "136",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Docurama",
		"country": ["usa", "can"],
		"id": [null],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "137",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "fuboTV",
		"country": ["usa"],
		"id": ["138"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "138",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Into The Outdoors",
		"country": ["usa"],
		"id": ["139"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "139",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Zoomi",
		"country": ["usa", "can"],
		"id": ["141"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "141",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Shudder",
		"country": ["usa", "can"],
		"id": ["2142"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "142",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "SundanceNOW",
		"country": ["usa", "can"],
		"id": ["2143"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "143",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "AfrolandTV",
		"country": ["usa", "can"],
		"id": ["144"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "144",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "WatchFree+ On Demand",
		"country": ["usa", "can"],
		"id": ["2145"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "145",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "US Weekly TV",
		"country": ["usa", "can"],
		"id": ["146"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "146",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Sensical",
		"country": ["usa"],
		"id": ["148"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "148",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "The First",
		"country": ["usa", "can"],
		"id": ["149"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "149",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Sling TV",
		"country": ["usa"],
		"id": ["150"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "150",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "STARZ",
		"country": ["usa"],
		"id": ["151"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "151",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Beani.TV",
		"country": ["usa", "can"],
		"id": ["152"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "152",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Hipstr",
		"country": ["usa", "can"],
		"id": ["153"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "153",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Fandor",
		"country": ["usa", "can"],
		"id": ["2154"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "154",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Screambox",
		"country": ["usa", "can"],
		"id": ["2155"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "155",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Amazon Music",
		"country": ["usa", "can"],
		"id": ["156"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "156",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "KORTV",
		"country": ["usa", "can"],
		"id": ["157"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "157",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Bon App\u00e9tit",
		"country": ["usa", "can"],
		"id": ["158"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "158",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Newsy",
		"country": ["usa", "can"],
		"id": ["38"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "15",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "History Vault",
		"country": ["usa"],
		"id": ["160"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "160",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Lifetime Movie Club",
		"country": ["usa"],
		"id": ["161"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "161",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "A&E Crime Central",
		"country": ["usa"],
		"id": ["162"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "162",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Outside TV",
		"country": ["usa", "can"],
		"id": ["163"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "163",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Popstar TV",
		"country": ["usa", "can"],
		"id": ["164"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "164",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Estrella TV",
		"country": ["usa"],
		"id": ["165"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "165",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Novocomedy",
		"country": ["usa", "can"],
		"id": ["166"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "166",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Lava",
		"country": ["usa", "can"],
		"id": ["167"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "167",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Chicken Soup For The Soul",
		"country": ["usa"],
		"id": ["168"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "168",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "The Daily Wire",
		"country": ["usa", "can"],
		"id": ["169"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "169",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Dove Channel",
		"country": ["usa", "can"],
		"id": ["42"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "16",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Outdoor America",
		"country": ["usa", "can"],
		"id": ["170"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "170",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "PlayWorks Kids",
		"country": ["usa", "can"],
		"id": ["171"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "171",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Annoying Orange",
		"country": ["usa", "can"],
		"id": ["172"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "172",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Baby Einstein",
		"country": ["usa", "can"],
		"id": ["175"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "175",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Passionflix",
		"country": ["usa", "can"],
		"id": ["176"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "176",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Distro TV",
		"country": ["usa", "can"],
		"id": ["2178"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "178",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Nosey",
		"country": ["usa", "can"],
		"id": ["179"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "179",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Very Local",
		"country": ["usa", "can"],
		"id": ["181"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "181",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "TikTok",
		"country": ["usa"],
		"id": ["184"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "184",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "World Poker Tour",
		"country": ["usa"],
		"id": ["2185"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "185",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "FamilyTime",
		"country": ["usa", "can"],
		"id": ["2186"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "186",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Here TV",
		"country": ["usa", "can"],
		"id": ["188"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "188",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "ConTV",
		"country": ["usa", "can"],
		"id": ["41"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "18",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "MyOutdoorTV",
		"country": ["usa", "can"],
		"id": ["192"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "192",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "La Bocina Latina",
		"country": ["usa", "can"],
		"id": ["194"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "194",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Hallmark Movies Now",
		"country": ["usa"],
		"id": ["2203"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "203",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "BRB Travel & Food",
		"country": ["usa"],
		"id": ["207"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "207",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Best of Roblox",
		"country": ["usa"],
		"id": ["208"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "208",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Dan TDM",
		"country": ["usa"],
		"id": ["209"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "209",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Run The Fut Market",
		"country": ["usa"],
		"id": ["210"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "210",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Sirius XM",
		"country": ["usa"],
		"id": ["2212"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "212",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "AMC+",
		"country": ["usa"],
		"id": ["2218"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "218",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Journy",
		"country": ["usa", "can"],
		"id": ["2219"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "219",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Toon Goggles",
		"country": ["usa", "can"],
		"id": ["46"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "21",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Discovery Go",
		"country": ["usa"],
		"id": ["2222"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "222",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Food Network Go",
		"country": ["usa"],
		"id": ["2223"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "223",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "HGTV",
		"country": ["usa"],
		"id": ["2224"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "224",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Investigation Discovery (ID) Go",
		"country": ["usa"],
		"id": ["2225"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "225",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "TLC GO",
		"country": ["usa"],
		"id": ["2226"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "226",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Christmas Plus",
		"country": ["usa"],
		"id": ["2228"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "228",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Free Movies+",
		"country": ["usa"],
		"id": ["2229"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "229",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "URBN TV",
		"country": ["usa", "can"],
		"id": ["2230"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "230",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Made It Myself TV",
		"country": ["usa", "can"],
		"id": ["2239"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "239",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "FilmRise",
		"country": ["usa"],
		"id": ["47"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "24",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "AsianCrush",
		"country": ["usa", "can"],
		"id": ["50"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "27",
				"MESSAGE": "https://html5.asiancrush.com/?ua=viziosmartcast"
			}
		]
	},
	{
		"name": "Midnight Pulp",
		"country": ["usa", "can"],
		"id": ["122"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "28",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Cinehouse",
		"country": ["usa", "can"],
		"id": ["80"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "29",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "WatchFree+",
		"country": ["usa"],
		"id": ["48"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "3014",
				"MESSAGE": "http://127.0.0.1:12345/scfs/sctv/main.html#/watchfreeplus"
			}
		]
	},
	{
		"name": "Vudu",
		"country": ["usa"],
		"id": ["6"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "31",
				"MESSAGE": "https://my.vudu.com/castReceiver/index.html?launch-source=app-icon"
			}
		]
	},
	{
		"name": "DAZN",
		"country": ["usa", "can"],
		"id": ["57"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "34",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Flixfling",
		"country": ["*"],
		"id": ["49"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "36",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Paramount+",
		"country": ["usa"],
		"id": ["9"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "37",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Movies Anywhere",
		"country": ["usa"],
		"id": ["86"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "38",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "FitFusion",
		"country": ["usa", "can"],
		"id": ["54"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "39",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Hulu",
		"country": ["usa"],
		"id": ["19"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "3",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "RedBox",
		"country": ["usa"],
		"id": ["55"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "41",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "CBS News",
		"country": ["usa", "can"],
		"id": ["56"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "42",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Adventure Sports Network",
		"country": ["usa", "can"],
		"id": ["244"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "44",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Love Destination",
		"country": ["*"],
		"id": ["64"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "57",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Pandora",
		"country": ["usa"],
		"id": ["70"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "58",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Funimation",
		"country": ["usa", "can"],
		"id": ["59"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "59",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Crackle",
		"country": ["usa"],
		"id": ["8"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "5",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Haystack TV",
		"country": ["usa", "can"],
		"id": ["35"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "60",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Tubi",
		"country": ["usa", "can"],
		"id": ["90"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "61",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "XUMO",
		"country": ["usa"],
		"id": ["27"],
		"config": [
			{
				"NAME_SPACE": 0,
				"APP_ID": "36E1EA1F",
				"MESSAGE": "{\"CAST_NAMESPACE\":\"urn:x-cast:com.google.cast.media\",\"CAST_MESSAGE\":{\"type\":\"LOAD\",\"media\":{},\"autoplay\":true,\"currentTime\":0,\"customData\":{}}}"
			}
		]
	},
	{
		"name": "Pluto TV",
		"country": ["usa"],
		"id": ["12"],
		"config": [
			{
				"NAME_SPACE": 0,
				"APP_ID": "E6F74C01",
				"MESSAGE": "{\"CAST_NAMESPACE\":\"urn:x-cast:tv.pluto\",\"CAST_MESSAGE\":{\"command\":\"initializePlayback\",\"channel\":\"\",\"episode\":\"\",\"time\":0}}"
			}
		]
	},
	{
		"name": "Blackdove",
		"country": ["usa", "can"],
		"id": ["71"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "66",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "MagellanTV",
		"country": ["usa", "can"],
		"id": ["74"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "67",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Sesame Street",
		"country": ["usa", "can"],
		"id": ["73"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "68",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Brown Sugar",
		"country": ["usa"],
		"id": ["84"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "69",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "iHeartRadio",
		"country": ["usa"],
		"id": ["11"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "6",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Party Tyme Karaoke",
		"country": ["usa", "can"],
		"id": ["77"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "70",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "The Archive",
		"country": ["usa", "can", "mex"],
		"id": ["93"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "71",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Wu Tang Collection",
		"country": ["usa", "can"],
		"id": ["78"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "72",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Acorn TV",
		"country": ["usa"],
		"id": ["97"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "74",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Disney+",
		"country": ["usa", "can", "mex"],
		"id": ["76"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "75",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Comedy Dynamics",
		"country": ["usa"],
		"id": ["276"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "76",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Court TV",
		"country": ["usa"],
		"id": ["87"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "78",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Local Now",
		"country": ["usa"],
		"id": ["85"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "79",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Dark Matter TV",
		"country": ["usa"],
		"id": ["82"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "81",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Fite TV",
		"country": ["usa", "can"],
		"id": ["83"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "82",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Adventure 2 Learning",
		"country": ["usa"],
		"id": ["106"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "83",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "HappyKids.tv",
		"country": ["usa"],
		"id": ["103"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "85",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Fawesome.tv",
		"country": ["usa"],
		"id": ["104"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "87",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Peacock",
		"country": ["usa"],
		"id": ["88"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "88",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Sanctuary Yoga",
		"country": ["usa"],
		"id": ["89"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "89",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "ElectricNow",
		"country": ["usa", "can"],
		"id": ["290"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "90",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Kidoodle.tv",
		"country": ["usa", "can"],
		"id": ["92"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "92",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Ninja Kidz TV",
		"country": ["usa"],
		"id": ["115"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "93",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Hometalk TV",
		"country": ["usa"],
		"id": ["100"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "95",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Plex",
		"country": ["usa", "can"],
		"id": ["40"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "9",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Netflix",
		"country": ["*"],
		"id": ["34"],
		"config": [
			{
				"NAME_SPACE": 3,
				"APP_ID": "1",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Prime Video",
		"country": ["*"],
		"id": ["33"],
		"config": [
			{
				"NAME_SPACE": 2,
				"APP_ID": "4",
				"MESSAGE": null
			}
		]
	},
	{
		"name": "Apple TV+",
		"country": ["usa"],
		"id": ["91"],
		"config": [
			{
				"NAME_SPACE": 3,
				"APP_ID": "4",
				"MESSAGE": null
			}
		]
	}
]
