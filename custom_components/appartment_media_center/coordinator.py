"""Poll the device and serialize reads/writes to avoid stale state races."""
import asyncio
from datetime import timedelta
import logging

from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApiError, AuthenticationError
from .const import DOMAIN


class MediaCenterCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api, device_id, entry=None):
        super().__init__(hass, logging.getLogger(__name__), name=DOMAIN,
                         update_interval=timedelta(seconds=5), config_entry=entry)
        self.api = api
        self.device_id = device_id
        self._lock = asyncio.Lock()

    def _check_identity(self, data):
        if data["device_id"] != self.device_id:
            raise ApiError("L'indirizzo ora identifica un dispositivo diverso")
        return data

    async def _async_update_data(self):
        async with self._lock:
            try:
                return self._check_identity(await self.api.status())
            except AuthenticationError as err:
                raise ConfigEntryAuthFailed("Token API non valido") from err
            except ApiError as err:
                raise UpdateFailed(str(err)) from err

    async def async_select_mode(self, mode):
        await self.async_command("set_mode", {"mode": mode})

    async def async_command(self, action, args):
        async with self._lock:
            try:
                self._check_identity(await self.api.status())
                data = self._check_identity(await self.api.command(action, args))
            except ApiError as err:
                raise HomeAssistantError(str(err)) from err
            self.async_set_updated_data(data)
