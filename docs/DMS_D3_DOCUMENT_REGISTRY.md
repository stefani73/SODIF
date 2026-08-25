# DMS D3 — registrul documentelor

## Obiectiv

Registrul transformă arhiva verificabilă într-o zonă operațională a produsului. Utilizatorul
poate identifica un document, selecta revizia relevantă și consulta conținutul fără acces
direct la structura de stocare sau la baza de date.

## Capabilități

- sumar distinct pentru documente, revizii, semnatari și volum;
- căutare după identificator, nume de fișier sau semnatar;
- filtrare exactă după identitatea semnatarului;
- gruparea rezultatelor la nivelul documentului și acces la toate reviziile;
- previzualizare PDF și descărcare controlată;
- afișarea amprentei, semnatarului, momentelor relevante și legăturii cu revizia precedentă;
- acces direct din centrul de control după rularea demonstrației.

## Garanții tehnice

Registrul nu citește direct obiectele de pe disc. Deschiderea trece prin portul arhivei, care
recalculează SHA-256 și verifică dimensiunea înainte de a returna conținutul. Un obiect lipsă,
alterat sau inconsistent produce un răspuns fail-closed și nu este trimis previzualizării.

Căutarea rămâne limitată și tipizată. SQLite FTS5 indexează exclusiv metadatele declarate,
iar istoricul este ordonat după numărul reviziei și reconstruit din înregistrările persistente.
Interfața nu expune căi locale, interogări SQL sau mesaje interne ale excepțiilor.

## Extensibilitate

Serviciul read-only al registrului este separat de Streamlit și de implementarea SQLite.
Același contract poate susține ulterior control de acces, clasificări, retenție, semnături
PAdES și adaptoare pentru stocare locală, cloud sau hibridă.
