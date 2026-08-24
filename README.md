# SODIF POC

**Signed Intent Execution** — controlul execuției digitale autorizate prin documente semnate.

Promisiunea produsului: **Exact ceea ce s-a semnat. O singură dată.**

Acest repository conține demonstratorul TRL 4 realizat incremental. Fiecare pas este
acceptat numai după trecerea integrală a testelor automate și a verificărilor de calitate.

## Pornire locală

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run src\sodif\app.py
```

Alternativ:

```powershell
.\scripts\run.ps1
```

## Flight demonstrativ

```powershell
.\scripts\flight.ps1
```

Comanda rulează catalogul reproductibil de șase scenarii și afișează dovada structurată
JSON, fără efecte asupra unui sistem extern.

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
- `tests/` — teste unitare și smoke tests;
- `docs/` — decizii, specificații și criterii de acceptare;
- `var/logs/` — loguri locale generate la rulare;
- `var/exports/` — rapoarte și pachete exportate;
- `scripts/` — comenzi reproductibile pentru rulare și calitate.

Pasul 6 integrează validarea documentului, consensul adaptiv, permisul și execuția controlată
în șase scenarii reproductibile. Interfața completă și exporturile de raport sunt implementate
în pașii următori.
