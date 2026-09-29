"""A real select entity, controlled by select.select_option."""
from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, MODES, CONTROL_TYPES


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([MediaCenterMode(hass.data[DOMAIN][entry.entry_id], entry)])


class MediaCenterMode(CoordinatorEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_name = "Modalità schermo"
    _attr_icon = "mdi:monitor"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._device_id = entry.unique_id
        self._panel_url = entry.data["url"]
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
        # Preserve custom image mode so the user can return to any normal mode.
        current = self.current_option
        return list(MODES) + ([current] if current and current not in MODES else [])

    @property
    def extra_state_attributes(self):
        attrs = {key: self.coordinator.data.get(key) for key in
                 ("requested_mode", "actual_content", "airplay", "receiver_ready", "browser_ready",
                  "errors")}
        presentation = self.coordinator.data.get("presentation")
        attrs["presentation"] = ({key: presentation.get(key) for key in ("kind", "name", "page", "pages")}
                                 if presentation else None)
        attrs["jobs"] = [{key: job.get(key) for key in ("id", "kind", "status", "progress", "error")}
                         for job in (self.coordinator.data.get("jobs") or [])[-10:]]
        attrs["panel_url"] = self._panel_url
        if self.hass:
            registry = er.async_get(self.hass)
            attrs["control_entities"] = {
                key: entity_id for key, platform in CONTROL_TYPES.items()
                if (entity_id := registry.async_get_entity_id(platform, DOMAIN, f"{self._device_id}_{key}"))
            }
        return attrs

    async def async_select_option(self, option):
        if option == self.current_option:
            return
        if option not in MODES:
            raise HomeAssistantError("Modalità non supportata")
        await self.coordinator.async_select_mode(MODES[option])
