# Automated Incident Response Ban Engine

Repository del progetto finale di laboratorio Python di **Andrea Finocchielli** e **Alessio Ordazzo**.

Il progetto consiste in una CLI didattica che analizza log SSH, rileva tentativi di brute-force e decide se un indirizzo IP deve essere bloccato quando supera una soglia configurabile in una finestra temporale.

La modalità `dry-run` permette di simulare il ban senza modificare realmente il firewall del sistema, così la demo resta sicura e controllabile.

---

## Cosa fa

**Automated Incident Response Ban Engine** è un piccolo motore di risposta agli incidenti ispirato a strumenti come Fail2ban.

Il programma legge file di log SSH, riconosce i tentativi di login falliti, estrae gli indirizzi IP coinvolti e li aggrega per capire se un host sta effettuando troppi tentativi in poco tempo.

Quando un IP supera la soglia configurata, il motore produce una decisione di ban e la passa a un backend firewall. Il backend può essere reale, come Linux `iptables` o Windows `netsh`, oppure simulato tramite `DryRunFirewallBackend`.

---

## Membri del gruppo

- Andrea Finocchielli — GitHub: `andrefinoo`
- Alessio Ordazzo — GitHub: da indicare

Corso: **Programmazione Python — Cybersecurity Specialist**

---

## Obiettivo del progetto

L’obiettivo è realizzare un progetto Python funzionante, organizzato e difendibile all’orale.

Il programma dovrà:

- leggere log SSH da file;
- riconoscere tentativi di login falliti;
- estrarre e validare indirizzi IPv4 e IPv6;
- raggruppare i tentativi per IP;
- applicare una soglia di ban;
- ignorare gli IP presenti in whitelist;
- usare backend firewall polimorfici;
- salvare configurazione e stato in JSON;
- fornire test automatici con `pytest`.

---

## Requisiti

Richiede:

- Python 3.11+
- pytest

Le dipendenze del progetto sono indicate in:

```bash
requirements.txt
```