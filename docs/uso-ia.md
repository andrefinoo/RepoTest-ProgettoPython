# Uso dell’intelligenza artificiale

Durante il progetto abbiamo usato soprattutto **Gemini** e **ChatGPT** come supporto per chiarire i requisiti, valutare alcune soluzioni, individuare errori e preparare test.  
Le scelte finali sono state adattate al nostro codice e controllate con PyCharm e pytest.

---

## 1. Analisi della consegna e pianificazione iniziale

All’inizio abbiamo usato l’IA per riassumere la consegna e trasformarla in una checklist più semplice da seguire.

Ci è stato suggerito di dividere il progetto in modelli, parser, engine, backend firewall, configurazione e persistenza. Abbiamo mantenuto questa divisione perché rende il lavoro più ordinato e facile da testare.

Abbiamo però evitato strutture troppo complesse e dipendenze non necessarie, adattando tutto ai file già presenti nel repository.

La pianificazione è stata verificata confrontandola con la consegna ufficiale, la proposta e la struttura reale del progetto.

---

## 2. Modelli dati e validazione degli IP

Abbiamo chiesto come rappresentare i tentativi di login e le decisioni di ban.

L’IA ci ha suggerito di usare `dataclass`, creare `LoginAttempt` e `BanDecision` e validare gli indirizzi con `ipaddress.ip_address()`.

Abbiamo accettato questa soluzione perché è più sicura e leggibile di una regex completa per IPv4 e IPv6. Abbiamo mantenuto i modelli semplici e adattato nomi e controlli ai test del progetto.

Il risultato è stato verificato con pytest su IP validi, IP non validi, username opzionale e conversione in dizionario.

---

## 3. Parser dei log SSH

Per il parser abbiamo chiesto aiuto nel riconoscere i principali errori SSH e nell’estrarre timestamp, username e indirizzo IP.

Ci è stato consigliato di usare regex separate per `Failed password`, `invalid user` e `Invalid user`, invece di un unico pattern difficile da leggere.

Abbiamo limitato il parser ai casi utili per l’MVP e restituito `None` per le righe non pertinenti. Per i timestamp senza anno abbiamo usato una soluzione semplice con fallback.

Abbiamo verificato il comportamento con test su righe valide, righe ignorate, IP errati e file con contenuto misto.

---

## 4. Struttura del repository e import

Quando i test non trovavano il package, abbiamo chiesto come gestire correttamente una struttura con cartella `src`.

Sono state proposte più soluzioni, tra cui `PYTHONPATH`, installazione editable e `tests/conftest.py`.

Abbiamo scelto `conftest.py` perché permetteva di eseguire i test dalla root in modo stabile, senza dipendere dal nome della cartella locale.

Abbiamo evitato import come `RepoPython.src...` e verificato la correzione eseguendo:

```bash
python -m pytest -q
```

---

## 5. Backend firewall polimorfici

Abbiamo usato ChatGPT per chiarire la struttura della gerarchia firewall e per controllare i comandi dei diversi sistemi operativi.

Ci è stato suggerito di creare la classe astratta `FirewallBackend` con `block_ip()`, `unblock_ip()` e `is_blocked()`, poi tre implementazioni concrete: dry-run, Linux e Windows.

Abbiamo sviluppato prima il backend dry-run con un `set`, poi il backend Linux con `iptables` e infine quello Windows con `netsh advfirewall`. I comandi sono passati a `subprocess.run()` come liste, senza `shell=True`.

Abbiamo adattato i nomi delle regole Windows e separato i test dei comandi dal test del polimorfismo.

Tutti i comandi reali sono stati sostituiti con mock durante pytest, così da non modificare il firewall del computer.

---

## 6. Debugging del test polimorfico

Il test polimorfico inizialmente falliva perché i mock Linux e Windows applicati a `subprocess.run()` interferivano tra loro.

L’IA ci ha aiutato a capire che entrambi i moduli facevano riferimento allo stesso oggetto `subprocess`.

Abbiamo quindi lasciato ai test specifici il controllo dei comandi e usato `patch.object()` sui metodi delle singole istanze nel test polimorfico.

Non abbiamo eliminato il test né ridotto le verifiche solo per far passare la suite.

Dopo la modifica abbiamo rilanciato pytest e controllato sia il comportamento reale del dry-run sia le chiamate ai backend Linux e Windows.

---

## 7. Supporto alla documentazione

Abbiamo usato ChatGPT per organizzare e revisionare `devlog.md`, `scelte.md` e `uso-ia.md`.

Il supporto è servito soprattutto per creare una struttura chiara, riassumere il lavoro svolto e controllare la coerenza con i commit e con la checklist.

Le bozze sono state usate come base e poi adattate al nostro modo di spiegare il progetto.

L’IA non ha eseguito commit, push, test o comandi firewall e non ha deciso autonomamente quali modifiche inserire.

---

## 8. Metodo seguito nell’uso dell’IA

Per ogni suggerimento abbiamo cercato prima di capirlo, poi di confrontarlo con il codice e con le lezioni.

Abbiamo accettato solo le soluzioni che riuscivamo a spiegare e che potevamo verificare con test o esecuzioni controllate.

Quando una proposta era troppo complessa, non adatta al repository o difficile da capire, l’abbiamo modificata oppure scartata.

Al momento il repository contiene aggiornamenti fino alla documentazione dei backend firewall; le parti su `IncidentResponseEngine`, JSON, persistenza e CLI verranno aggiunte quando saranno realmente sviluppate.