"""Config flow for Octopus Energy Japan integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import OctopusEnergyJP
from .const import (
    CONF_ACCOUNT_NUMBER,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_ACCOUNT_NUMBER): cv.string,
        vol.Optional(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL_HOURS
        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    api = OctopusEnergyJP(
        session=session,
        email=data[CONF_EMAIL],
        password=data[CONF_PASSWORD],
        account_number=data[CONF_ACCOUNT_NUMBER],
    )

    await api.async_get_token()  # 验证凭证是否有效

    return {"title": f"Octopus Energy Japan ({data[CONF_ACCOUNT_NUMBER]})"}


class OctopusEnergyJPConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Octopus Energy Japan."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OctopusEnergyJPOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except Exception:
                _LOGGER.exception("Failed to authenticate with Octopus Energy Japan")
                errors["base"] = "auth"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class OctopusEnergyJPOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=24)),
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options)) 