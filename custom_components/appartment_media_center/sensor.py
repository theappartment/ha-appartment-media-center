"""Actual output, AirPlay, and background task status."""
from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN
from .entity import MediaCenterEntity

SENSORS = {"actual_content": ("Contenuto sullo schermo", "mdi:monitor"),
           "airplay": ("Stato AirPlay", "mdi:cast"),
           "job": ("Ultima attività", "mdi:progress-clock")}


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([MediaCenterSensor(hass.data[DOMAIN][entry.entry_id], entry, key)
                        for key in SENSORS])


class MediaCenterSensor(MediaCenterEntity, SensorEntity):
    def __init__(self, coordinator, entry, key):
        super().__init__(coordinator, entry, key, *SENSORS[key])
        self.key = key

    @property
    def native_value(self):
        if self.key == "job":
            jobs = self.coordinator.data.get("jobs") or []
            return jobs[-1].get("status") if jobs else "idle"
        return self.coordinator.data.get(self.key)

    @property
    def extra_state_attributes(self):
        if self.key != "job":
            return None
        jobs = self.coordinator.data.get("jobs") or []
        return {key: jobs[-1].get(key) for key in ("id", "kind", "progress", "error")} if jobs else {}
