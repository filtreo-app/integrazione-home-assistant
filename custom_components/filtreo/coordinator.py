"""Il coordinatore: chiede lo stato a Filtreo ogni 30 secondi e lo passa a tutte le entità."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FiltreoApi, FiltreoChiaveErrata, FiltreoErrore
from .const import DOMAIN, SCAN_SECONDI

_LOGGER = logging.getLogger(__name__)


class FiltreoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: FiltreoApi) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN,
                         update_interval=timedelta(seconds=SCAN_SECONDI))
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            dati = await self.api.stato()
        except FiltreoChiaveErrata as e:
            raise ConfigEntryAuthFailed("Chiave di Filtreo non più valida") from e
        except FiltreoErrore as e:
            raise UpdateFailed(f"Filtreo non risponde: {e}") from e
        return dati
