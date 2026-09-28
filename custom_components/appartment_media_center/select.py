"""A real select entity, controlled by select.select_option."""
from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODES


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([MediaCenterMode(hass.data[DOMAIN][entry.entry_id], entry)])


class MediaCenterMode(CoordinatorEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_name = "Modalità schermo"
    _attr_icon = "mdi:monitor"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id}_screen_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)}, name=entry.title,
            manufacturer="Appartment", model="Media Center",
            configuration_url=entry.data["url"],
        )

    @property
    def current_option(self):
        mode = self.coordinator.data.get("requested_mode")
        return next((label for label, value in MODES.items() if value == mode), mode)

    @property
    def options(self):
        # Preserve external modes (meeting/custom) so the four buttons remain
        # available and can return the device to a normal showreel mode.
        current = self.current_option
        return list(MODES) + ([current] if current and current not in MODES else [])

    @property
    def extra_state_attributes(self):
        return {key: self.coordinator.data.get(key) for key in
                ("requested_mode", "actual_content", "airplay", "receiver_ready", "browser_ready")}

    async def async_select_option(self, option):
        if option == self.current_option:
            return
        if option not in MODES:
            raise HomeAssistantError("Modalità non supportata")
        await self.coordinator.async_select_mode(MODES[option])
