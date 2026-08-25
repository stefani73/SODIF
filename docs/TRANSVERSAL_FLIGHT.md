# Transversal Flight — specificația lanțului complet de încredere

## Obiectiv

Transversal Flight demonstrează, într-un singur flux reproductibil, că o intenție aprobată
printr-un document semnat poate fi păstrată verificabil și aplicată exact la limita API.
Fluxul folosește componentele reale ale celor trei module SODIF și produce dovezi corelate,
nu rezultate paralele fără legătură.

## Contractul celor două demonstrații

- **Security Flight** validează exclusiv nucleul finanțat: integritatea reviziei, verificarea
  semantică adaptivă, emiterea permisului legat de acțiune și protecția anti-replay. Nu scrie
  în arhivă și nu trece prin Gateway.
- **Transversal Flight** păstrează aceleași controale și adaugă arhivarea reviziilor acceptate,
  aplicarea permisului prin Semantic Execution Gateway și dovada efectului asupra API-ului.

## Traseul tranzacției conforme

1. revizia și semnătura sunt validate;
2. revizia acceptată este înregistrată în arhiva verificabilă;
3. câmpurile critice sunt confruntate prin verificare semantică adaptivă;
4. intenția acceptată este compilată într-un plan API determinist;
5. permisul Ed25519 leagă planul, destinația și fereastra de valabilitate;
6. Gateway-ul aplică politica rutei și autorizează permisul o singură dată;
7. adaptorul API execută numai planul aprobat și emite confirmarea;
8. raportul corelează identificatorii arhivei, permisului, deciziei Gateway și execuției.

## Situații și rezultat observabil

| Situație | Security | Arhivă | Gateway / API |
|---|---|---|---|
| document conform | permis emis | revizie păstrată | rutare și HTTP 202 |
| dovadă inițial incompletă | verificare extinsă controlat | revizie păstrată | rutare după confirmare |
| document modificat | blocare la integritate | fără scriere | nu este apelat |
| conflict semantic critic | escaladare, fără permis | revizia validă rămâne trasabilă | nu este apelat |
| acțiune API modificată | abatere față de permis | revizie păstrată | blocare înainte de API |
| permis reutilizat | consum unic | revizie păstrată | prima cerere este rutată, repetarea este blocată |

O tranzacție oprită într-un modul nu este forțată artificial prin modulele următoare. Aceasta
este proprietatea fail-closed demonstrată: dovezile arată atât controalele executate, cât și
punctul exact în care efectul extern a fost prevenit.

## Dovezi și exporturi

Fiecare rulare produce:

- raport Word pentru evaluare umană;
- raport JSON cu modelele complete ale scenariilor;
- jurnal NDJSON ordonat cu observațiile, deciziile Gateway și verdictele finale;
- manifest SHA-256 cu dimensiunea și amprenta fiecărui artefact;
- pachet ZIP determinist care reunește toate fișierele.

Pentru fiecare decizie Gateway sunt păstrate identificatorul requestului, ruta, audiența,
permisul, controalele aplicate, amprenta acțiunii observate, amprenta autorizată și, numai
pentru rutare, confirmarea execuției.

## Criterii de acceptare

- Security Flight nu conține dovezi de arhivă sau Gateway;
- Transversal Flight conține dovezi din toate cele trei module;
- rezultatele de securitate rămân aceleași în ambele demonstrații;
- documentul modificat nu este arhivat și nu ajunge la analiza semantică ori Gateway;
- conflictul critic nu produce permis sau apel API;
- schimbarea acțiunii este blocată prin nepotrivirea față de permis;
- același permis produce cel mult o execuție;
- fiecare acțiune și decizie relevantă apare în jurnalul exportat;
- raportul și pachetul sunt reproductibile pentru aceeași rulare.
