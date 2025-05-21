"""Constants for the Octopus Energy Japan integration."""

DOMAIN = "octopusenergy_jp"
NAME = "Octopus Energy Japan"

# Configuration
CONF_ACCOUNT_NUMBER = "account_number"
CONF_SCAN_INTERVAL = "scan_interval"

# API
API_ENDPOINT = "https://api.oejp-kraken.energy/v1/graphql/"
TOKEN_VALID_DURATION = 3600  # Token valid for 1 hour (3600 seconds)

# Sensor
ENERGY_USAGE_SENSOR = "energy_usage"
ENERGY_COST_SENSOR = "energy_cost"
ATTRIBUTION = "Data provided by Octopus Energy Japan"

# Units
UNIT_KWH = "kWh"
UNIT_YEN = "¥"

# Icons
ICON_ENERGY = "mdi:flash"
ICON_MONEY = "mdi:currency-jpy"

# Default values
DEFAULT_SCAN_INTERVAL_HOURS = 3  # Default scan interval in hours 