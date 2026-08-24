# DMS D2 — preluarea documentelor semnate

## Obiectiv

D2 adaugă în produs fluxul de preluare a unei revizii semnate. Utilizatorul furnizează
documentul PDF și dovada detașată a semnăturii în format JSON, iar SODIF decide fail-closed
dacă revizia poate intra în arhivă.

## Flux funcțional

1. sunt validate tipul, dimensiunea și structura PDF-ului;
2. digestul conținutului este comparat cu digestul acoperit de semnătură;
3. semnătura Ed25519 este verificată față de registrul local de încredere;
4. semnatarul, cheia și momentul semnării sunt validate;
5. revizia este confruntată cu istoricul persistent al documentului;
6. conținutul este arhivat și indexat numai dacă toate controalele reușesc;
7. utilizatorul primește identificatorul arhivei și amprenta documentului.

O reîncărcare identică este recunoscută și nu creează alt obiect sau altă înregistrare.
Același număr de revizie cu alt conținut, altă semnătură ori alt predecesor este respins.

## Interfața de produs

Pagina „Preluare documente” este inclusă în zona „Documente” a navigației. Aceasta oferă:

- încărcarea controlată a fișierului PDF și a dovezii JSON;
- mesaje explicite pentru integritate, încredere, semnătură și istoric;
- confirmarea arhivării cu document, revizie, semnatar, identificator și digest;
- un exemplu semnat verificabil, arhivabil imediat;
- un pachet ZIP reproductibil pentru testarea manuală a încărcării.

Interfața nu expune cheia privată, calea fizică a obiectului, excepții interne sau date din
document în mesajele de eroare.

## Persistență și compatibilitate

Indexul D1 este migrat automat pentru a păstra digestul reviziei precedente. Astfel,
serviciul de preluare poate reconstrui și valida istoricul după repornirea aplicației.
Schema, depozitul de obiecte și serviciul de preluare rămân independente de Streamlit.

## Limita D2

Profilul demonstrativ folosește registrul local de încredere și semnături detașate Ed25519.
Integrarea cu PAdES, certificate calificate, OCSP/CRL sau servicii externe de încredere este
o extensie ulterioară și nu este simulată ca fiind prezentă.
