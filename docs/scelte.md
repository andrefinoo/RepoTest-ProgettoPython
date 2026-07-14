# Scelte implementative

Questo documento raccoglie le decisioni tecniche non immediate adottate durante lo sviluppo del progetto. Le scelte vengono aggiornate progressivamente quando una parte del programma diventa stabile e verificata dai test.

## 1. Gerarchia dei backend firewall

### Contesto

Il programma deve poter applicare la stessa operazione di mitigazione su sistemi differenti. Linux utilizza `iptables`, Windows utilizza `netsh advfirewall`, mentre durante test e dimostrazioni è necessario simulare il comportamento senza modificare il firewall reale.

### Scelta adottata

Abbiamo definito la classe base astratta `FirewallBackend`, che stabilisce un contratto comune tramite tre metodi:

- `block_ip(ip: str)`;
- `unblock_ip(ip: str)`;
- `is_blocked(ip: str) -> bool`.

Le implementazioni concrete attuali sono:

- `DryRunFirewallBackend`;
- `LinuxIptablesBackend`;
- `WindowsFirewallBackend`.

La classe base eredita da `ABC` e i tre metodi sono dichiarati con `@abstractmethod`. In questo modo `FirewallBackend` non può essere istanziata direttamente e ogni nuova sottoclasse deve implementare tutte le operazioni richieste.

### Perché abbiamo usato l'ereditarietà

In questo caso la relazione “è un” è corretta: ogni implementazione concreta **è un backend firewall** e rispetta lo stesso contratto operativo, anche se traduce le operazioni in modo differente.

L'ereditarietà permette al resto del programma di lavorare con un riferimento di tipo `FirewallBackend` senza conoscere la classe concreta. Il codice può quindi chiamare `backend.block_ip(ip)` allo stesso modo per Linux, Windows o dry-run. Il comportamento effettivo viene deciso dall'oggetto ricevuto: questo è il punto in cui si realizza il polimorfismo.

La gerarchia rende inoltre più semplice aggiungere in futuro un nuovo backend, per esempio basato su `nftables`, senza modificare la logica di analisi degli incidenti.

### Alternative considerate

Una prima alternativa sarebbe stata creare funzioni separate, come `block_ip_linux()` e `block_ip_windows()`. Questa soluzione avrebbe però distribuito la stessa responsabilità in più funzioni e avrebbe obbligato il chiamante a conoscere il sistema operativo.

Un'altra alternativa sarebbe stata inserire nel motore una catena di condizioni:

```python
if sistema == "linux":
    ...
elif sistema == "windows":
    ...
```

Abbiamo scartato questa soluzione perché avrebbe accoppiato la logica di rilevamento ai dettagli del firewall. Ogni nuovo sistema operativo avrebbe richiesto una modifica al motore.

La composizione rimane invece la scelta corretta a un livello superiore: l'`IncidentResponseEngine` riceverà e utilizzerà un oggetto `FirewallBackend`, ma non erediterà da esso. Un motore di risposta agli incidenti **ha un** backend firewall, non **è un** backend firewall.

### Compromessi

La gerarchia introduce più classi e più file rispetto a una soluzione procedurale. In cambio otteniamo un contratto esplicito, responsabilità separate, test più isolati ed estensione più semplice.

## 2. Backend dry-run separato dai backend reali

### Contesto

L'esecuzione di comandi firewall reali durante i test o la demo potrebbe richiedere privilegi amministrativi e potrebbe modificare la connettività del computer.

### Scelta adottata

Abbiamo creato `DryRunFirewallBackend`, che implementa lo stesso contratto dei backend reali ma conserva gli indirizzi bloccati in un `set[str]`.

Il metodo `block_ip()` aggiunge l'indirizzo all'insieme, `unblock_ip()` lo rimuove con `discard()` e `is_blocked()` verifica la presenza dell'indirizzo.

### Motivazione

Il dry-run non è stato inserito come semplice condizione dentro i backend Linux o Windows. È una sottoclasse autonoma perché rappresenta una strategia completa e sostituibile, utilizzabile dal programma esattamente come un backend reale.

L'uso di un `set` evita duplicati e rende immediato il controllo di appartenenza. La scelta è adatta alla simulazione, anche se lo stato rimane soltanto in memoria e viene perso alla chiusura del processo.

## 3. Esecuzione dei comandi di sistema con `subprocess`

### Scelta adottata

I backend reali costruiscono i comandi come liste di argomenti e li passano a `subprocess.run()` senza utilizzare `shell=True`.

Per le operazioni che modificano il firewall, `block_ip()` e `unblock_ip()`, utilizziamo `check=True`. Un comando terminato con codice di errore provoca quindi un'eccezione invece di essere ignorato silenziosamente.

Per `is_blocked()` utilizziamo invece `check=False`, perché un codice di ritorno diverso da zero può significare semplicemente che la regola cercata non esiste. L'output viene acquisito solo quando necessario.

### Motivazione

Le liste di argomenti sono più leggibili e riducono i rischi legati all'interpretazione di una stringa da parte della shell. Inoltre rendono i comandi più semplici da verificare nei test.

Nel backend Windows abbiamo adottato il prefisso costante `BanEngine` e il metodo `_rule_name(ip)` per produrre nomi di regola deterministici. In questo modo la stessa regola può essere cercata e rimossa senza duplicare la logica di costruzione del nome.

## 4. Test sicuri tramite mock

### Contesto

I test non devono eseguire realmente `iptables` o `netsh`, né dipendere dal sistema operativo sul quale viene eseguita la suite.

### Scelta adottata

Nei test dei singoli backend sostituiamo `subprocess.run()` con un mock. Verifichiamo così:

- il comando costruito;
- gli argomenti passati;
- l'uso di `check`, `capture_output` e `text`;
- l'interpretazione del codice di ritorno e dell'output.

Il test polimorfico usa una funzione che accetta un parametro di tipo `FirewallBackend` e invoca `block_ip()` senza controllare la sottoclasse concreta. Per Linux e Windows viene applicato `patch.object()` direttamente al metodo delle istanze, mentre il backend dry-run esegue il proprio comportamento reale in memoria.

### Motivazione

Questa soluzione dimostra il polimorfismo senza invocare comandi privilegiati. L'uso di `patch.object()` nel test comune evita inoltre interferenze tra mock applicati a moduli che fanno riferimento allo stesso oggetto `subprocess`.

## 5. Decisioni ancora da consolidare

Le scelte relative a `IncidentResponseEngine`, configurazione JSON, persistenza dello storico dei ban e interfaccia CLI verranno aggiunte quando le rispettive implementazioni saranno complete e verificate dai test.

---

**Riferimento di sviluppo:** commit `1b10851` — `completa backend firewall polimorfici`.# Scelte implementative

Questo documento raccoglie le decisioni tecniche non immediate adottate durante lo sviluppo del progetto. Le scelte vengono aggiornate progressivamente quando una parte del programma diventa stabile e verificata dai test.

## 1. Gerarchia dei backend firewall

### Contesto

Il programma deve poter applicare la stessa operazione di mitigazione su sistemi differenti. Linux utilizza `iptables`, Windows utilizza `netsh advfirewall`, mentre durante test e dimostrazioni è necessario simulare il comportamento senza modificare il firewall reale.

### Scelta adottata

Abbiamo definito la classe base astratta `FirewallBackend`, che stabilisce un contratto comune tramite tre metodi:

- `block_ip(ip: str)`;
- `unblock_ip(ip: str)`;
- `is_blocked(ip: str) -> bool`.

Le implementazioni concrete attuali sono:

- `DryRunFirewallBackend`;
- `LinuxIptablesBackend`;
- `WindowsFirewallBackend`.

La classe base eredita da `ABC` e i tre metodi sono dichiarati con `@abstractmethod`. In questo modo `FirewallBackend` non può essere istanziata direttamente e ogni nuova sottoclasse deve implementare tutte le operazioni richieste.

### Perché abbiamo usato l'ereditarietà

In questo caso la relazione “è un” è corretta: ogni implementazione concreta **è un backend firewall** e rispetta lo stesso contratto operativo, anche se traduce le operazioni in modo differente.

L'ereditarietà permette al resto del programma di lavorare con un riferimento di tipo `FirewallBackend` senza conoscere la classe concreta. Il codice può quindi chiamare `backend.block_ip(ip)` allo stesso modo per Linux, Windows o dry-run. Il comportamento effettivo viene deciso dall'oggetto ricevuto: questo è il punto in cui si realizza il polimorfismo.

La gerarchia rende inoltre più semplice aggiungere in futuro un nuovo backend, per esempio basato su `nftables`, senza modificare la logica di analisi degli incidenti.

### Alternative considerate

Una prima alternativa sarebbe stata creare funzioni separate, come `block_ip_linux()` e `block_ip_windows()`. Questa soluzione avrebbe però distribuito la stessa responsabilità in più funzioni e avrebbe obbligato il chiamante a conoscere il sistema operativo.

Un'altra alternativa sarebbe stata inserire nel motore una catena di condizioni:

```python
if sistema == "linux":
    ...
elif sistema == "windows":
    ...
```

Abbiamo scartato questa soluzione perché avrebbe accoppiato la logica di rilevamento ai dettagli del firewall. Ogni nuovo sistema operativo avrebbe richiesto una modifica al motore.

La composizione rimane invece la scelta corretta a un livello superiore: l'`IncidentResponseEngine` riceverà e utilizzerà un oggetto `FirewallBackend`, ma non erediterà da esso. Un motore di risposta agli incidenti **ha un** backend firewall, non **è un** backend firewall.

### Compromessi

La gerarchia introduce più classi e più file rispetto a una soluzione procedurale. In cambio otteniamo un contratto esplicito, responsabilità separate, test più isolati ed estensione più semplice.

## 2. Backend dry-run separato dai backend reali

### Contesto

L'esecuzione di comandi firewall reali durante i test o la demo potrebbe richiedere privilegi amministrativi e potrebbe modificare la connettività del computer.

### Scelta adottata

Abbiamo creato `DryRunFirewallBackend`, che implementa lo stesso contratto dei backend reali ma conserva gli indirizzi bloccati in un `set[str]`.

Il metodo `block_ip()` aggiunge l'indirizzo all'insieme, `unblock_ip()` lo rimuove con `discard()` e `is_blocked()` verifica la presenza dell'indirizzo.

### Motivazione

Il dry-run non è stato inserito come semplice condizione dentro i backend Linux o Windows. È una sottoclasse autonoma perché rappresenta una strategia completa e sostituibile, utilizzabile dal programma esattamente come un backend reale.

L'uso di un `set` evita duplicati e rende immediato il controllo di appartenenza. La scelta è adatta alla simulazione, anche se lo stato rimane soltanto in memoria e viene perso alla chiusura del processo.

## 3. Esecuzione dei comandi di sistema con `subprocess`

### Scelta adottata

I backend reali costruiscono i comandi come liste di argomenti e li passano a `subprocess.run()` senza utilizzare `shell=True`.

Per le operazioni che modificano il firewall, `block_ip()` e `unblock_ip()`, utilizziamo `check=True`. Un comando terminato con codice di errore provoca quindi un'eccezione invece di essere ignorato silenziosamente.

Per `is_blocked()` utilizziamo invece `check=False`, perché un codice di ritorno diverso da zero può significare semplicemente che la regola cercata non esiste. L'output viene acquisito solo quando necessario.

### Motivazione

Le liste di argomenti sono più leggibili e riducono i rischi legati all'interpretazione di una stringa da parte della shell. Inoltre rendono i comandi più semplici da verificare nei test.

Nel backend Windows abbiamo adottato il prefisso costante `BanEngine` e il metodo `_rule_name(ip)` per produrre nomi di regola deterministici. In questo modo la stessa regola può essere cercata e rimossa senza duplicare la logica di costruzione del nome.

## 4. Test sicuri tramite mock

### Contesto

I test non devono eseguire realmente `iptables` o `netsh`, né dipendere dal sistema operativo sul quale viene eseguita la suite.

### Scelta adottata

Nei test dei singoli backend sostituiamo `subprocess.run()` con un mock. Verifichiamo così:

- il comando costruito;
- gli argomenti passati;
- l'uso di `check`, `capture_output` e `text`;
- l'interpretazione del codice di ritorno e dell'output.

Il test polimorfico usa una funzione che accetta un parametro di tipo `FirewallBackend` e invoca `block_ip()` senza controllare la sottoclasse concreta. Per Linux e Windows viene applicato `patch.object()` direttamente al metodo delle istanze, mentre il backend dry-run esegue il proprio comportamento reale in memoria.

### Motivazione

Questa soluzione dimostra il polimorfismo senza invocare comandi privilegiati. L'uso di `patch.object()` nel test comune evita inoltre interferenze tra mock applicati a moduli che fanno riferimento allo stesso oggetto `subprocess`.

## 5. Decisioni ancora da consolidare

Le scelte relative a `IncidentResponseEngine`, configurazione JSON, persistenza dello storico dei ban e interfaccia CLI verranno aggiunte quando le rispettive implementazioni saranno complete e verificate dai test.

---

**Riferimento di sviluppo:** commit `1b10851` — `completa backend firewall polimorfici`.