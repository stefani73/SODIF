# Pasul 3 — document semnat și controlul reviziilor

## Obiectiv

Acceptarea unei revizii numai când conținutul exact, identitatea semnatarului și poziția în
istoricul documentului pot fi demonstrate tehnic. Rezultatul devine intrarea de încredere
pentru verificările semantice din pasul următor.

## Mecanism demonstrat

1. PDF-ul este verificat la limita binară și limitat ca dimensiune.
2. Octeții primiți sunt amprentați cu SHA-256.
3. Digestul, identificatorul documentului, numărul reviziei, predecesorul, semnatarul și
   momentul semnării formează un pachet canonic RFC 8785.
4. Semnătura detașată Ed25519 a pachetului este verificată cu o cheie din registrul de
   încredere și cu regulile sale de activare/revocare.
5. Revizia este adăugată atomic numai dacă extinde exact ultima revizie acceptată.

Semnătura acoperă indirect fiecare octet al PDF-ului prin digest și acoperă direct contextul
reviziei. Astfel, aceeași semnătură nu poate fi mutată pe alt document, semnatar sau poziție
în istoric.

## Cazuri blocate

- PDF gol, supradimensionat sau cu structură minimă invalidă;
- conținut modificat după semnare;
- cheie necunoscută, inactivă, revocată sau atribuită altui semnatar;
- semnătură coruptă ori mutată pe alte metadate;
- prima revizie diferită de 1;
- salt peste o revizie, predecesor vechi, ramificare sau reutilizarea aceluiași conținut.

## Delimitare tehnică

Demonstratorul folosește o semnătură detașată Ed25519 reală, nu un indicator simulat.
Validarea PAdES încorporată în PDF și conectarea la PKI/HSM sunt adaptoare de producție
ulterioare; contractele permit înlocuirea mecanismului fără schimbarea fluxului SODIF.

## Criterii de acceptare

- o revizie validă produce un `DocumentEnvelope` și un `RevisionRecord` coerente;
- orice schimbare a conținutului sau a metadatelor semnate este respinsă;
- istoricul acceptat este monoton, fără goluri și fără ramificații;
- toate respingerile au un cod stabil, utilizabil ulterior în interfață și raport;
- Ruff, mypy strict, pytest și verificarea dependențelor sunt integral verzi;
- repository-ul este curat după commitul separat al Pasului 3.
