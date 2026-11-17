"""switch.filtreo: acceso = filtro attivo; spento = in pausa (con la durata che il pannello ricorda)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import FiltreoEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities([FiltreoInterruttore(entry.runtime_data)])


class FiltreoInterruttore(FiltreoEntity, SwitchEntity):
    _attr_name = None            # = il nome del dispositivo: switch.filtreo
    _attr_icon = "mdi:shield-check"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "filtro")

    @property
    def available(self) -> bool:
        return super().available and bool(self.coordinator.data.get("raggiungibile"))

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("acceso"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        d = self.coordinator.data
        p = d.get("pausa") or {}
        return {"in_pausa": bool(p.get("attiva")), "pausa_resta_secondi": int(p.get("resta_sec") or 0),
                "pausa_senza_scadenza": bool(p.get("senza_scadenza")), "durata_pausa": d.get("pausa_durata")}

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api.riprendi()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.spegni()
        await self.coordinator.async_request_refresh()
