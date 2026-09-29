"""System audio volume."""
import math
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN
from .entity import MediaCenterEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([MediaCenterVolume(hass.data[DOMAIN][entry.entry_id], entry)])


class MediaCenterVolume(MediaCenterEntity, NumberEntity):
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "volume", "Volume", "mdi:volume-high")

    @property
    def native_value(self):
        return self.coordinator.data.get("volume")

    async def async_set_native_value(self, value):
        if not math.isfinite(value) or not 0 <= value <= 100 or value != int(value):
            raise HomeAssistantError("Volume: intero da 0 a 100")
        await self.coordinator.async_command("set_audio", {"volume": int(value)})
