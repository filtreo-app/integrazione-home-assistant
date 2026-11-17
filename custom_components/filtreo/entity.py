"""Base comune: tutte le entità stanno sotto un unico dispositivo «Filtreo»."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FiltreoCoordinator


class FiltreoEntity(CoordinatorEntity[FiltreoCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: FiltreoCoordinator, chiave: str) -> None:
        super().__init__(coordinator)
        voce = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{voce}_{chiave}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, voce)},
            name="Filtreo",
            manufacturer="Filtreo",
            model="Filtro di rete",
            sw_version=(coordinator.data or {}).get("versione") or None,
        )
