## Aggiornamento sessione — 04/07/2026

### Attività svolte con il supporto dell'IA

Durante questa sessione abbiamo usato ChatGPT come supporto operativo per avviare il progetto in modo ordinato.

In particolare, abbiamo chiesto supporto per:

- verificare la presenza dei file di progetto e del riferimento al repository GitHub;
- confermare la gerarchia dei materiali da seguire;
- iniziare la compilazione del file `docs/uso-ia.md`;
- preparare una prima bozza del `docs/devlog.md`;
- preparare i comandi Git per configurare correttamente gli utenti locali collegati al repository;
- individuare il primo blocco tecnico da sviluppare, cioè i modelli dati `LoginAttempt` e `BanDecision`.

### Come abbiamo usato l'IA

L'IA è stata usata come tutor e supporto alla pianificazione, non come risolutore automatico del progetto.

Le risposte ricevute sono state usate per chiarire il flusso di lavoro e per trasformare i requisiti della consegna in attività più concrete. In questa fase l'obiettivo non era produrre subito tutto il codice, ma capire come procedere senza creare una struttura troppo complessa.

Abbiamo usato l'IA anche per ottenere bozze iniziali di documentazione. Queste bozze non vengono considerate definitive: devono ancora essere riviste, adattate e approvate dal gruppo prima di essere inserite nel repository.

### Cosa abbiamo accettato

Abbiamo accettato:

- l'idea di procedere per fasi, partendo dalla struttura del progetto e poi dai modelli dati;
- l'impostazione del file `docs/uso-ia.md` con sezioni dedicate a richieste, output, parti accettate, parti modificate e parti rifiutate;
- una bozza di devlog, da rivedere prima del commit;
- i comandi Git per configurare `user.name` e `user.email` sui computer dei membri del gruppo;
- il suggerimento di iniziare dai modelli dati perché sono una base comune per parser, engine, persistenza e test.

### Cosa abbiamo modificato

Abbiamo considerato le risposte dell'IA come materiale di partenza.

Abbiamo considerato da modificare o adattare:

- il testo della documentazione;
- le descrizioni del devlog, per fare in modo che raccontino quello che abbiamo fatto;
- eventuali nomi, esempi o dettagli tecnici non perfettamente coerenti con il repository;
- il codice proposto, se durante l'implementazione risulta troppo complesso o non allineato al livello delle lezioni.

### Cosa abbiamo rifiutato o non applicato

Non abbiamo accettato:

- la generazione completa dell'intero progetto in un'unica soluzione;
- l'idea di scrivere codice avanzato non ancora spiegabile dal gruppo;
- l'uso dell'IA per sostituire la nostra comprensione del progetto;
- l'inserimento automatico di documentazione non riletta;

### Codice generato o suggerito

In questa sessione l'IA ha suggerito una possibile implementazione iniziale per:

- `src/ban_engine/models.py`;
- `tests/test_models.py`.

Questa parte non è ancora considerata automaticamente definitiva. Prima di inserirla nel progetto, bisognerà leggerla, capirla, provarla con `pytest` e modificarla dove necessario.

### Impatto reale sul progetto

L'impatto principale dell'IA oggi è stato organizzativo e documentale.

Abbiamo chiarito:

- quali file seguire;
- come documentare l'uso dell'IA;
- come scrivere un devlog coerente;
- come configurare gli utenti Git;
- quale modulo sviluppare per primo.

Non sono ancora state completate funzionalità operative del motore di ban. Il progetto è ancora nella fase iniziale di setup, documentazione e pianificazione tecnica.

### Verifica da parte del gruppo

Prima del commit, il gruppo controllerà che:

- il testo inserito in `docs/uso-ia.md` rappresenti davvero l'uso fatto dell'IA;
- scrittura del devlog con le attività effettivamente svolte;
- eventuale codice suggerito sia compreso e testato;

---

## Aggiornamento sessione — 08/07/2026

### Attività svolte con il supporto dell'IA

Durante questa sessione abbiamo usato ChatGPT per proseguire con la **Fase 2** del progetto, cioè lo sviluppo del parser dei log SSH.

In particolare, abbiamo chiesto supporto per:

- ripassare gli obiettivi della Fase 2 prima di iniziare a scrivere codice;
- definire la responsabilità della classe `SSHLogParser`;
- individuare i principali pattern di log SSH da riconoscere;
- preparare una possibile implementazione di `src/ban_engine/parser.py`;
- preparare i test automatici in `tests/test_parser.py`;
- creare un file di esempio `examples/auth.log`;
- aggiornare questo documento per dichiarare l’uso dell’IA nella fase del parser.

### Come abbiamo usato l'IA

L'IA è stata usata come supporto tecnico e didattico.

Prima di scrivere il codice, abbiamo chiesto di chiarire cosa dovesse fare il parser e quali casi dovesse gestire. Questo ci ha aiutato a non partire subito con una soluzione troppo grande o difficile da controllare.

Successivamente abbiamo usato l'IA per ottenere una bozza di codice per `SSHLogParser` e una bozza di test. Il codice è stato trattato come punto di partenza: prima di considerarlo valido, deve essere letto, compreso, inserito nel progetto e verificato con `pytest`.

Abbiamo aggiornato il parser per gestire log SSH realistici con prefisso numerico opzionale, come `[01]`, e per riconoscere anche i tentativi falliti tramite `Failed publickey`.

Le righe di login riuscito o di semplice connessione/disconnessione vengono ignorate.

### Cosa abbiamo accettato

Abbiamo accettato:

- l’idea di creare una classe `SSHLogParser` dedicata al parsing dei log SSH;
- la scelta di far restituire al parser un oggetto `LoginAttempt` quando una riga rappresenta un tentativo fallito;
- la scelta di restituire `None` quando una riga non è pertinente;
- l’uso di regex per riconoscere righe come `Failed password` e `Invalid user`;
- l’aggiunta del metodo `parse_file()` per leggere un file riga per riga;
- la creazione di `tests/test_parser.py` per verificare i casi principali;
- l’aggiunta di `examples/auth.log` come file utile per test e demo;
- l’aggiornamento del devlog con una descrizione della Fase 2.

### Cosa abbiamo modificato o adattato

Abbiamo considerato da modificare o adattare:

- i pattern regex, se durante i test risultano troppo rigidi o non coprono bene i log di esempio;
- la gestione del timestamp, perché i log SSH non includono l’anno;
- il contenuto di `examples/auth.log`, in base ai casi che vorremo mostrare durante la demo;
- il testo del devlog, per renderlo coerente con quello che è stato effettivamente fatto dal gruppo;

### Cosa abbiamo rifiutato o non applicato

Non abbiamo accettato:

- la creazione di un parser troppo generico per qualsiasi formato di log;
- l’aggiunta di librerie esterne non necessarie;
- una gestione troppo complessa dei timestamp;
- codice non verificato con i test.

### Codice generato o suggerito

In questa sessione l'IA ha suggerito una possibile implementazione per:

- `src/ban_engine/parser.py`;
- `tests/test_parser.py`;
- `examples/auth.log`.

Il parser proposto riconosce tentativi falliti tramite regex e crea oggetti `LoginAttempt`.

I test proposti verificano:

- righe `Failed password` con utente esistente;
- righe `Failed password for invalid user`;
- righe `Invalid user`;
- righe non pertinenti;
- IP non validi;
- lettura di più righe da file tramite `parse_file()`.

Questa parte deve essere verificata dal gruppo con:

```bash
python -m pytest -q