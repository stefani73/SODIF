# SODIF

**Signed Intent Infrastructure** — controlul tranzacțiilor digitale autorizate prin documente
semnate.

Promisiunea produsului: **Exact ceea ce s-a semnat. O singură dată.**

Aplicația este organizată în trei module de produs cu limite și contracte explicite:

- **Signed Intent Security** — verifică documentul și intenția, apoi emite permisul
  criptografic legat de acțiunea API autorizată;
- **Verifiable Document Archive** — păstrează reviziile validate, istoricul criptografic și
  pachetele portabile de dovezi;
- **Semantic Execution Gateway** — verifică permisul față de cererea API, aplică politicile
  de rutare și produce decizia auditabilă `route/block` la limita de execuție.

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

- **Security Flight** — nucleul de semnătură și securitate: integritate, consens adaptiv,
  permis unic, legarea acțiunii API și protecția anti-replay;
- **Transversal Flight** — traversează cele trei module: verifică și autorizează intenția,
  arhivează reviziile acceptate, aplică permisul în Gateway și exportă deciziile corelate.
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
SODIF_ORGANIZATION_NAME=PowerNet
SODIF_WORKSPACE_NAME=SODIF Transaction Control
SODIF_DOMAIN_NAME=Achiziții
SODIF_PROTECTED_SERVICE=ERP Purchase API
SODIF_EXPORT_ROOT=var/exports
```

Pentru variabilele `*_ENABLED`, valorile acceptate sunt `true/false`, `yes/no`, `on/off` și
`1/0`. Identificatorii și prefixul rutei sunt validați, iar limita parametrilor este numerică.
Configurațiile ambigue sunt respinse la pornire.

Valorile sunt preconfigurate din mediu și pot fi ajustate în pagina „Configurare
operațională”. Modificările sunt validate, păstrate în sesiunea activă și utilizate efectiv
de flight-uri, politicile Gateway și rapoarte.

## Audit și exporturi

La finalul fiecărui flight, aplicația scrie automat raportul Word, datele JSON, jurnalul
NDJSON, manifestul de integritate și pachetul ZIP. Pagina „Audit și exporturi” permite
descărcarea acelorași artefacte
cu manifest de integritate. Pentru Transversal Flight, jurnalul include fiecare decizie
Gateway, controalele aplicate, amprentele acțiunii și dovada execuției sau blocării.

Fișierele sunt organizate pe sesiune, tip de flight și identificatorul rulării:

```text
var/exports/<session>/<security|transversal>/<report-id>/
```

Export local:

```powershell
.\scripts\export-flight.ps1
```

Fișierele sunt generate în `var\exports`.

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
- `src/sodif/permits/` — emiterea, verificarea și consumul unic al permiselor de execuție;
- `src/sodif/execution/` — manifest, compilare și adaptor API controlat;
- `src/sodif/demo/` — catalogul și motorul flight-ului reproductibil;
- `src/sodif/reporting/` — raport Word, serializări și pachet de dovezi;
- `src/sodif/ui/pages/` — pagini de produs și operațiuni independente;
- `tests/` — teste unitare și smoke tests;
- `docs/` — decizii, specificații și criterii de acceptare;
- `var/logs/` — loguri locale generate la rulare;
- `var/exports/` — rapoarte și pachete exportate;
- `var/archive/` — indexul și obiectele documentare generate local;
- `scripts/` — comenzi reproductibile pentru rulare și calitate.

Interfața rulează direct motorul operațional, prezintă deciziile și oferă exporturi
verificabile pentru analiză umană, audit automat și arhivare.
