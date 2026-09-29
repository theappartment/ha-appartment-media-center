"""Effective system mute, including standby mute."""
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN
from .entity import MediaCenterEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([MediaCenterMute(hass.data[DOMAIN][entry.entry_id], entry)])


class MediaCenterMute(MediaCenterEntity, SwitchEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "muted", "Muto", "mdi:volume-off")

    @property
    def is_on(self):
        return self.coordinator.data.get("muted")

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_command("set_audio", {"muted": True})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_command("set_audio", {"muted": False})
