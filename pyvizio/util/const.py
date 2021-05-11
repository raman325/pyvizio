"""pyvizio utility constants."""

APK_SOURCE_PATH = "src"
RESOURCE_PATH = "resources/res/raw"
APP_NAMES_FILE = "apps.json"
APP_PAYLOADS_FILE = "apps_availability.json"

# File with app URLs: smartcast.apk-decompiled\res\values\strings.xml
# Use the keys below to find the values

# <string name="default_appsservice_app_server">
APP_NAMES_URL = "http://hometest.buddytv.netdna-cdn.com/appservice/vizio_apps_prod.json"
# <string name="default_appsservice_availability_server">
APP_PAYLOADS_URL = (
    "http://hometest.buddytv.netdna-cdn.com/appservice/app_availability_prod.json"
)
