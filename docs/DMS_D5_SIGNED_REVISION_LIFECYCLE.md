# DMS D5 — ciclul reviziilor semnate

## Rezultat

Componenta documentară demonstrează acum un istoric real, nu doar capacitatea structurală
de a-l stoca. O revizie nouă este admisă numai dacă semnătura sa acoperă propriul conținut și
metadatele indică exact amprenta ultimei revizii acceptate.

## Flux demonstrativ

Pagina „Preluare documente” oferă un set reproductibil cu două revizii ale aceleiași comenzi:

1. revizia inițială este verificată și arhivată;
2. acțiunea pentru revizia următoare devine disponibilă;
3. a doua semnătură este verificată independent;
4. numărul reviziei, identitatea documentului, formatul și digestul predecesorului sunt
   confruntate cu istoricul persistent;
5. registrul afișează revizia curentă și permite revenirea la versiunea anterioară;
6. pachetul offline include ambele înregistrări și verifică continuitatea lanțului.

Transversal Flight reproduce aceeași proprietate: după execuția controlată, o revizie
ulterioară continuă istoricul documentului și ambele identificatoare de arhivă sunt păstrate
în dovezile scenariului. Security Flight rămâne neschimbat și fără efecte DMS.

## Controale fail-closed

Sunt respinse reviziile care sar un număr, indică alt predecesor, repetă un conținut anterior,
schimbă identitatea sau formatul documentului ori au un moment de semnare neordonat. O
reîncărcare identică rămâne idempotentă și nu creează o versiune suplimentară.

## Criterii de acceptare

- revizia a doua nu poate fi demonstrată înaintea reviziei inițiale;
- setul demonstrativ este determinist și poate fi verificat manual;
- istoricul persistent conține exact două revizii legate;
- Transversal Flight expune două dovezi de arhivă pentru scenariul conform;
- Security Flight nu dobândește dependențe sau efecte DMS;
- toate exporturile păstrează lista reviziilor asociate deciziei.
