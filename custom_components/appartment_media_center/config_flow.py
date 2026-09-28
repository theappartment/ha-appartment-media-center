"""UI setup, reconfiguration and reauthentication."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .api import ApiError, AuthenticationError, MediaCenterApi, make_ssl_context, normalize_url
from .const import DOMAIN


class MediaCenterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        return await self._form("user", user_input)

    async def async_step_reconfigure(self, user_input=None):
        return await self._form("reconfigure", user_input)

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        return await self._form("reauth_confirm", user_input)

    async def _form(self, step, user_input):
        entry = None
        if step != "user":
            entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        defaults = dict(entry.data) if entry else {"url": "https://appartment.local:8443"}
        errors = {}
        if user_input is not None:
            defaults.update(user_input)
            try:
                data = {
                    "url": normalize_url(user_input["url"]),
                    "token": user_input["token"].strip(),
                    "ca_file": user_input.get("ca_file", "").strip(),
                }
                if not data["token"]:
                    raise ValueError("Empty token")
                context = await self.hass.async_add_executor_job(make_ssl_context, data["ca_file"])
                api = MediaCenterApi(async_get_clientsession(self.hass), data["url"], data["token"], context)
                state = await api.status()
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except ApiError:
                errors["base"] = "cannot_connect"
            except (OSError, ValueError):
                errors["base"] = "invalid_config"
            else:
                if entry:
                    if state["device_id"] != entry.unique_id:
                        return self.async_abort(reason="wrong_device")
                    return self.async_update_reload_and_abort(entry, data_updates=data)
                await self.async_set_unique_id(state["device_id"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=state.get("receiver_name") or "Appartment Media Center", data=data)
        schema = vol.Schema({
            vol.Required("url", default=defaults.get("url", "")): str,
            vol.Required("token"): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
            vol.Optional("ca_file", default=defaults.get("ca_file", "")): str,
        })
        return self.async_show_form(step_id=step, data_schema=schema, errors=errors)
