"""Appartment Media Center, including its Lovelace frontend."""
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MediaCenterApi, make_ssl_context
from .const import CARD_URL, DOMAIN
from .coordinator import MediaCenterCoordinator

PLATFORMS = [Platform.SELECT]


async def async_setup(hass, config):
    """Publish only the bundled JS, never the integration directory."""
    await hass.http.async_register_static_paths([
        StaticPathConfig(CARD_URL.split("?")[0],
                         str(Path(__file__).parent / "frontend" / "showreel-mode-card.js"), True)
    ])
    add_extra_js_url(hass, CARD_URL)
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass, entry):
    try:
        context = await hass.async_add_executor_job(make_ssl_context, entry.data.get("ca_file", ""))
    except (OSError, ValueError) as err:
        raise ConfigEntryError("Certificato CA non leggibile o non valido") from err
    api = MediaCenterApi(async_get_clientsession(hass), entry.data["url"], entry.data["token"], context)
    coordinator = MediaCenterCoordinator(hass, api, entry.unique_id, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    if await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
        return True
    return False
