"""Title displayed in meeting mode."""
from homeassistant.components.text import TextEntity, TextMode
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN
from .entity import MediaCenterEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([MediaCenterMeetingTitle(hass.data[DOMAIN][entry.entry_id], entry)])


class MediaCenterMeetingTitle(MediaCenterEntity, TextEntity):
    _attr_native_min = 0
    _attr_native_max = 160
    _attr_mode = TextMode.TEXT

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "meeting_title", "Titolo riunione", "mdi:format-title")

    @property
    def native_value(self):
        return self.coordinator.data.get("meeting_title")

    async def async_set_value(self, value):
        if len(value) > 160:
            raise HomeAssistantError("Il titolo può contenere al massimo 160 caratteri")
        await self.coordinator.async_command("configure", {"meeting_title": value})
