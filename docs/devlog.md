# Devlog

Questo documento raccoglie il lavoro svolto durante lo sviluppo di **Automated Incident Response Ban Engine**.  
Le attività sono riportate nell’ordine in cui sono state affrontate, mantenendo i problemi incontrati e le soluzioni adottate.

---

## Settimana 1 — 04/07/2026

Abbiamo iniziato leggendo la consegna, la proposta e la checklist, così da capire quali parti fossero davvero necessarie per l’MVP.

Abbiamo deciso di lavorare per piccoli blocchi: prima i modelli dati, poi il parser, i backend firewall e infine il motore principale.

In `models.py` abbiamo creato `validate_ip`, `LoginAttempt` e `BanDecision`. Per controllare gli indirizzi IPv4 e IPv6 abbiamo usato il modulo `ipaddress`, evitando regex troppo permissive.

Abbiamo aggiunto i test dei modelli per verificare IP validi e non validi, username opzionale e conversione dei dati in dizionario.

Durante l’avvio dei test abbiamo avuto problemi con gli import dalla cartella `src`. Abbiamo risolto aggiungendo `tests/conftest.py`, così da poter eseguire la suite dalla root con:

```bash
python -m pytest -q
```

Questa prima fase ci ha dato una base semplice da riutilizzare nel parser e, più avanti, nella persistenza JSON.

---

## Settimana 2 — 08/07/2026

Abbiamo sviluppato `SSHLogParser`, che riconosce nei log SSH i principali tentativi di accesso falliti.

Abbiamo gestito i casi `Failed password`, `Failed password for invalid user` e `Invalid user`, usando regex separate per mantenere il codice leggibile.

Quando una riga viene riconosciuta, il parser restituisce un oggetto `LoginAttempt`. Le righe non pertinenti vengono invece ignorate restituendo `None`.

Abbiamo aggiunto `parse_file()`, che legge il log riga per riga con `Path` e raccoglie solo gli eventi validi.

Poiché i log SSH non riportano normalmente l’anno, abbiamo usato l’anno corrente e previsto un fallback quando il timestamp non è convertibile.

Infine abbiamo creato i test del parser e il file `examples/auth.log`, utile sia per le verifiche automatiche sia per la futura demo in modalità dry-run.

---

## Settimana 3 — sviluppo progressivo dei backend firewall
Abbiamo inizialmente creato la classe astratta `FirewallBackend`, che definisce i metodi comuni `block_ip`, `unblock_ip` e `is_blocked`.

### Primo passaggio — backend dry-run

Abbiamo iniziato implementando `DryRunFirewallBackend`, la versione sicura del firewall usata per test e dimostrazioni.

Il backend conserva gli indirizzi bloccati in un `set`, aggiungendoli con `block_ip()` e rimuovendoli con `unblock_ip()`. Il metodo `is_blocked()` controlla semplicemente se l’indirizzo è presente nell’insieme.

Abbiamo aggiornato `firewall/__init__.py` per esportare la nuova classe e abbiamo scritto i primi test sulla gerarchia.

I test verificano che `FirewallBackend` non possa essere istanziata direttamente, che il backend dry-run sia una sua sottoclasse e che blocco e sblocco modifichino correttamente lo stato in memoria.

Nella prima versione avevamo anche duplicato per errore un test di sblocco. Il problema è stato eliminato nei passaggi successivi, mantenendo una sola verifica chiara.

### Secondo passaggio — backend Linux

Nel secondo passaggio abbiamo implementato `LinuxIptablesBackend`.

Per bloccare un indirizzo costruiamo il comando `iptables -A INPUT -s <ip> -j DROP`, mentre per rimuovere il blocco usiamo la stessa regola con l’opzione `-D`.

Per controllare se l’IP è già bloccato usiamo `iptables -C` e interpretiamo il codice di ritorno del processo: `0` significa che la regola esiste.

I comandi vengono passati a `subprocess.run()` come liste di argomenti, senza usare `shell=True`.

Nei test abbiamo sostituito `subprocess.run()` con un mock. In questo modo possiamo controllare i comandi costruiti senza richiedere privilegi amministrativi e senza modificare realmente il firewall della macchina.

Abbiamo inoltre aggiornato `firewall/__init__.py` per rendere disponibile anche `LinuxIptablesBackend`.

### Terzo passaggio — backend Windows e test polimorfico

Nel terzo passaggio abbiamo implementato `WindowsFirewallBackend` usando `netsh advfirewall`.

Ogni regola usa un nome prevedibile nel formato `BanEngine-<ip>`. Questo ci permette di aggiungere, cercare e rimuovere la stessa regola senza duplicare la logica.

`block_ip()` crea una regola in ingresso che blocca l’indirizzo remoto. `unblock_ip()` elimina la regola usando il suo nome, mentre `is_blocked()` controlla sia il codice di ritorno sia la presenza del nome della regola nell’output del comando.

Anche in questo caso abbiamo usato mock di `subprocess.run()` per verificare i comandi senza eseguire operazioni reali sul sistema.

Infine abbiamo aggiunto `apply_block()`, una funzione che riceve un generico `FirewallBackend` e chiama `block_ip()` senza conoscere la sottoclasse concreta.

Nel test polimorfico passiamo alla stessa funzione un backend dry-run, uno Linux e uno Windows. Per evitare interferenze tra i mock di `subprocess`, abbiamo usato `patch.object()` direttamente sui metodi delle istanze Linux e Windows.

Il backend dry-run esegue invece il comportamento reale in memoria. Questo ci permette di dimostrare che tutte le sottoclassi rispettano lo stesso contratto, pur avendo implementazioni differenti.


---

## Risultato della fase firewall

Alla fine di questa fase abbiamo ottenuto:

- una classe astratta comune `FirewallBackend`;
- un backend dry-run sicuro;
- un backend Linux basato su `iptables`;
- un backend Windows basato su `netsh advfirewall`;
- test specifici per ogni implementazione;
- un test che dimostra il polimorfismo reale;
- nessuna esecuzione di comandi firewall durante pytest.

Questa parte ci ha fatto capire meglio la differenza tra testare il comportamento comune della gerarchia e testare i dettagli interni di ogni backend.

Il prossimo passo sarà collegare parser e backend attraverso `IncidentResponseEngine`, aggiungendo soglia, finestra temporale e whitelist.