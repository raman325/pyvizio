"""pyvizio utility constants."""

APK_SOURCE_PATH = "src"
RESOURCE_PATH = "resources/res/raw"
APP_NAMES_FILE = "apps.json"
APP_PAYLOADS_FILE = "apps_availability.json"

# Class with app URLs: com.vizio.smartcast.apps.repository.AppServiceConfigRepositoryImpl
# Hostname stored in DEFAULT_APPS_HOSTNAME
# Use the constants below to find the values

# DEFAULT_APPS_PATH_PROD
APP_NAMES_URL = "http://scfs.vizio.com/appservice/vizio_apps_prod.json"
# DEFAULT_AVAILABILITY_PATH_PROD
APP_PAYLOADS_URL = "http://scfs.vizio.com/appservice/app_availability_prod.json"
