# Appartment Media Center — custom component Home Assistant

Pacchetto unico per **Home Assistant Core/base**, senza Supervisor e senza HACS:

- configurazione da **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**;
- entità `select` creata dal componente, con le quattro modalità italiane;
- collegamento HTTPS autenticato all'API locale del media center Ubuntu;
- card Lovelace responsive inclusa, tema scuro, selezione lime e frecce;
- JavaScript servito e caricato automaticamente dal componente: **non occorre copiare nulla in `www` né registrare risorse**;
- aggiornamento dello stato ogni 5 secondi, gestione offline, riconfigurazione e autenticazione aggiornata.

Il pacchetto comprende il controllo HA e la card. Il player video/foto e AirPlay continuano a funzionare sul media center Ubuntu esistente.

## Installazione

[Scarica lo ZIP pronto per installazione](https://github.com/theappartment/ha-appartment-media-center/raw/refs/heads/main/appartment-media-center-ha-1.0.0.zip). Estrai il pacchetto e copia la cartella indicata sotto.

1. Copia la cartella `custom_components/appartment_media_center` nella directory di configurazione di Home Assistant:

   ```text
   /config/custom_components/appartment_media_center/
     __init__.py
     manifest.json
     api.py
     config_flow.py
     const.py
     coordinator.py
     select.py
     strings.json
     translations/it.json
     frontend/showreel-mode-card.js
   ```

   `/config` è la directory con `configuration.yaml`; su Core può essere `~/.homeassistant` o il percorso passato a `hass --config`.

2. Se avevi installato la card standalone, rimuovi la sua vecchia risorsa `/local/showreel-mode-card/…` da Lovelace. Le card già configurate restano compatibili. Ricarica completamente il browser dopo il riavvio per eliminare il vecchio modulo dalla memoria.
3. Riavvia Home Assistant.
4. Aggiungi l'integrazione **Appartment Media Center** da Dispositivi e servizi.
5. Inserisci URL, token API locale e, se necessario, percorso del certificato pubblico PEM.
6. Ricarica completamente la pagina/app Home Assistant: il modulo della card viene registrato al caricamento dell'integrazione.

Non aggiungere una sezione `appartment_media_center:` a `configuration.yaml`: la connessione si configura da interfaccia. Nessun riavvio di Ubuntu o del player è necessario.

## Collegamento e certificato HTTPS

URL di esempio: `https://appartment.local:8443` oppure `https://192.168.1.100:8443`, se presenti nel certificato. Usa un indirizzo raggiungibile **dal server Home Assistant**, senza `/api/v1`, query o credenziali nell'URL.

Il token API locale è la proprietà `api_token` del file `~/.local/share/appartment-media-center/credentials.json` sul media center. Non è la password `admin` né il token cloud. Inseriscilo solo nel modulo di configurazione HA. Non copiarlo nella card YAML, negli screenshot o nei log.

Per il certificato autofirmato dell'installazione attuale:

1. Copia **il solo certificato pubblico** `~/.local/share/appartment-media-center/tls.crt` dal media center al server HA, per esempio `/config/certs/appartment.crt`.
2. Inserisci `/config/certs/appartment.crt` nel campo **File CA/certificato PEM**.
3. Il nome/IP nell'URL deve corrispondere ai nomi del certificato, che deve essere valido e non scaduto.

Non copiare `tls.key`. La verifica TLS resta abilitata. Con un certificato emesso da una CA già riconosciuta puoi lasciare vuoto il campo PEM. Quando rinnovi un certificato autofirmato, aggiorna anche la copia fidata su HA e ricarica l'integrazione.

## Aggiungi la card

Apri il dispositivo creato dall'integrazione e copia l'ID della sua entità select. Poi aggiungi una card **Manuale**:

```yaml
type: custom:showreel-mode-card
entity: select.appartment_ufficio_modalita_schermo
```

L'ID è un esempio: dipende dal nome del dispositivo, da eventuali rinomine e da conflitti con entità esistenti. Le quattro modalità predefinite della card coincidono con quelle del select: non serve configurare `modes`.

| Card / select | Modalità API |
| --- | --- |
| Automatico | `auto` |
| Showreel video | `showreel` |
| Showreel foto | `photos` |
| Schermo nero | `black` |

Il click chiama `select.select_option`; il componente invia `POST /api/v1/commands` con UUID, scadenza di 60 secondi e azione `set_mode`. Il verde segue lo stato restituito dal backend. Un esito HTTP 200 con comando rifiutato è trattato come errore.

In caso di modalità esterna `meeting` o `custom`, il select mostra temporaneamente quel valore, nessuno dei quattro pulsanti è verde e puoi usare la card per tornare a una delle quattro modalità. Gli attributi dell'entità includono contenuto effettivo e stato AirPlay: AirPlay può essere attivo mentre la modalità selezionata resta uno showreel.

### Personalizzazione YAML

```yaml
type: custom:showreel-mode-card
entity: select.appartment_ufficio_modalita_schermo
modes:
  - option: Automatico
    label: Automatico
    description: Ultimo showreel scelto in attesa. AirPlay quando ti colleghi.
  - option: Showreel video
    label: Showreel video
    description: Video in loop. AirPlay sempre disponibile.
  - option: Showreel foto
    label: Showreel foto
    description: Gli shooting in loop. AirPlay sempre disponibile.
  - option: Schermo nero
    label: Schermo nero
    description: Standby silenzioso. AirPlay sempre disponibile.
```

Sono richieste quattro voci con `option` univoche; `label` e `description` sono facoltative. Il layout usa una colonna sotto 560 px di larghezza della card, due da 560 px e quattro da 1100 px. Per il layout orizzontale desktop assegna spazio sufficiente, ad esempio una vista di tipo **Pannello** con la sola card.

## Manutenzione

- **URL/token/certificato cambiati:** menu ⋮ dell'integrazione → Riconfigura. Il dispositivo deve avere lo stesso `device_id`; per un dispositivo diverso aggiungi una nuova integrazione.
- **Non disponibile:** verifica rete, certificato e media center. La riconnessione avviene con il polling. Token non valido avvia il flusso di riautenticazione.
- **Custom element doesn't exist:** verifica che l'integrazione sia caricata e ricarica completamente la pagina. Il file è servito a `/appartment_media_center/showreel-mode-card.js?v=1.0.0`. Normalmente non aggiungerlo anche alle risorse Lovelace.
- **Aggiornamento:** sostituisci la cartella del componente, riavvia HA e ricarica il browser. La versione del modulo cambia insieme a `VERSION` in `const.py`.
- **Rimozione:** elimina l'integrazione da Dispositivi e servizi, rimuovi le card dalle dashboard, elimina la cartella e riavvia HA. Il file frontend viene mantenuto durante il processo HA anche se si scarica l'ultima voce, per non interrompere altre card che lo usano.

La cartella statica espone esclusivamente il JS, non i file Python o la configurazione. Il token viene conservato nella configurazione interna di HA e non viene passato al browser.

## Compatibilità e verifica

Versione minima prevista: **Home Assistant Core 2025.4**. La verifica automatizzata usa Core 2025.4.4 in un ambiente isolato e un server API simulato; non equivale a un'installazione sul tuo server HA. Non sono richiesti pacchetti Python aggiuntivi a runtime.

Verifiche eseguite: **12 test Python superati**, inclusi TLS, token errato, comandi rifiutati con HTTP 200, payload/scadenza, quattro modalità, modalità esterne, identità dispositivo, config flow, caricamento e scaricamento. La card inclusa supera **26 verifiche in Chromium**. Eseguita inoltre una lettura dello stato dal media center reale con token e certificato TLS verificato, senza inviare comandi al dispositivo.

Per riprodurre i test, in un ambiente separato con Python 3.13:

```bash
python3.13 -m venv .venv
.venv/bin/pip install homeassistant==2025.4.4 pytest pytest-asyncio
.venv/bin/python -m pytest -q
```

Apri `tests/card.html` nel browser per le verifiche e la demo frontend con `hass` simulato. Il pacchetto non include token, password, chiavi private o certificati del dispositivo.

Riferimenti: [custom integrations](https://developers.home-assistant.io/docs/creating_integration_file_structure/), [config flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/), [static paths](https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/).
