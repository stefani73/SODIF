# SODIF Multipage Product Experience

## Obiectiv

Interfața prezintă SODIF ca produs coerent, nu ca succesiune de componente demonstrative.
Navigația laterală retractabilă separă poziționarea comercială, explicația funcțională,
operațiunile și dovezile, păstrând aceeași stare pe durata sesiunii.

## Pagini

### Prezentare

- promisiunea centrală a produsului și lanțul de încredere;
- protecțiile oferite unei tranzacții derivate dintr-un document semnat;
- domenii de aplicabilitate formulate în limbaj orientat spre beneficiar;
- acces direct la demonstrația tehnică.

### Cum funcționează

- traseul de la verificarea documentului la execuția API;
- verificare adaptivă și permis criptografic de unică folosință;
- diferențierea față de controlul bazat exclusiv pe identitatea apelantului;
- poziționarea SODIF înaintea API-ului, direct sau împreună cu un gateway.

### Centru de control

- o singură acțiune principală pentru rularea demonstrației;
- rezultat executiv și explorarea celor șase situații;
- controale pentru document, intenția aprobată și execuție;
- motivul deciziei, efectul asupra API-ului, traseul și dovezile verificabile;
- acces explicit la pagina de rapoarte după finalizarea rulării.

### Rapoarte și dovezi

- identitatea și momentul sigilării raportului curent;
- pachet complet, raport Word, date JSON și jurnal de audit;
- amprentă vizibilă a pachetului și descrierea fiecărui artefact;
- îndrumare către centrul de control când sesiunea nu conține încă o rulare.

## Arhitectură UI

- `ui/shell.py` definește paginile, grupurile de navigație și cadrul vizual comun;
- `pages/` conține punctele de intrare native folosite de navigația Streamlit;
- `ui/pages/` conține suprafețe independente, extensibile cu domenii noi;
- `ui/state.py` gestionează raportul și exporturile comune sesiunii;
- `ui/presentation.py` păstrează vocabularul produsului separat de modelele tehnice;
- `ui/styles.py` definește sistemul vizual local și comportamentul responsive.

## Reguli de prezentare

Interfața folosește termeni românești naturali și iconografie Material furnizată nativ de
Streamlit. Nu sunt afișate versiuni, etape, framework-uri, identificatori ai nivelurilor
interne ori unități tehnice de cost. Identificatorii și amprentele apar numai unde sunt
necesare trasabilității.

## Criterii de acceptare

- meniul lateral este vizibil implicit și poate fi retras;
- cele patru pagini pornesc fără excepții și păstrează starea demonstrației;
- rularea și descărcările funcționează pe pagini separate;
- textele publice nu conțin vocabular intern sau formulări hibride inutile;
- acțiunile și navigația folosesc iconografie Material, fără emoji decorative;
- toate verificările de calitate și testele sunt verzi înainte de commit.
