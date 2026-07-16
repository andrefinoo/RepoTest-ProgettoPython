# Scelte implementative

Questo documento riassume le principali decisioni tecniche prese durante lo sviluppo di **Automated Incident Response Ban Engine**.  
Le scelte sono state aggiunte man mano che le varie parti del progetto diventavano stabili e verificate dai test.

---

## 1. Gerarchia dei backend firewall

Abbiamo creato la classe astratta `FirewallBackend`, che definisce i metodi comuni `block_ip()`, `unblock_ip()` e `is_blocked()`.

Da questa classe derivano `DryRunFirewallBackend`, `LinuxIptablesBackend` e `WindowsFirewallBackend`.

Abbiamo scelto l’ereditarietà perché ogni classe concreta **è un backend firewall** e deve rispettare lo stesso contratto, anche se esegue operazioni diverse.

In questo modo il resto del programma può usare un oggetto di tipo `FirewallBackend` senza sapere se sta lavorando con Linux, Windows o dry-run.

Abbiamo scartato funzioni separate o controlli `if/elif` sul sistema operativo, perché avrebbero legato troppo il motore ai dettagli dei singoli firewall.

---

## 2. Backend dry-run separato

Per test e dimostrazioni avevamo bisogno di una modalità sicura che non modificasse il firewall reale.

Abbiamo quindi creato `DryRunFirewallBackend`, che salva gli IP bloccati in un `set`.

`block_ip()` aggiunge l’indirizzo, `unblock_ip()` lo rimuove e `is_blocked()` controlla se è presente.

Abbiamo preferito una sottoclasse autonoma invece di un semplice flag nei backend reali, perché il dry-run rappresenta un comportamento completo e può essere usato allo stesso modo degli altri backend.

Il limite è che lo stato rimane solo in memoria e viene perso alla chiusura del programma.

---

## 3. Uso di `subprocess`

I backend Linux e Windows costruiscono i comandi come liste di argomenti e li passano a `subprocess.run()` senza usare `shell=True`.

Per blocco e sblocco usiamo `check=True`, così un errore del comando non viene ignorato.

Per `is_blocked()` usiamo `check=False`, perché un codice di ritorno diverso da zero può indicare semplicemente che la regola non esiste.

Nel backend Windows ogni regola usa il nome `BanEngine-<ip>`, così la stessa regola può essere cercata e rimossa in modo prevedibile.

Questa soluzione rende i comandi più leggibili, più semplici da testare e meno dipendenti dall’interpretazione della shell.

---

## 4. Test con mock

Durante i test non vogliamo eseguire davvero `iptables` o `netsh`.

Per questo sostituiamo `subprocess.run()` con dei mock e controlliamo il comando costruito, gli argomenti passati e il risultato interpretato dal backend.

Nel test polimorfico usiamo una funzione che riceve un generico `FirewallBackend` e chiama `block_ip()`.

Per Linux e Windows applichiamo `patch.object()` direttamente ai metodi delle istanze, mentre il backend dry-run esegue il comportamento reale in memoria.

Abbiamo scelto questa soluzione dopo aver notato che due patch contemporanee su `subprocess.run()` interferivano tra loro.

---

## 5. Ereditarietà e composizione

L’ereditarietà viene usata solo nella gerarchia dei backend, dove la relazione “è un” è corretta.

L’`IncidentResponseEngine` non erediterà da `FirewallBackend`: riceverà invece un backend come dipendenza.

In questo caso la relazione è “ha un”, quindi la composizione è più adatta.

Questa separazione permette al motore di usare backend diversi senza contenere logica specifica per Linux o Windows.

---

## 6. Decisioni ancora da completare

Le scelte relative a `IncidentResponseEngine`, configurazione JSON, persistenza dello stato e CLI verranno aggiunte quando queste parti saranno realmente implementate e verificate dai test.

---

## Compromessi principali

La gerarchia introduce più classi e file rispetto a semplici funzioni, ma rende il codice
più estendibile e permette di usare backend diversi con la stessa interfaccia.

Il dry-run è sicuro e semplice da testare, ma conserva lo stato solo in memoria.

I backend reali dipendono da comandi specifici del sistema operativo e richiedono privilegi
amministrativi, quindi nei test dobbiamo usare i mock.

L’uso dei mock rende i test sicuri e ripetibili, ma non verifica che `iptables` o `netsh`
funzionino davvero sulla macchina finale.

---