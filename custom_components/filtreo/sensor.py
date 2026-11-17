"""Sensori: bloccate oggi, richieste oggi, percentuale, dispositivi."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import FiltreoEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    c = entry.runtime_data
    async_add_entities([
        FiltreoNumero(c, "bloccate_oggi", "Bloccate oggi", "bloccate", "mdi:shield-off", None),
        FiltreoNumero(c, "richieste_oggi", "Richieste oggi", "richieste", "mdi:dns", None),
        FiltreoNumero(c, "percentuale", "Percentuale", "percento", "mdi:percent", PERCENTAGE),
        FiltreoDispositivi(c),
    ])


class FiltreoNumero(FiltreoEntity, SensorEntity):
    def __init__(self, coordinator, chiave, nome, campo, icona, unita) -> None:
        super().__init__(coordinator, chiave)
        self._attr_name = nome
        self._campo = campo
        self._attr_icon = icona
        self._attr_native_unit_of_measurement = unita
        # «oggi» riparte da zero a mezzanotte: TOTAL_INCREASING lo tratta come un nuovo giorno
        self._attr_state_class = SensorStateClass.MEASUREMENT if campo == "percento" else SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> int:
        return int((self.coordinator.data.get("oggi") or {}).get(self._campo) or 0)


class FiltreoDispositivi(FiltreoEntity, SensorEntity):
    _attr_name = "Dispositivi"
    _attr_icon = "mdi:devices"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "dispositivi")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("dispositivi") or [])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"elenco": {d["nome"]: d.get("modo") or "" for d in self.coordinator.data.get("dispositivi") or []}}
