# SODIF

**Platformă de securitate cibernetică pentru controlul execuției digitale autorizate prin
documente semnate.**

SODIF menține continuitatea verificabilă dintre revizia semnată, intenția operațională,
permisul criptografic și cererea API observată la execuție.

Aplicația este organizată în trei module de produs cu limite și contracte explicite:

- **SODIF Security** — confruntă structura PDF cu forma randată și citită OCR, construiește
  dovada criptografică pe câmp și emite permisul cu utilizare unică legat de acțiunea API;
- **SODIF Archive** — păstrează reviziile validate, istoricul criptografic și pachetele
  portabile pentru verificare independentă;
- **SODIF Gateway** — recanonicalizează cererea API, verifică proveniența fiecărui parametru,
  legarea de permis și protecția anti-replay la limita de execuție.

Interfața multipagină individualizează fiecare modul, operațiunile documentare, rulările
controlate și auditul. Catalogul comun din `src/sodif/product/` păstrează identitatea, promisiunea și
contractele modulelor sincronizate în întreaga aplicație.

Pagina Gateway include un `Policy Studio` funcțional. Tranzacțiile conforme sunt autorizate
și rutate prin adaptorul protejat, iar modificarea parametrilor sau reutilizarea permisului
sunt blocate înainte de API. Fiecare evaluare produce o decizie JSON exportabilă cu verificările
aplicate, amprenta requestului și efectul asupra serviciului destinație.

Pagina „Preluare documente” validează perechea PDF + dovadă de semnătură JSON înainte de
arhivare. Exemplul inclus construiește două revizii succesive: a doua este acceptată numai
dacă indică exact amprenta reviziei precedente. Setul semnat poate fi descărcat pentru
reîncărcare manuală.

Pagina „Registru documente” oferă căutare, filtrare, previzualizare PDF, istoricul verificabil
al reviziilor și un pachet portabil cu document, istoric, manifest criptografic și instrucțiuni
de verificare offline. Conținutul este furnizat interfeței numai după ce arhiva îi reconfirmă
dimensiunea și amprenta criptografică.

## Pornire locală

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run src\sodif\app.py
```

Alternativ:

```powershell
.\scripts\run.ps1
```

## Demonstrație tehnică

```powershell
.\scripts\flight.ps1
```

Comanda rulează Security Flight și afișează dovada structurată JSON, fără efecte asupra unui
sistem extern și fără scrieri în DMS.

Aplicația oferă două rulări distincte:

- **Security Flight** — nucleul de semnătură și securitate: integritate, extragere PDF reală
  prin pypdf și două trasee vizuale randate diferit, citite cu același motor Tesseract,
  invariabilitate pe câmp, permis unic, legarea acțiunii API și protecția anti-replay;
- **Transversal Flight** — traversează cele trei module: verifică și autorizează intenția,
  arhivează reviziile acceptate, aplică permisul în SODIF Gateway și exportă deciziile corelate.
  Documentele respinse nu sunt arhivate, iar cererile neconforme nu ajung la API.

## Configurarea modulelor

Toate modulele sunt active implicit. Expunerea lor în navigație poate fi controlată fără
modificarea codului:

```text
SODIF_MODULE_SECURITY_ENABLED=true
SODIF_MODULE_ARCHIVE_ENABLED=true
SODIF_MODULE_GATEWAY_ENABLED=true
SODIF_GATEWAY_ROUTE_ID=erp.purchase-orders
SODIF_GATEWAY_AUDIENCE=erp-purchase-api
SODIF_GATEWAY_PATH_PREFIX=/purchase-orders
SODIF_GATEWAY_MAXIMUM_PARAMETERS=16
SODIF_ORGANIZATION_NAME=TECHSUITE SRL
SODIF_WORKSPACE_NAME=SODIF Operations
SODIF_DOMAIN_NAME=Achiziții
SODIF_PROTECTED_SERVICE=ERP Purchase API
SODIF_EXPORT_ROOT=var/exports
SODIF_TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
SODIF_PDFTOPPM_CMD=C:\path\to\pdftoppm.exe
```

Pentru variabilele `*_ENABLED`, valorile acceptate sunt `true/false`, `yes/no`, `on/off` și
`1/0`. Identificatorii și prefixul rutei sunt validați, iar limita parametrilor este numerică.
Configurațiile ambigue sunt respinse la pornire.

Extragerea vizuală necesită Tesseract cu limbile `ron` și `eng`; al doilea profil de randare
folosește `pdftoppm` din Poppler. Căile sunt detectate automat când executabilele sunt în
`PATH` și pot fi fixate explicit prin variabilele de mai sus.

Configurația TRL 4 validează în laborator motorul de securitate, controlul Gateway și
arhivarea locală. Cele două trasee vizuale diferă prin renderer, rezoluție și segmentare, dar
folosesc același motor OCR. Gateway-ul execută politicile și verificările criptografice reale,
iar sistemul API destinație este reprezentat printr-un adaptor local fără efect extern.

Valorile sunt preconfigurate din mediu și pot fi ajustate în pagina „Configurare
operațională”. Modificările sunt validate, păstrate în sesiunea activă și utilizate efectiv
de flight-uri, politicile Gateway și rapoarte.

## Audit și exporturi

La finalul fiecărui flight, aplicația scrie automat raportul Word, datele JSON, jurnalul
NDJSON, manifestul de integritate, pachetul ZIP și chitanța registrului criptografic. Fiecare
pachet este înscris într-un lanț anti-tamper comun, verificat înaintea unei noi înscrieri.
Pagina „Audit și exporturi” permite descărcarea artefactelor, a chitanței și a registrului
criptografic. Pentru Transversal Flight, jurnalul include fiecare decizie
Gateway, controalele aplicate, amprentele acțiunii și dovada execuției sau blocării.

Fișierele sunt organizate pe sesiune, tip de flight și identificatorul rulării:

```text
var/exports/<session>/<security|transversal>/<report-id>/
var/exports/sodif-run-integrity-ledger.ndjson
```

Export local:

```powershell
.\scripts\export-flight.ps1
```

Comanda rulează ambele Flight-uri și generează în `var\exports` rapoartele DOCX, datele JSON,
jurnalele NDJSON, manifestele SHA-256 și pachetele ZIP.

## Verificare integrală

```powershell
.\scripts\quality.ps1
```

Comanda execută analiza statică, verificarea tipurilor și toate testele cu prag minim de
acoperire de 85%.

## Structură

- `src/sodif/` — codul aplicației;
- `src/sodif/product/` — catalogul și limitele celor trei module de produs;
- `src/sodif/gateway/` — politicile de rutare și motorul semantic `route/block`;
- `src/sodif/domain/` — modele, stări, canonicalizare și contracte independente de UI;
- `src/sodif/documents/` — verificarea semnăturii, a conținutului și a lanțului de revizii;
- `src/sodif/archive/` — depozit documentar, index SQLite și verificarea integrității;
- `src/sodif/verification/` — risc explicabil, normalizare, consens și rutare adaptivă;
- `src/sodif/extraction/` — extragere structurală pypdf și randare OCR MuPDF/Poppler;
- `src/sodif/invariance/` — provocare post-semnătură, angajamente pe câmp și dovada legării
  parametrilor API;
- `src/sodif/permits/` — emiterea, verificarea și consumul unic al permiselor de execuție;
- `src/sodif/execution/` — manifest, compilare și adaptor API controlat;
- `src/sodif/demo/` — catalogul și motorul flight-ului reproductibil;
- `src/sodif/reporting/` — raport Word, serializări, pachet de audit și registrul anti-tamper;
- `src/sodif/ui/pages/` — pagini de produs și operațiuni independente;
- `tests/` — teste unitare și smoke tests;
- `docs/` — decizii, specificații și criterii de acceptare;
- `var/logs/` — loguri locale generate la rulare;
- `var/exports/` — rapoarte și pachete exportate;
- `var/archive/` — indexul și obiectele documentare generate local;
- `scripts/` — comenzi reproductibile pentru rulare și calitate.

Interfața rulează direct motorul operațional, prezintă deciziile și oferă exporturi
verificabile pentru analiză umană, audit automat și arhivare.
