"""Tests against actual Home Assistant classes and an isolated HTTPS device."""
from datetime import datetime, timedelta, timezone
import ipaddress
import ssl
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
from aiohttp import web
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntries, ConfigEntryState
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.appartment_media_center import async_setup, async_setup_entry, async_unload_entry
from custom_components.appartment_media_center.api import (
    ApiError, AuthenticationError, MediaCenterApi, make_ssl_context, normalize_url,
)
from custom_components.appartment_media_center.const import CARD_URL, MODES
from custom_components.appartment_media_center.coordinator import MediaCenterCoordinator
from custom_components.appartment_media_center.select import MediaCenterMode
from custom_components.appartment_media_center.config_flow import MediaCenterConfigFlow


@pytest.fixture
async def device(tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc) - timedelta(minutes=1))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), False)
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), True)
            .sign(key, hashes.SHA256()))
    cert_file, key_file = tmp_path / "cert.pem", tmp_path / "key.pem"
    cert_file.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_file.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_file, key_file)
    state = {"device_id": "test-device", "receiver_name": "Studio", "requested_mode": "auto", "airplay": "idle"}
    control = {"result": "applied", "calls": []}

    async def handler(request):
        if request.headers.get("Authorization") != "Bearer test-token":
            return web.json_response({}, status=401)
        if request.method == "GET":
            return web.json_response(state)
        body = await request.json()
        control["calls"].append(body)
        if control["result"] == "applied":
            state["requested_mode"] = body["args"]["mode"]
        return web.json_response({"status": control["result"], "state": state})

    app = web.Application()
    app.router.add_get('/api/v1/status', handler)
    app.router.add_post('/api/v1/commands', handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 0, ssl_context=context)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    async with aiohttp.ClientSession() as session:
        api = MediaCenterApi(session, f'https://127.0.0.1:{port}', 'test-token', make_ssl_context(str(cert_file)))
        yield api, state, control, str(cert_file)
    await runner.cleanup()


@pytest.fixture
async def hass(tmp_path):
    instance = HomeAssistant(str(tmp_path))
    instance.config_entries = ConfigEntries(instance, {})
    yield instance
    await instance.async_stop(force=True)


@pytest.mark.parametrize('url', ['http://localhost', 'https://user:pass@localhost', 'https://localhost/api/v1', 'https://localhost?token=x', 'https://localhost:bad'])
def test_invalid_urls(url):
    with pytest.raises(ValueError):
        normalize_url(url)


async def test_https_api(device):
    api, state, control, _ = device
    assert (await api.status())['requested_mode'] == 'auto'
    for mode in MODES.values():
        assert (await api.set_mode(mode))['requested_mode'] == mode
    calls = control['calls']
    assert len({call['id'] for call in calls}) == 4
    for call in calls:
        assert call['action'] == 'set_mode'
        remaining = datetime.fromisoformat(call['expires_at']) - datetime.now(timezone.utc)
        assert 0 < remaining.total_seconds() <= 60


async def test_auth_rejection_and_tls(device):
    api, _, control, _ = device
    api._token = 'incorrect'
    with pytest.raises(AuthenticationError):
        await api.status()
    api._token = 'test-token'
    for result in ['rejected', 'failed', 'expired', 'conflict', 'interrupted']:
        control['result'] = result
        with pytest.raises(ApiError):
            await api.set_mode('black')
    api._ssl = make_ssl_context()
    with pytest.raises(ApiError):
        await api.status()


async def test_select_state_and_external_modes(hass, device):
    api, state, control, _ = device
    coordinator = MediaCenterCoordinator(hass, api, 'test-device')
    coordinator.async_set_updated_data(await coordinator._async_update_data())
    entry = SimpleNamespace(unique_id='test-device', title='Studio', data={'url': api.url})
    select = MediaCenterMode(coordinator, entry)
    assert select.current_option == 'Automatico'
    for label, mode in MODES.items():
        await select.async_select_option(label)
        assert state['requested_mode'] == mode
        assert select.current_option == label
    for mode in ['meeting', 'custom']:
        state['requested_mode'] = mode
        coordinator.async_set_updated_data(await api.status())
        assert select.current_option == mode and mode in select.options
        await select.async_select_option('Automatico')
        assert select.current_option == 'Automatico'
        assert select.options == list(MODES)
    control['result'] = 'rejected'
    with pytest.raises(HomeAssistantError):
        await select.async_select_option('Schermo nero')
    assert select.current_option == 'Automatico'
    state['device_id'] = 'different-device'
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    calls = len(control['calls'])
    with pytest.raises(HomeAssistantError):
        await select.async_select_option('Schermo nero')
    assert len(control['calls']) == calls
    api._token = 'incorrect'
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_frontend_registration(hass):
    hass.http = SimpleNamespace(async_register_static_paths=AsyncMock())
    with patch('custom_components.appartment_media_center.add_extra_js_url') as add:
        assert await async_setup(hass, {})
        add.assert_called_once_with(hass, CARD_URL)
    config = hass.http.async_register_static_paths.call_args.args[0][0]
    assert config.url_path == CARD_URL.split('?')[0]
    assert config.path.endswith('/frontend/showreel-mode-card.js')


async def test_config_flow(hass, device):
    api, state, _, ca_file = device
    flow = MediaCenterConfigFlow()
    flow.hass = hass
    flow.context = {}
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = lambda: None
    with patch('custom_components.appartment_media_center.config_flow.async_get_clientsession', return_value=api.session):
        result = await flow.async_step_user({'url': api.url, 'token': 'incorrect', 'ca_file': ca_file})
        assert result['errors']['base'] == 'invalid_auth'
        result = await flow.async_step_user({'url': api.url, 'token': 'test-token', 'ca_file': ca_file})
        assert result['type'] == 'create_entry'
        assert result['title'] == 'Studio'
        assert result['data']['url'] == api.url
        flow.async_set_unique_id.assert_awaited_once_with('test-device')


async def test_setup_unload_and_reload(hass, device):
    api, _, _, ca_file = device
    hass.data['appartment_media_center'] = {}
    entry = SimpleNamespace(entry_id='test-entry', unique_id='test-device',
                            state=ConfigEntryState.SETUP_IN_PROGRESS, async_on_unload=Mock(), pref_disable_polling=False,
                            data={'url': api.url, 'token': 'test-token', 'ca_file': ca_file})
    with (patch('custom_components.appartment_media_center.async_get_clientsession', return_value=api.session),
          patch.object(hass.config_entries, 'async_forward_entry_setups', new=AsyncMock()) as forward,
          patch.object(hass.config_entries, 'async_unload_platforms', new=AsyncMock(return_value=True))):
        for _ in range(2):
            assert await async_setup_entry(hass, entry)
            assert hass.data['appartment_media_center'][entry.entry_id].data['requested_mode'] == 'auto'
            assert await async_unload_entry(hass, entry)
            assert entry.entry_id not in hass.data['appartment_media_center']
        assert forward.await_count == 2


async def test_reconfigure_identity(hass, device):
    api, state, _, ca_file = device
    entry = SimpleNamespace(entry_id='test-entry', unique_id='test-device',
                            data={'url': api.url, 'token': 'test-token', 'ca_file': ca_file})
    flow = MediaCenterConfigFlow()
    flow.hass = hass
    flow.context = {'entry_id': entry.entry_id}
    with (patch.object(hass.config_entries, 'async_get_entry', return_value=entry),
          patch('custom_components.appartment_media_center.config_flow.async_get_clientsession', return_value=api.session),
          patch.object(flow, 'async_update_reload_and_abort', return_value={'type': 'abort', 'reason': 'reconfigure_successful'}) as update):
        result = await flow.async_step_reconfigure(entry.data)
        assert result['reason'] == 'reconfigure_successful'
        update.assert_called_once()
        state['device_id'] = 'other-device'
        result = await flow.async_step_reconfigure(entry.data)
        assert result['reason'] == 'wrong_device'
