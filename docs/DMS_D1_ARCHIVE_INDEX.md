# DMS D1 — depozit documentar și index verificabil

## Obiectiv

D1 introduce nucleul de arhivare al SODIF pentru revizii de document validate. Componenta
este independentă de Streamlit și oferă contracte reutilizabile pentru preluare, căutare,
istoric și recuperarea conținutului original.

## Reguli de acceptare

O revizie poate fi arhivată numai după ce serviciul de documente a confirmat semnătura,
digestul conținutului și continuitatea reviziei. Depozitul verifică din nou digestul și
dimensiunea înainte de stocare și la fiecare recuperare.

- aceeași revizie este procesată idempotent;
- același număr de revizie cu alt conținut sau altă semnătură produce conflict;
- numele original este păstrat exclusiv ca metadată și nu poate controla calea de stocare;
- obiectele sunt adresate prin SHA-256 și deduplicate;
- metadatele sunt indexate tranzacțional în SQLite;
- indexul full-text acoperă identificatorul documentului, numele original și semnatarul;
- modificarea sau lipsa obiectului arhivat este detectată înainte de livrare.

## Structura locală

```text
var/archive/
  index.sqlite3
  objects/sha256/<prefix>/<digest>.blob
```

Fișierele sunt ignorate de Git. Codul nu expune calea fizică în contractele de produs, iar
înlocuirea depozitului local cu un adaptor object-storage nu schimbă serviciul de arhivare.

## Integrarea în flight

Flight-ul folosit de aplicație scrie în arhiva locală. Toate scenariile în care revizia
semnată este validă primesc același identificator de arhivă deduplicat; documentul modificat
după semnare este blocat înainte de arhivare. Evenimentul și identificatorul arhivei apar în
traseul deciziei, în dovezile scenariului și în exporturile JSON, NDJSON și Word.

## Limita D1

D1 livrează nucleul persistent și integrarea cu fluxul. Încărcarea utilizatorului, pagina de
explorare, previzualizarea și administrarea metadatelor sunt implementate în extensiile
D2–D3. Depozitul local este demonstrativ și nu reprezintă o arhivă electronică juridică.
