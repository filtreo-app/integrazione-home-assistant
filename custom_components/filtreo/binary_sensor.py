"""binary_sensor.filtreo_cloudflare: il paracadute su Cloudflare (filtro fuori casa) è collegato e attivo."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import FiltreoEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities([FiltreoCloudflare(entry.runtime_data)])


class FiltreoCloudflare(FiltreoEntity, BinarySensorEntity):
    _attr_name = "Filtreo Cloud"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:cloud-check"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "cloudflare")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("cloudflare"))
