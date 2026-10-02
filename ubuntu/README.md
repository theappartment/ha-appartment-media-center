# Aggiornamento Ubuntu: chiusura richiesta portachiavi

Questo aggiornamento aggiunge il comando autenticato `dismiss_keyring_prompt` al
backend media center esistente. Il solo aggiornamento di Home Assistant non basta.

## Installazione via SSH (utente che esegue il media center)

Estrai lo ZIP sul media center. Dalla cartella estratta:

```bash
python3 ubuntu/aggiorna-portachiavi.py --path "$HOME/media-center"
systemctl --user restart appartment-media-center.service
```

Il riavvio del servizio può interrompere la riproduzione/condivisione corrente:
eseguilo al termine della sessione e riseleziona la modalità desiderata in HA.
Lo script salva una copia dei file modificati in `media-center/.local-backups/keyring-*`,
controlla la struttura prima di scrivere e conserva le altre modifiche locali.
Può essere rieseguito: se il codice è già aggiornato non lo duplica.
Non copia configurazioni, token o certificati e non riavvia da solo il servizio.

Requisiti: backend con le modalità Riunione/presentazioni già installate, sessione
Ubuntu **X11**, `python-xlib` (già presente in requirements.lock del media center),
Python di sistema `/usr/bin/python3` con `python3-gi` e `gir1.2-atspi-2.0`,
servizio di accessibilità della sessione GNOME, GCR `/usr/libexec/gcr-prompter` oppure `/usr/lib/gcr/gcr-prompter` e variabili
`DISPLAY`/`XAUTHORITY` ereditate dal servizio utente della sessione grafica.
La sessione X11 è richiesta. Le richieste interne di GNOME Shell sono supportate
tramite AT-SPI (dialogo portachiavi/keyring e pulsante Cancel/Annulla).

Il comando controlla classe della finestra, eseguibile e proprietario del processo;
invia `WM_DELETE_WINDOW` solo alle finestre GCR visibili e attende che spariscano.
Per GNOME Shell usa l’azione accessibile del pulsante; se non esposta, un clic
nel centro dei suoi limiti correnti, dopo aver riconosciuto il dialogo portachiavi.
Non invia password e non termina il demone del portachiavi.
Il processo di controllo ha un timeout di 5 secondi. Un errore nella connessione X11
o nella chiusura viene restituito a HA; nessuna finestra trovata è un esito valido.
La chiusura non impedisce all'applicazione di chiedere di nuovo lo sblocco.

La risposta di `/api/v1/status` espone `capabilities: ["dismiss_keyring_prompt"]`.
La richiesta a `/api/v1/commands` usa il consueto token Bearer e l'envelope
`id`, `expires_at`, `action: "dismiss_keyring_prompt"`, `args: {}`.
Il risultato contiene `closed` (numero di finestre chiuse); argomenti aggiuntivi
sono rifiutati. ID duplicati non rieseguono la chiusura.

Protocollo finestra: [specifiche X11/EWMH](https://specifications.freedesktop.org/wm/latest-single/).

Dalla 1.2.0 già attiva è sufficiente rieseguire lo script di aggiornamento:
non serve riavviare il servizio perché gli helper vengono caricati a ogni comando.
