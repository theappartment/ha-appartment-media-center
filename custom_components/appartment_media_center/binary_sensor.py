"""Operational health sensors."""
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.const import EntityCategory
from .const import DOMAIN
from .entity import MediaCenterEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([MediaCenterHealth(hass.data[DOMAIN][entry.entry_id], entry, key, name)
                        for key, name in (("receiver_ready", "Ricevitore AirPlay pronto"),
                                          ("browser_ready", "Player pronto"), ("errors", "Problemi dispositivo"))])


class MediaCenterHealth(MediaCenterEntity, BinarySensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry, key, name):
        super().__init__(coordinator, entry, key, name, "mdi:monitor-dashboard")
        self.key = key
        self._attr_device_class = (BinarySensorDeviceClass.PROBLEM if key == "errors"
                                   else BinarySensorDeviceClass.RUNNING)

    @property
    def is_on(self):
        return bool(self.coordinator.data.get(self.key))
