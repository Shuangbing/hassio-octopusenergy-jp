"""Sensor platform for Octopus Energy Japan integration."""
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    UnitOfEnergy,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import OctopusEnergyJP
from .const import (
    ATTRIBUTION,
    CONF_ACCOUNT_NUMBER,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
    ENERGY_COST_SENSOR,
    ENERGY_USAGE_SENSOR,
    ICON_ENERGY,
    ICON_MONEY,
    NAME,
    UNIT_YEN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Octopus Energy Japan sensor."""
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    account_number = entry.data[CONF_ACCOUNT_NUMBER]
    scan_interval_hours = entry.options.get(
        CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS)
    )

    session = async_get_clientsession(hass)
    api = OctopusEnergyJP(
        session=session,
        email=email,
        password=password,
        account_number=account_number,
    )

    # 创建数据协调器
    async def async_update_data() -> Dict[str, float]:
        """Fetch data from API."""
        return await api.async_get_yesterday_data()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{NAME} ({account_number})",
        update_method=async_update_data,
        update_interval=timedelta(hours=scan_interval_hours),
    )

    # 初始数据获取
    await coordinator.async_config_entry_first_refresh()

    entities = [
        OctopusEnergyJPEnergySensor(coordinator, entry, account_number),
        OctopusEnergyJPCostSensor(coordinator, entry, account_number),
    ]

    async_add_entities(entities, True)


class OctopusEnergyJPSensorBase(CoordinatorEntity):
    """Base class for Octopus Energy Japan sensors."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        account_number: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._account_number = account_number
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, account_number)},
            name=f"{NAME} ({account_number})",
            manufacturer="Octopus Energy Japan",
            model="Electricity Supply",
            entry_type="service",
        )
        self._config_entry = config_entry
        self._attr_attribution = ATTRIBUTION

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success


class OctopusEnergyJPEnergySensor(OctopusEnergyJPSensorBase, SensorEntity):
    """Sensor for electricity usage."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_has_entity_name = True
    _attr_icon = ICON_ENERGY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        account_number: str,
    ) -> None:
        """Initialize the energy usage sensor."""
        super().__init__(coordinator, config_entry, account_number)
        self._attr_unique_id = f"{account_number}_{ENERGY_USAGE_SENSOR}"
        self._attr_name = "Yesterday's Energy Usage"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("energy_usage")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes of the sensor."""
        return {
            "account_number": self._account_number,
            "last_updated": self.coordinator.last_update_success,
        }


class OctopusEnergyJPCostSensor(OctopusEnergyJPSensorBase, SensorEntity):
    """Sensor for electricity cost."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UNIT_YEN
    _attr_has_entity_name = True
    _attr_icon = ICON_MONEY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        account_number: str,
    ) -> None:
        """Initialize the energy cost sensor."""
        super().__init__(coordinator, config_entry, account_number)
        self._attr_unique_id = f"{account_number}_{ENERGY_COST_SENSOR}"
        self._attr_name = "Yesterday's Energy Cost"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("energy_cost")

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes of the sensor."""
        return {
            "account_number": self._account_number,
            "last_updated": self.coordinator.last_update_success,
        } 