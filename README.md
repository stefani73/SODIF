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

## Verificare integrală

```powershell
.\scripts\quality.ps1
```

Comanda execută analiza statică, verificarea tipurilor și toate testele cu prag minim de
acoperire de 85%.

## Structură

- `src/sodif/` — codul aplicației;
- `tests/` — teste unitare și smoke tests;
- `docs/` — decizii, specificații și criterii de acceptare;
- `var/logs/` — loguri locale generate la rulare;
- `var/exports/` — rapoarte și pachete exportate;
- `scripts/` — comenzi reproductibile pentru rulare și calitate.

Logica funcțională SODIF nu este inclusă în Pasul 1; va fi introdusă modular, în pașii
validați ulterior.

