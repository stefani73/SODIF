# Registrul criptografic anti-tamper al rulărilor

## Rol

Registrul asigură continuitatea verificabilă a pachetelor produse de Security Flight și
Transversal Flight. Este un mecanism transversal al zonei „Audit & Integrity”, nu un al
patrulea modul de produs.

## Mecanism

Fiecare rulare finalizată produce o intrare NDJSON care conține:

- numărul secvențial și amprenta SHA-256 a intrării precedente;
- identificatorii rulării, sesiunii și tipului de flight;
- calea relativă și amprenta pachetului ZIP;
- calea relativă și amprenta manifestului de integritate;
- amprenta canonică a intrării curente.

Prima intrare este originea lanțului. Fiecare intrare ulterioară depinde criptografic de
intrarea precedentă, astfel încât modificarea, eliminarea, reordonarea sau inserarea unei
înregistrări să devină detectabilă.

## Verificare

Verificarea independentă controlează simultan:

1. protocolul și structura fiecărei intrări;
2. secvența și continuitatea legăturilor criptografice;
3. recalcularea amprentei fiecărei intrări;
4. existența pachetului ZIP și a manifestului referențiat;
5. concordanța SHA-256 a ambelor fișiere cu valorile înscrise.

O verificare nereușită blochează înscrierea unei noi rulări. Registrul corupt nu este
suprascris și nu este reparat implicit.

## Artefacte

- `var/exports/sodif-run-integrity-ledger.ndjson` — registrul comun;
- `<run>/sodif-run-integrity-receipt.json` — chitanța portabilă a rulării;
- pachetul ZIP și manifestul existente — obiectele protejate de intrare.

Chitanța include poziția, amprenta intrării, legătura precedentă, capul verificat al
registrului și amprentele obiectelor asociate.

## Integrarea în flight-uri

Pentru ambele flight-uri, înscrierea se execută automat după generarea pachetului de audit.
Pagina „Audit și exporturi” afișează starea lanțului, poziția rulării, numărul intrărilor
verificate și permite descărcarea chitanței și a registrului complet.

## Criterii de acceptare

- două flight-uri succesive formează un lanț cu două intrări valide;
- chitanța celei de-a doua rulări indică amprenta primei intrări;
- modificarea unei intrări este detectată;
- modificarea pachetului ZIP este detectată;
- o nouă înscriere este refuzată dacă registrul existent nu se verifică integral.
