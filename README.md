# Appartment Media Center — custom component Home Assistant

Pacchetto unico per **Home Assistant Core/base**, senza Supervisor e senza HACS:

- configurazione da **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**;
- entità `select` creata dal componente, con cinque modalità italiane, inclusa **Riunione**;
- collegamento HTTPS autenticato all'API locale del media center Ubuntu;
- card Lovelace responsive inclusa, tema scuro, selezione lime e frecce;
- JavaScript servito e caricato automaticamente dal componente: **non occorre copiare nulla in `www` né registrare risorse**;
- aggiornamento dello stato ogni 5 secondi, gestione offline, riconfigurazione e autenticazione aggiornata.

Il pacchetto comprende il controllo HA e la card. Il player video/foto e AirPlay continuano a funzionare sul media center Ubuntu esistente.

## Installazione

[Scarica lo ZIP pronto per installazione](https://github.com/theappartment/ha-appartment-media-center/raw/refs/heads/main/appartment-media-center-ha-1.2.1.zip). Estrai il pacchetto e copia la cartella indicata sotto.

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
     entity.py
     number.py
     switch.py
     text.py
     button.py
     sensor.py
     binary_sensor.py
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

Non aggiungere una sezione `appartment_media_center:` a `configuration.yaml`: la connessione si configura da interfaccia. Per la sola integrazione HA non serve riavviare Ubuntu o il player; il nuovo comando portachiavi richiede anche l’aggiornamento backend descritto sotto.

## Correzione 1.2.1 — richiesta mostrata da GNOME Shell

Supporta anche la finestra del portachiavi mostrata da GNOME Shell, non elencata
come finestra GCR X11 separata. Riconosce il dialogo visibile e il suo pulsante
Cancel/Annulla tramite accessibilità; non legge il contenuto dei campi password.
Su GNOME Shell senza azioni accessibili usa la posizione attuale del pulsante
individuato, mai coordinate fisse. Verificato sulla finestra reale e attraverso
l'API autenticata usata da HA.

Se hai già la 1.2.0 e il servizio Ubuntu aggiornato in esecuzione, basta rieseguire
l'installatore Ubuntu della 1.2.1: i file di chiusura sono caricati a ogni pressione,
quindi non occorre riavviare Ubuntu, il player o Home Assistant.

## Novità 1.2.0 — Chiudi richiesta portachiavi

La card include **Chiudi richiesta portachiavi**, disponibile anche come entità `button`.
Annulla le finestre di autenticazione GCR visibili sul desktop Ubuntu X11, come il
messaggio “Default keyring is locked”. Non inserisce password, non sblocca o elimina
il portachiavi e non interrompe video, AirPlay o presentazioni. Se non ci sono
finestre GCR aperte, il comando termina senza modifiche. L'app che richiede lo
sblocco potrebbe ripresentare la finestra: questo è un comando di chiusura manuale.

**Aggiornare entrambi i lati:**

1. Sul media center Ubuntu applica l'aggiornamento descritto in
   [ubuntu/README.md](ubuntu/README.md), poi riavvia il servizio media center.
2. Sostituisci `custom_components/appartment_media_center` con la cartella dello ZIP
   1.2.0 e riavvia Home Assistant. Non eliminare l'integrazione esistente.
3. Ricarica completamente il browser. Se hai registrato manualmente la risorsa
   della card, aggiorna il suo URL a
   `/appartment_media_center/showreel-mode-card.js?v=1.2.1` (Modulo JavaScript).

Non occorrono modifiche al YAML. Il pulsante si trova in **Contenuti e stato**;
con `show_controls: false` non viene mostrato. Sul backend precedente rimane
non disponibile finché non viene installato l'aggiornamento Ubuntu.

## Novità 1.1.0 e aggiornamento dalla 1.0.0

Scarica lo ZIP 1.1.0, sostituisci **l'intera cartella** `custom_components/appartment_media_center`, riavvia Home Assistant e ricarica completamente il browser/app. Non eliminare l'integrazione: URL, token, certificato e ID del select restano validi. Le nuove entità compariranno sullo stesso dispositivo.

La configurazione minima della card rimane identica. Se nel YAML avevi scritto una lista `modes` con quattro elementi, rimuovila per usare le cinque modalità predefinite oppure aggiungi `option: Riunione`.

## Controlli inclusi

Il dispositivo espone 18 entità utilizzabili anche nelle automazioni:

| Tipo | Funzioni |
| --- | --- |
| Select | Automatico, Showreel video, Showreel foto, Schermo nero, Riunione |
| Numero | Volume sistema, 0–100% |
| Switch | Muto effettivo |
| Testo | Titolo della schermata Riunione, fino a 160 caratteri |
| 8 pulsanti | Libera schermo, aggiorna video, aggiorna foto, sincronizza contenuti, pagina precedente/successiva, chiudi presentazione, chiudi richiesta portachiavi |
| 3 sensori | Contenuto effettivo sullo schermo, stato AirPlay, ultima attività con progresso |
| 3 sensori diagnostici | Player pronto, ricevitore AirPlay pronto, presenza di problemi |

La card trova le entità collegate tramite il registro di HA, anche dopo una rinomina: non devi aggiungere altri ID al YAML. Se disabiliti un'entità, il relativo controllo non sarà disponibile. Il rilevamento può richiedere il successivo aggiornamento, entro circa 5 secondi.

- **Riunione** mostra titolo, logo e istruzioni AirPlay. Salvare il titolo modifica il messaggio ma non cambia automaticamente modalità.
- **Libera schermo** interrompe AirPlay, chiude la presentazione e torna a Riunione. La card chiede conferma prima di inviarlo; nelle automazioni `button.press` lo esegue direttamente.
- **Audio:** il volume agisce sull'uscita di sistema; non riattiva un filmato impostato muto dalla playlist. In Schermo nero, senza presentazione/AirPlay, il backend mantiene il muto anche se provi a spegnerlo.
- **Presentazioni:** precedente, successiva e chiusura agiscono sul PDF/Slides già aperto. I controlli sono disabilitati quando non c'è una presentazione; per Slides, anche i comandi pagina durante AirPlay. Per caricare/aprire PDF, Slides e immagini usa il collegamento al pannello incluso nella card, con l'autenticazione del pannello. Il browser deve poter raggiungere l'indirizzo locale del media center e fidarsi del suo certificato: il collegamento non passa tramite HA.
- **Attività:** aggiornamento feed e sincronizzazione avviano lavori in background. La card riporta avanzamento ed esito dal dispositivo; comando accettato non significa download completato. Una sincronizzazione completata può comunque lasciare una raccolta incompleta: verifica i dettagli nel pannello del media center.
- **Diagnostica:** il colore delle modalità segue il select; gli indicatori mostrano separatamente AirPlay e contenuto effettivo. I dati del dispositivo si aggiornano ogni 5 secondi.

Per mostrare soltanto le modalità, aggiungi `show_controls: false` alla card. I controlli estesi richiedono il select fornito da questa integrazione; con un select generico resta disponibile la selezione delle modalità.

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

L'ID è un esempio: dipende dal nome del dispositivo, da eventuali rinomine e da conflitti con entità esistenti. Le cinque modalità predefinite della card coincidono con quelle del select: non serve configurare `modes`.

| Card / select | Modalità API |
| --- | --- |
| Automatico | `auto` |
| Showreel video | `showreel` |
| Showreel foto | `photos` |
| Schermo nero | `black` |
| Riunione | `meeting` |

Il click chiama `select.select_option`; il componente invia `POST /api/v1/commands` con UUID, scadenza di 60 secondi e azione `set_mode`. Il verde segue lo stato restituito dal backend. Un esito HTTP 200 con comando rifiutato è trattato come errore.

In caso di schermata personalizzata, il select mostra temporaneamente `custom`; nessuno dei cinque pulsanti è verde e puoi usare la card per tornare a una modalità normale. Gli attributi dell'entità includono contenuto effettivo e stato AirPlay: AirPlay può essere attivo mentre la modalità selezionata resta uno showreel.

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
  - option: Riunione
    label: Riunione
    description: Schermata di benvenuto e condivisione AirPlay.
```

Sono ammesse da una a otto voci con `option` univoche; `label` e `description` sono facoltative. Il layout usa una colonna sotto 560 px di larghezza della card, due da 560 px e fino a cinque da 1100 px. Per il layout orizzontale desktop assegna spazio sufficiente, ad esempio una vista di tipo **Pannello** con la sola card.

## Manutenzione

- **URL/token/certificato cambiati:** menu ⋮ dell'integrazione → Riconfigura. Il dispositivo deve avere lo stesso `device_id`; per un dispositivo diverso aggiungi una nuova integrazione.
- **Non disponibile:** verifica rete, certificato e media center. La riconnessione avviene con il polling. Token non valido avvia il flusso di riautenticazione.
- **Custom element doesn't exist:** verifica che l'integrazione sia caricata e ricarica completamente la pagina. Il file è servito a `/appartment_media_center/showreel-mode-card.js?v=1.2.1`. Normalmente non aggiungerlo anche alle risorse Lovelace.
- **Aggiornamento:** sostituisci la cartella del componente, riavvia HA e ricarica il browser. La versione del modulo cambia insieme a `VERSION` in `const.py`.
- **Rimozione:** elimina l'integrazione da Dispositivi e servizi, rimuovi le card dalle dashboard, elimina la cartella e riavvia HA. Il file frontend viene mantenuto durante il processo HA anche se si scarica l'ultima voce, per non interrompere altre card che lo usano.

La cartella statica espone esclusivamente il JS, non i file Python o la configurazione. Il token viene conservato nella configurazione interna di HA e non viene passato al browser.

## Compatibilità e verifica

Versione minima prevista: **Home Assistant Core 2025.4**. La verifica automatizzata usa Core 2025.4.4 in un ambiente isolato e un server API simulato; non equivale a un'installazione sul tuo server HA. Non sono richiesti pacchetti Python aggiuntivi a runtime.

Verifiche eseguite: **17 test Python superati**, inclusi TLS, token errato, comandi rifiutati con HTTP 200, payload/scadenza, cinque modalità, modalità esterne, identità dispositivo, config flow, caricamento e scaricamento. La card inclusa supera **47 verifiche in Chromium**. Per la versione 1.2.0 sono stati verificati anche la disponibilità del nuovo pulsante, gli errori backend e l’installazione Ubuntu idempotente. Il comando è stato provato sul desktop Ubuntu reale con una finestra GCR di test: annullamento riuscito, seconda esecuzione senza finestre senza effetti. I test backend del nuovo comando e quelli API/controller passano (23 complessivi).

Per riprodurre i test, in un ambiente separato con Python 3.13:

```bash
python3.13 -m venv .venv
.venv/bin/pip install homeassistant==2025.4.4 pytest pytest-asyncio
.venv/bin/python -m pytest -q
```

Apri `tests/card.html` nel browser per le verifiche e la demo frontend con `hass` simulato. Il pacchetto non include token, password, chiavi private o certificati del dispositivo.

Riferimenti: [custom integrations](https://developers.home-assistant.io/docs/creating_integration_file_structure/), [config flow](https://developers.home-assistant.io/docs/config_entries_config_flow_handler/), [static paths](https://developers.home-assistant.io/blog/2024/06/18/async_register_static_paths/).
