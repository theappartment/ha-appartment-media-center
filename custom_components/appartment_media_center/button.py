"""Operational and presentation controls."""
from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN, BUTTONS
from .entity import MediaCenterEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([MediaCenterButton(hass.data[DOMAIN][entry.entry_id], entry, key)
                        for key in BUTTONS])


class MediaCenterButton(MediaCenterEntity, ButtonEntity):
    def __init__(self, coordinator, entry, key):
        name, self.action, self.args, icon = BUTTONS[key]
        super().__init__(coordinator, entry, key, name, icon)

    @property
    def available(self):
        if not super().available:
            return False
        data = self.coordinator.data
        if self.action == "dismiss_keyring_prompt":
            return self.action in data.get("capabilities", [])
        if self.action in ("presentation_control", "close_presentation"):
            presentation = data.get("presentation")
            if not presentation:
                return False
            if (self.action == "presentation_control" and presentation.get("kind") == "slides"
                    and data.get("airplay") in ("video", "audio")):
                return False
        return True

    async def async_press(self):
        if not self.available:
            raise HomeAssistantError("Comando non disponibile nello stato corrente")
        await self.coordinator.async_command(self.action, dict(self.args))
