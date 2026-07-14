# Uso dell'intelligenza artificiale

Questo documento descrive in modo trasparente e progressivo come abbiamo utilizzato strumenti di intelligenza artificiale durante lo sviluppo del progetto **Automated Incident Response Ban Engine**.

L'IA è stata usata come supporto per comprendere requisiti, valutare alternative, individuare errori, preparare casi di test e revisionare bozze. Le decisioni finali, l'integrazione nel repository e la verifica del funzionamento restano responsabilità del gruppo.

> **Stato del documento:** progressivo. Prima della consegna ogni voce deve essere riletta e corretta dai componenti del gruppo, così che descriva soltanto attività realmente svolte e comprese.

## Strumenti utilizzati

- **Gemini:** supporto iniziale alla proposta, all'architettura generale e all'individuazione di possibili casi limite.
- **ChatGPT:** supporto alla lettura dei requisiti, alla pianificazione delle fasi, al debugging, alla revisione dei test e alla strutturazione della documentazione.
- **PyCharm e pytest:** non sono strumenti di IA, ma sono stati usati per verificare concretamente i suggerimenti ricevuti.

---

## 1. Analisi della consegna e pianificazione iniziale

**Periodo:** inizio progetto, fino al 04/07/2026  
**Strumenti:** Gemini e ChatGPT

### Cosa abbiamo chiesto

Abbiamo chiesto di:

- riassumere i vincoli della consegna;
- trasformare i requisiti in una checklist operativa;
- verificare che l'idea del Ban Engine fosse sufficientemente concreta;
- individuare una gerarchia di classi che rispettasse il requisito di ereditarietà significativa;
- proporre un ordine di sviluppo che mantenesse il progetto avviabile e testabile.

### Suggerimenti ricevuti

L'IA ha suggerito di:

- separare modelli, parser, engine, backend firewall, configurazione e persistenza;
- usare una classe base astratta `FirewallBackend`;
- creare implementazioni differenti per dry-run, Linux e Windows;
- procedere per fasi, completando ogni modulo insieme ai relativi test;
- mantenere il motore indipendente dai comandi specifici del sistema operativo.

### Cosa abbiamo accettato

Abbiamo accettato:

- la divisione del progetto in moduli con responsabilità separate;
- la gerarchia `FirewallBackend` con più sottoclassi;
- l'uso di un backend dry-run per test e demo sicure;
- l'ordine di lavoro: modelli, parser, backend, engine, JSON, CLI e documentazione.

### Cosa abbiamo modificato

Abbiamo adattato la struttura proposta ai nomi e ai file già presenti nel repository. La checklist è stata usata come guida, non come generazione automatica dell'intero progetto.

### Cosa abbiamo rifiutato o evitato

Abbiamo evitato:

- una struttura troppo complessa con pattern non necessari;
- dipendenze esterne non richieste;
- una soluzione in cui il motore controllasse direttamente il sistema operativo;
- modifiche massive al repository senza commit intermedi.

### Come abbiamo verificato

Abbiamo confrontato la pianificazione con la consegna ufficiale, la proposta e la struttura reale del repository.

---

## 2. Modelli dati e validazione degli indirizzi IP

**Periodo:** prima settimana di sviluppo  
**Strumento principale:** ChatGPT

### Cosa abbiamo chiesto

Abbiamo chiesto chiarimenti su:

- come modellare un tentativo di login fallito;
- quali campi inserire in `LoginAttempt`;
- come rappresentare una decisione di ban;
- come validare correttamente indirizzi IPv4 e IPv6;
- quali test minimi scrivere per i modelli.

### Suggerimenti ricevuti

L'IA ha proposto:

- l'uso di `dataclass`;
- una funzione `validate_ip()` basata su `ipaddress.ip_address()`;
- i modelli `LoginAttempt` e `BanDecision`;
- metodi `to_dict()` per preparare la futura serializzazione JSON;
- test per IP validi, IP non validi, username opzionale e conversione in dizionario.

### Cosa abbiamo accettato

Abbiamo accettato l'uso del modulo standard `ipaddress`, perché è più affidabile di una regex generica per validare gli indirizzi IP.

Abbiamo mantenuto i modelli semplici, con i soli campi necessari al dominio.

### Cosa abbiamo modificato

Abbiamo adattato nomi, type hint e validazioni allo stile del progetto e ai test effettivamente presenti.

### Cosa abbiamo rifiutato o evitato

Abbiamo evitato:

- regex dedicate alla validazione completa degli IP;
- modelli con troppi metodi o responsabilità;
- librerie esterne di validazione non necessarie.

### Come abbiamo verificato

Abbiamo eseguito `pytest` sui test dei modelli e controllato manualmente il comportamento con indirizzi IPv4, IPv6 e valori non validi.

---

## 3. Parser dei log SSH

**Periodo:** 08/07/2026  
**Strumenti:** Gemini e ChatGPT

### Cosa abbiamo chiesto

Abbiamo chiesto supporto per:

- riconoscere righe SSH con `Failed password`;
- distinguere utenti validi e `invalid user`;
- estrarre timestamp, username e indirizzo IP;
- ignorare righe non pertinenti senza generare errori;
- definire casi limite per i test del parser.

### Suggerimenti ricevuti

L'IA ha suggerito regex separate e leggibili per i principali formati di errore SSH, invece di un'unica espressione molto complessa.

È stato inoltre suggerito di restituire `None` per le righe non pertinenti e di trasformare le righe riconosciute in oggetti `LoginAttempt`.

### Cosa abbiamo accettato

Abbiamo accettato:

- l'uso di pattern distinti;
- la restituzione di `None` per le righe ignorate;
- la lettura del file riga per riga;
- la validazione dell'IP attraverso il modello già esistente.

### Cosa abbiamo modificato

Abbiamo limitato i pattern ai casi necessari per l'MVP e per i log di esempio, evitando di costruire un parser universale.

Per i timestamp privi di anno abbiamo adottato un fallback semplice e documentabile, da perfezionare se necessario.

### Cosa abbiamo rifiutato o evitato

Abbiamo evitato regex troppo compatte e difficili da spiegare all'orale.

Non abbiamo accettato pattern senza test o non collegati a esempi reali presenti nel progetto.

### Come abbiamo verificato

Abbiamo eseguito i test su:

- password fallita per utente esistente;
- password fallita per utente non valido;
- riga `Invalid user`;
- riga non pertinente;
- IP non valido;
- parsing di un file con righe miste.

---

## 4. Struttura del repository e problemi di import

**Periodo:** prima e seconda settimana  
**Strumento principale:** ChatGPT

### Cosa abbiamo chiesto

Abbiamo chiesto aiuto per:

- correggere l'errore `ModuleNotFoundError`;
- capire come eseguire i test con una struttura `src/`;
- riorganizzare il repository senza rompere gli import;
- scegliere tra `PYTHONPATH`, installazione editable e `conftest.py`.

### Suggerimenti ricevuti

Sono state proposte più alternative:

- impostare temporaneamente `PYTHONPATH=src`;
- installare il progetto in modalità editable;
- aggiungere `src/` al percorso dei test tramite `tests/conftest.py`.

### Cosa abbiamo accettato

Abbiamo scelto `tests/conftest.py` per rendere l'esecuzione dei test più stabile nelle macchine usate durante lo sviluppo.

### Cosa abbiamo modificato

La soluzione è stata adattata alla struttura effettiva della repository dopo il commit di riorganizzazione.

### Cosa abbiamo rifiutato o evitato

Abbiamo evitato import del tipo `RepoPython.src...`, perché dipendevano dal nome della cartella locale e non dal package reale.

Abbiamo anche evitato di riscrivere la cronologia Git con un rebase complesso durante questa fase, preferendo commit correttivi normali.

### Come abbiamo verificato

Abbiamo verificato che i test potessero essere avviati dalla root con:

```bash
python -m pytest -q
```

---

## 5. Backend firewall polimorfici

**Periodo:** 14/07/2026  
**Strumento principale:** ChatGPT  
**Commit di riferimento:** `1b10851` — `completa backend firewall polimorfici`

### Cosa abbiamo chiesto

Abbiamo chiesto supporto per:

- definire il contratto astratto dei backend;
- implementare un dry-run non distruttivo;
- costruire correttamente i comandi Linux e Windows;
- usare `subprocess.run()` in modo controllabile dai test;
- dimostrare il polimorfismo con pytest.

### Suggerimenti ricevuti

L'IA ha suggerito:

- `FirewallBackend` basata su `ABC`;
- i metodi astratti `block_ip()`, `unblock_ip()` e `is_blocked()`;
- `DryRunFirewallBackend` con un `set` di indirizzi bloccati;
- `LinuxIptablesBackend` con comandi `iptables`;
- `WindowsFirewallBackend` con comandi `netsh advfirewall`;
- comandi passati a `subprocess.run()` come liste, senza `shell=True`;
- mock di `subprocess.run()` nei test.

### Cosa abbiamo accettato

Abbiamo accettato:

- il contratto astratto comune;
- le tre implementazioni concrete;
- l'uso del `set` nel backend dry-run;
- l'uso di `check=True` nelle operazioni di modifica;
- la simulazione delle chiamate esterne tramite mock;
- la separazione tra test del comando e test del polimorfismo.

### Cosa abbiamo modificato

Abbiamo adattato i comandi alle implementazioni effettive e ai nomi delle regole Windows.

Il test polimorfico è stato modificato dopo aver scoperto un'interferenza tra due patch applicate contemporaneamente a `subprocess.run()`.

### Cosa abbiamo rifiutato o evitato

Abbiamo evitato:

- l'esecuzione di comandi firewall reali durante i test;
- l'uso di `shell=True`;
- condizioni Linux/Windows dentro il motore;
- un test polimorfico che verificasse contemporaneamente troppi dettagli interni.

### Come abbiamo verificato

Abbiamo:

- controllato i comandi costruiti tramite mock;
- verificato blocco, sblocco e controllo dello stato nel dry-run;
- verificato che una funzione che riceve un generico `FirewallBackend` possa usare backend differenti;
- eseguito la suite pytest dopo le correzioni.

---

## 6. Debugging del test polimorfico

**Periodo:** 14/07/2026  
**Strumento:** ChatGPT

### Problema sottoposto all'IA

Il test `test_block_ip_is_polymorphic` falliva perché il mock associato al backend Linux non risultava chiamato una volta come previsto.

### Analisi suggerita

L'IA ha evidenziato che i moduli Linux e Windows importano lo stesso modulo Python `subprocess`. Applicare contemporaneamente due patch a `subprocess.run` poteva quindi creare interferenze tra i mock.

### Soluzione accettata

Abbiamo separato gli obiettivi dei test:

- i test specifici dei backend verificano i comandi `subprocess`;
- il test polimorfico verifica soltanto che la stessa funzione possa chiamare `block_ip()` su oggetti concreti differenti.

Per quest'ultimo abbiamo usato `patch.object()` sui metodi delle singole istanze.

### Cosa abbiamo modificato rispetto al suggerimento

La correzione è stata inserita solo dopo aver letto il traceback e verificato che il problema fosse coerente con il comportamento dei mock.

### Cosa abbiamo rifiutato o evitato

Non abbiamo eliminato il test e non abbiamo indebolito le asserzioni dei test specifici dei backend soltanto per ottenere una suite verde.

### Come abbiamo verificato

Abbiamo rilanciato pytest e controllato che:

- il dry-run modificasse realmente il proprio stato in memoria;
- i metodi Linux e Windows fossero invocati una sola volta;
- i test specifici continuassero a controllare i comandi corretti.

---

## 7. Supporto alla documentazione

**Periodo:** progressivo  
**Strumento:** ChatGPT

### Cosa abbiamo chiesto

Abbiamo chiesto supporto per organizzare e revisionare:

- `docs/devlog.md`;
- `docs/scelte.md`;
- `docs/uso-ia.md`.

### Tipo di supporto ricevuto

L'IA ha fornito:

- strutture di sezione;
- riepiloghi tecnici basati sul lavoro svolto;
- proposte di formulazione;
- controlli di coerenza tra documentazione, checklist e commit;
- segnalazioni su parti troppo generiche o non conformi alla consegna.

### Cosa abbiamo accettato

Abbiamo usato le bozze come canovaccio per non dimenticare:

- problemi incontrati;
- alternative considerate;
- modifiche ai suggerimenti;
- test usati per verificare il codice;
- collegamenti tra decisioni e commit.

### Cosa deve essere modificato dal gruppo

Prima della consegna, il gruppo deve:

- rileggere ogni testo;
- riscrivere le parti che non rispecchiano il proprio modo di esprimersi;
- eliminare affermazioni non verificabili;
- aggiungere dettagli personali sulle difficoltà realmente incontrate;
- assicurarsi di saper spiegare ogni frase all'orale.

### Cosa non è stato delegato

L'IA non ha:

- eseguito autonomamente commit o push;
- scelto quali modifiche integrare senza approvazione;
- eseguito comandi firewall reali;
- sostituito la verifica con pytest;
- assunto la responsabilità delle decisioni finali.

---

## 8. Criterio generale seguito

Per ogni suggerimento dell'IA abbiamo cercato di seguire questo processo:

1. leggere e comprendere la proposta;
2. confrontarla con consegna, lezioni e codice esistente;
3. adattarla alla struttura reale del progetto;
4. verificare il risultato con test o esecuzione controllata;
5. accettare solo ciò che sappiamo spiegare;
6. documentare modifiche e alternative scartate.

Le prossime voci verranno aggiunte durante lo sviluppo di:

- `IncidentResponseEngine`;
- configurazione JSON;
- persistenza dello stato;
- CLI;
- manuale utente e manuale tecnico.