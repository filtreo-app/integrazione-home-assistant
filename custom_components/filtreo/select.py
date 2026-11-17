"""select.filtreo_modalita_<dispositivo>: cambia la modalità dei dispositivi che hanno «regole sue»."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import FiltreoEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    noti: set[str] = set()

    @callback
    def _nuovi() -> None:
        nuove = []
        for d in coordinator.data.get("dispositivi") or []:
            if d.get("proprie") and d["id"] not in noti:
                noti.add(d["id"])
                nuove.append(FiltreoModalita(coordinator, d["id"], d["nome"]))
        if nuove:
            async_add_entities(nuove)

    _nuovi()
    entry.async_on_unload(coordinator.async_add_listener(_nuovi))


class FiltreoModalita(FiltreoEntity, SelectEntity):
    _attr_icon = "mdi:tune-variant"

    def __init__(self, coordinator, did: str, nome: str) -> None:
        super().__init__(coordinator, f"modo_{did}")
        self._did = did
        self._attr_name = f"Livello {nome}"   # 1.1.2: stesso nome delle app («Livello»)

    def _modalita(self) -> list[dict]:
        return self.coordinator.data.get("modalita") or []

    @property
    def available(self) -> bool:
        return super().available and any(d["id"] == self._did and d.get("proprie")
                                         for d in self.coordinator.data.get("dispositivi") or [])

    @property
    def options(self) -> list[str]:
        return [m["nome"] for m in self._modalita()]

    @property
    def current_option(self) -> str | None:
        d = next((x for x in self.coordinator.data.get("dispositivi") or [] if x["id"] == self._did), None)
        m = next((m for m in self._modalita() if d and m["id"] == d.get("modo")), None)
        return m["nome"] if m else None

    async def async_select_option(self, option: str) -> None:
        m = next((m for m in self._modalita() if m["nome"] == option), None)
        if not m:
            raise HomeAssistantError(f"Livello sconosciuto: {option}")
        r = await self.coordinator.api.modo(self._did, m["id"])
        if not r.get("ok"):
            raise HomeAssistantError(r.get("testo") or "Impossibile cambiare il livello di protezione.")
        await self.coordinator.async_request_refresh()
