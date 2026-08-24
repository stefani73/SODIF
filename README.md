# SODIF POC

**Signed Intent Execution** — controlul execuției digitale autorizate prin documente semnate.

Promisiunea produsului: **Exact ceea ce s-a semnat. O singură dată.**

Acest repository conține demonstratorul TRL 4 realizat incremental. Interfața multipagină
separă prezentarea produsului, explicația funcțională, centrul de control și zona de
rapoarte și dovezi.

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

Comanda rulează catalogul reproductibil de șase situații și afișează dovada structurată
JSON, fără efecte asupra unui sistem extern.

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
- `scripts/` — comenzi reproductibile pentru rulare și calitate.

Interfața rulează direct motorul demonstrativ, prezintă deciziile și oferă exporturi
verificabile pentru evaluare umană, audit automat și arhivare.
