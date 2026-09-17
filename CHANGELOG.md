# Changelog

## 0.23.0 — 2026-09-17

- introduce selecția manuală, la preluare, a protecției avansate SODIF pentru fiecare document;
- păstrează regimul ales în metadatele arhivei și în pachetul documentar verificabil;
- afișează regimul de securitate în confirmarea preluării și în registrul documentelor;
- menține același regim pentru toate reviziile documentului și blochează schimbările de nivel
  în interiorul unui istoric existent;
- migrează arhivele existente în regimul avansat, păstrând comportamentul anterior.

## 0.22.0 — 2026-09-17

- explică în interfață, pentru fiecare câmp, valorile observate în structura PDF și în
  randările vizuale, precum și valoarea autorizabilă sau conflictul rezultat;
- afișează identificatorul de corelare al tranzacției și nivelul de control în toate scenariile;
- include identificatorul tranzacției în jurnalul NDJSON și în trasabilitatea raportului;
- descrie explicit calculul și compararea amprentei cererii în SODIF Gateway;
- delimitează configurația TRL 4: două randări distincte cu același Tesseract și adaptor API
  local fără efect extern;
- extinde rapoartele Word cu matricea valorilor confruntate.

## 0.20.0 — Cybersecurity product alignment

- poziționare unitară ca platformă de securitate cibernetică pentru execuții autorizate prin documente semnate;
- identitate canonică pentru modulele SODIF Security, SODIF Archive și SODIF Gateway;
- configurarea de laborator documentată explicit în rapoartele operaționale;
- generarea coordonată a ambelor Flight-uri și a tuturor artefactelor de audit;
- interfață și texte tehnice armonizate cu lanțul revizie–intenție–permis–cerere API;
- teste actualizate pentru contractele de produs și rapoartele extinse.

## 0.12.0 — DMS D3: registrul documentelor

- registru de produs cu sumar, căutare și filtrare după semnatar;
- gruparea reviziilor sub identitatea documentului;
- deschiderea conținutului numai după reverificarea integrității;
- previzualizare PDF și descărcarea reviziei selectate;
- trasabilitatea completă a lanțului de revizii;
- acces direct la registru din demonstrația controlată.

## 0.11.0 — DMS D2: preluarea documentelor semnate

- pagină de produs dedicată preluării documentului PDF și dovezii de semnătură;
- serviciu unic pentru verificarea semnăturii, a istoricului și arhivarea reviziei;
- recunoașterea idempotentă a unei revizii deja arhivate;
- suport persistent pentru lanțul complet de revizii;
- mesaje fail-closed clare, fără expunerea detaliilor interne;
- pachet semnat demonstrativ, reproductibil și descărcabil.

## 0.10.0 — DMS D1: arhivă și index verificabil

- depozit local de obiecte adresate prin SHA-256 și indexate în SQLite;
- arhivare exclusivă a reviziilor validate criptografic;
- preluare idempotentă, deduplicare și blocarea conflictelor de revizie;
- căutare full-text și filtre stabile pentru document și semnatar;
- reverificarea integrității la recuperarea documentului;
- dovada arhivării integrată în flight și în exporturile auditabile.

## 0.9.0 — Multipage product experience

- navigație laterală retractabilă, organizată în zone de produs și demonstrație;
- patru pagini distincte pentru prezentare, funcționare, control și dovezi;
- limbaj românesc revizuit și orientat spre utilizator;
- iconografie Material pentru navigație, acțiuni și descărcări;
- separarea rulării scenariilor de zona de rapoarte și exporturi;
- stare de sesiune comună și extensibilă pentru paginile produsului.

## 0.8.0 — Reporting and evidence exports

- raport Word profesional generat din rezultatul Assurance Flight;
- raport JSON complet și jurnal auditabil NDJSON;
- manifest cu amprente SHA-256 și rădăcină de integritate;
- pachet ZIP reproductibil cu metadate normalizate;
- descărcări directe pentru pachet, raport și dovezi;
- comandă separată pentru export local atomic.

## 0.7.0 — Product UI

- landing page cu poziționare clară Document-to-API;
- navigare minimală între prezentarea produsului și Assurance Flight;
- rulare interactivă a motorului flight din interfață;
- verdicte, controale și efect API formulate pentru utilizator;
- trasee de decizie și dovezi tehnice compacte;
- strat de prezentare separat și sistem vizual responsive, fără resurse externe.

## 0.6.0 — Pasul 6

- asamblare deterministă a manifestului din consens acceptat;
- compilare exactă a manifestului într-un plan API;
- adaptor API local fără efecte externe și chitanță de execuție;
- motor flight cu șase scenarii de succes, optimizare și atac;
- cronologie, digesturi și rezultate serializabile pentru fiecare scenariu;
- comandă CLI reproductibilă pentru rularea întregului flight.

## 0.5.0 — Pasul 5

- permis Ed25519 cu identificator unic și fereastră temporală scurtă;
- legare de verificare, consens, manifest, politică și planul API exact;
- registru separat de chei de emitere, cu activare și revocare;
- verificarea audienței și a digestului acțiunii înainte de autorizare;
- consum atomic și protecție concurentă împotriva reutilizării permisului;
- coduri de respingere stabile pentru emitere și autorizare.

## 0.4.0 — Pasul 4

- politică explicabilă de risc și niveluri adaptive V0–V3;
- normalizare semantică deterministă pentru șapte tipuri de date;
- consens cu proveniență între reprezentări independente;
- două căi în fluxul normal și activarea condiționată a celei de-a treia;
- escaladare fail-closed pentru lipsă, conflict sau risc de revizuire;
- contabilizarea costului de verificare și a resurselor economisite.

## 0.3.0 — Pasul 3

- validare minimală și limitare de dimensiune pentru artefacte PDF;
- semnătură detașată Ed25519 peste metadate canonice și digestul conținutului;
- registru local de chei de încredere, cu perioadă de activitate și revocare;
- lanț atomic de revizii care blochează salturi, ramificații și reutilizarea conținutului;
- coduri de respingere stabile și teste pentru modificare, chei nevalide și istoric inconsistent.

## 0.2.0 — Pasul 2

- modele de domeniu imutabile, stricte și versionabile;
- contracte pentru document, risc, consens, compilare și evidență;
- canonicalizare JSON deterministă și digesturi SHA-256;
- schemă generică pentru intenția operațională;
- mașină de stări pură, cu tranziții fail-closed;
- teste unitare și de arhitectură pentru independența față de Streamlit.

## 0.1.0 — Pasul 1

- structură modulară `src/`;
- mediu Python izolat și dependențe reproductibile;
- shell Streamlit minimal, cu identitate vizuală SODIF;
- porți automate: Ruff, mypy, pytest și coverage;
- documentație de continuitate și criterii de acceptare.
