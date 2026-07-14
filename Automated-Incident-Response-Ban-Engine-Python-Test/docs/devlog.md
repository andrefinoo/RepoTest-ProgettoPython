# Devlog

Questo documento raccoglie il diario di bordo del gruppo durante lo sviluppo del progetto
**Automated Incident Response Ban Engine**.

Lo usiamo per tenere traccia del lavoro svolto, delle decisioni prese, dei problemi incontrati
e dei passi successivi. Le entry sono scritte in modo diretto, così da poterle collegare alla
storia Git e spiegare facilmente il percorso seguito durante l'orale.

---

## Entry

### Settimana 1 — 04/07/2026

Oggi abbiamo iniziato il lavoro sul progetto **Automated Incident Response Ban Engine**.

La prima attività è stata chiarire il perimetro del progetto e l’ordine di priorità dei materiali.
Abbiamo deciso di usare le lezioni Python come riferimento principale per lo stile del codice,
così da evitare soluzioni troppo complesse o difficili da spiegare durante l’orale.

Abbiamo poi verificato i file fondamentali del progetto: la proposta, la consegna, la checklist
operativa e il riferimento al repository GitHub. Questo ci ha permesso di avere una roadmap
più chiara e di capire da dove partire senza scrivere codice in modo disordinato.

Un punto importante della giornata è stato l’allineamento sul metodo di lavoro: procederemo
per piccoli blocchi, completando un modulo alla volta. L’obiettivo è avere codice semplice,
leggibile e difendibile.

Abbiamo iniziato anche a compilare `docs/uso-ia.md`, dichiarando in modo trasparente come
stiamo usando l’IA. Per ora l’abbiamo usata soprattutto come supporto alla pianificazione,
alla lettura dei requisiti, alla preparazione della documentazione iniziale e alla revisione delle
prime scelte tecniche.

Successivamente abbiamo preparato i comandi Git per configurare correttamente gli utenti
collegati al repository. Questo passaggio è importante perché la consegna richiede una
cronologia Git chiara, con commit riconducibili ai membri del gruppo.

Dopo la parte organizzativa, abbiamo iniziato il primo blocco tecnico del progetto: i modelli
dati del dominio.

Abbiamo lavorato su `src/ban_engine/models.py`, dove abbiamo introdotto:

- `validate_ip`, funzione che usa `ipaddress` per validare e normalizzare indirizzi IPv4 e IPv6;
- `LoginAttempt`, modello che rappresenta un tentativo di login fallito estratto da un log SSH;
- `BanDecision`, modello che rappresenta la decisione di bannare un IP quando supera la soglia di tentativi falliti.

Questi modelli sono volutamente semplici: contengono solo i dati necessari e alcune
validazioni di base. La scelta è coerente con il nostro obiettivo di mantenere il codice
leggibile e spiegabile. Inoltre, i metodi `to_dict()` ci serviranno più avanti per salvare dati in
JSON senza duplicare la logica di conversione in altri moduli.

Abbiamo poi preparato `tests/test_models.py`, con i primi test automatici sui modelli dati.
I test controllano la validazione degli IP, la gestione dello username vuoto, la conversione in
dizionario e alcuni casi non validi di `BanDecision`.

Un problema pratico incontrato è stato l’avvio dei test con `PYTHONPATH=src pytest -q`.
Il comando non funzionava in modo affidabile su tutte le macchine, quindi abbiamo scelto
una soluzione più stabile e coerente con lo scaffolding del corso: aggiungere `tests/conftest.py`.

Questo file aggiunge automaticamente `src/` al percorso di import durante l’esecuzione dei test.
In questo modo possiamo lanciare i test dalla root del progetto con:

```bash
python -m pytest -q 
```

### Settimana 2 — 08/07/2026

Oggi abbiamo iniziato la **Fase 2** del progetto, dedicata al parser dei log SSH.

Dopo aver completato i modelli dati, abbiamo lavorato su `src/ban_engine/parser.py`, creando la classe `SSHLogParser`. Questa classe ha il compito di leggere le righe di un file di log SSH e riconoscere solo quelle che rappresentano tentativi di login falliti.

Abbiamo deciso di partire da tre casi principali:

- `Failed password for root from ...`;
- `Failed password for invalid user ... from ...`;
- `Invalid user ... from ...`.

Per riconoscere queste righe abbiamo usato espressioni regolari, mantenendole abbastanza semplici e leggibili. L’obiettivo non era creare subito un parser universale per qualsiasi formato di log, ma coprire bene i casi utili per la demo e per l’MVP.

Quando una riga viene riconosciuta, il parser restituisce un oggetto `LoginAttempt`, già definito in `models.py`. In questo modo il parser non restituisce dizionari o stringhe sparse, ma un modello dati coerente con il resto del progetto.

Abbiamo aggiunto anche il metodo `parse_file()`, che legge un file riga per riga usando `Path` e restituisce solo i tentativi falliti trovati. Le righe non pertinenti vengono ignorate senza far bloccare il programma.

Un aspetto da gestire è stato il timestamp dei log SSH. I log classici contengono mese, giorno e ora, ma non l’anno. Per ora abbiamo scelto una soluzione semplice: aggiungere l’anno corrente durante il parsing. Se il timestamp non è convertibile, viene usato un fallback con `datetime.now()`. Questa scelta è temporanea ma spiegabile, e potrà essere documentata meglio nel manuale tecnico.

Abbiamo poi creato `tests/test_parser.py`, con test dedicati al parser. I test controllano che:

- una riga `Failed password` con utente esistente venga riconosciuta;
- una riga `Failed password for invalid user` venga riconosciuta;
- una riga `Invalid user` venga riconosciuta;
- una riga non pertinente venga ignorata;
- un IP non valido produca errore;
- `parse_file()` restituisca solo i tentativi falliti presenti nel file.

Infine abbiamo aggiunto `examples/auth.log`, un file di esempio utile sia per i test sia per la futura demo orale in modalità `dry-run`.

Questa fase ci ha permesso di collegare il primo modello dati (`LoginAttempt`) a una funzionalità reale del progetto. Il prossimo passo sarà iniziare a lavorare sull’engine, cioè sulla parte che raggruppa i tentativi per IP, applica soglia e finestra temporale, controlla la whitelist e decide quando produrre una `BanDecision`.

### Settimana 3 — [da compilare]

