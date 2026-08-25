# SODIF POC

**Signed Intent Execution** — controlul execuției digitale autorizate prin documente semnate.

Promisiunea produsului: **Exact ceea ce s-a semnat. O singură dată.**

Acest repository conține demonstratorul TRL 4 realizat incremental. Interfața multipagină
separă prezentarea produsului, explicația funcțională, centrul de control și zona de
rapoarte și dovezi. Reviziile semnate validate sunt păstrate într-o arhivă locală
verificabilă, deduplicată și indexată.

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

Aplicația oferă două demonstrații distincte:

- **Security Flight** — nucleul de semnătură și securitate: integritate, consens adaptiv,
  permis unic, legarea acțiunii API și protecția anti-replay;
- **Integrated Flight** — același nucleu, completat cu arhivarea unui lanț de revizii,
  registrul documentar și exportul verificabil. Documentele respinse nu sunt arhivate.

## Pachet de dovezi

După rularea demonstrației din centrul de control, pagina „Rapoarte și dovezi” permite
descărcarea raportului Word, a datelor JSON, a jurnalului de audit și a pachetului complet
cu manifest de integritate.

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

Interfața rulează direct motorul demonstrativ, prezintă deciziile și oferă exporturi
verificabile pentru evaluare umană, audit automat și arhivare.
