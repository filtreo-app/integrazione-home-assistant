"""Filtreo: il filtro di casa dentro Home Assistant (e, col ponte HomeKit, nell'app Casa e in Siri)."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import FiltreoApi, FiltreoErrore
from .const import ATTR_MINUTI, CONF_TOKEN, DOMAIN, SERVIZIO_PAUSA
from .coordinator import FiltreoCoordinator

PLATFORMS = [Platform.SWITCH, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SELECT]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type FiltreoConfigEntry = ConfigEntry[FiltreoCoordinator]

SCHEMA_PAUSA = vol.Schema({vol.Required(ATTR_MINUTI): vol.All(vol.Coerce(int), vol.Range(min=1, max=480))})


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Il servizio filtreo.pausa (minuti): vale per ogni Filtreo configurato."""

    async def _pausa(call: ServiceCall) -> None:
        voci = hass.config_entries.async_loaded_entries(DOMAIN)
        if not voci:
            raise ServiceValidationError("Filtreo non è configurato.")
        for voce in voci:
            try:
                r = await voce.runtime_data.api.pausa(call.data[ATTR_MINUTI])
            except FiltreoErrore as e:
                raise HomeAssistantError(f"Filtreo non risponde: {e}") from e
            if not r.get("ok", False):
                raise HomeAssistantError(r.get("testo") or "Pausa non riuscita.")
            await voce.runtime_data.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVIZIO_PAUSA, _pausa, schema=SCHEMA_PAUSA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: FiltreoConfigEntry) -> bool:
    api = FiltreoApi(async_get_clientsession(hass), entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_TOKEN])
    coordinator = FiltreoCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: FiltreoConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
