# Pasul 2 — nucleul de domeniu SODIF

## Obiectiv

Stabilirea limbajului tehnic comun și a contractelor care vor rămâne stabile când sunt
adăugate parsere PDF, modele AI, politici, criptografie, API-uri și interfața completă.

## Livrabile

- modele imutabile pentru document, semnături, vederi semantice și consens;
- manifest de intenție și plan de execuție tipizat;
- scheme versionate pentru câmpurile care produc efect;
- evaluare de risc și context de acțiune ca obiecte de domeniu;
- canonicalizare RFC 8785 și digest SHA-256;
- mașină de stări cu tranziții explicite și stări terminale;
- protocoale Python pentru toate componentele extensibile.

## Invariante

- orice obiect respinge câmpurile necunoscute și mutarea după creare;
- orice digest are forma `sha256:` urmată de 64 de caractere hexazecimale;
- identificatorii de câmp sunt unici într-o vedere, schemă, manifest sau plan;
- rezultatul global al consensului este derivabil din starea câmpurilor;
- un manifest conține numai valori acceptate, cu surse și digesturi de proveniență;
- un plan de execuție este legat de digestul manifestului și nu acceptă rute ambigue;
- stările `executed` și `blocked` sunt terminale;
- nucleul de domeniu nu importă Streamlit și nu efectuează I/O.

## În afara Pasului 2

Nu se validează încă semnături PDF, nu se extrag valori, nu se calculează consensul, nu se
emit permise și nu se apelează API-uri. Pasul livrează contractele și regulile pure pe care
se vor baza aceste implementări.

## Criterii de acceptare

- toate modelele valide se serializează și se reconstruiesc fără pierderi;
- datele invalide sau ambigue sunt respinse explicit;
- canonicalizarea este stabilă indiferent de ordinea cheilor;
- tranzițiile nepermise și timpul ne-monoton sunt blocate;
- validarea schemei raportează determinist toate încălcările;
- Ruff, mypy strict și întreaga suită pytest sunt integral verzi;
- acoperirea codului rămâne peste pragul proiectului;
- repository-ul este curat după commitul separat al Pasului 2.

