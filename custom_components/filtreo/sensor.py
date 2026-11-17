"""Sensori: bloccate oggi, richieste oggi, percentuale, dispositivi."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
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
    # 1.2.0: «Profilo <dispositivo>», solo da leggere (si scelgono e si personalizzano nelle app Filtreo)
    noti: set[str] = set()

    @callback
    def _nuovi() -> None:
        nuove = []
        for d in c.data.get("dispositivi") or []:
            if d["id"] not in noti:
                noti.add(d["id"])
                nuove.append(FiltreoProfilo(c, d["id"], d["nome"]))
        if nuove:
            async_add_entities(nuove)

    _nuovi()
    entry.async_on_unload(c.async_add_listener(_nuovi))


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


class FiltreoProfilo(FiltreoEntity, SensorEntity):
    """il profilo che usa un dispositivo, con lo stesso nome delle app («Personale», «Standard · personalizzato»)"""
    _attr_icon = "mdi:shield-account-outline"

    def __init__(self, coordinator, did: str, nome: str) -> None:
        super().__init__(coordinator, f"profilo_{did}")
        self._did = did
        self._attr_name = f"Profilo {nome}"

    def _profilo(self) -> dict | None:
        d = next((x for x in self.coordinator.data.get("dispositivi") or [] if x["id"] == self._did), None)
        return next((m for m in self.coordinator.data.get("modalita") or [] if d and m["id"] == d.get("modo")), None)

    @property
    def available(self) -> bool:
        return super().available and any(d["id"] == self._did for d in self.coordinator.data.get("dispositivi") or [])

    @property
    def native_value(self) -> str | None:
        m = self._profilo()
        return m["nome"] if m else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        m = self._profilo() or {}
        return {"dettaglio": m.get("sotto") or ""}
