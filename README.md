# SODIF POC

**Signed Intent Execution** — controlul execuției digitale autorizate prin documente semnate.

Promisiunea produsului: **Exact ceea ce s-a semnat. O singură dată.**

Acest repository conține demonstratorul TRL 4 realizat incremental. Interfața include o
prezentare orientată spre produs și un Assurance Flight interactiv pentru verificarea
deciziilor de autorizare, blocare și escaladare.

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

Interfața rulează direct motorul flight și prezintă verdictul, controalele, efectul asupra
API-ului, traseul deciziei și dovezile verificabile. Exporturile de raport sunt livrate
separat în etapa următoare.
