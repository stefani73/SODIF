# Pasul 1 — criterii de acceptare

Pasul este considerat finalizat numai dacă:

- mediul virtual este localizat în `.venv` și folosește Python 3.12;
- proiectul poate fi instalat în mod editabil;
- `streamlit run src/sodif/app.py` pornește fără excepții;
- Ruff nu raportează încălcări;
- mypy rulează în mod strict fără erori;
- toate testele pytest trec;
- acoperirea codului este de minimum 85%;
- nu există secrete sau artefacte runtime urmărite de Git;
- dependențele instalate sunt salvate cu versiuni exacte;
- repository-ul Git este inițializat și starea lui este verificabilă.

Pasul 1 nu include procesarea documentelor, consens semantic, criptografie de execuție sau
scenariile funcționale SODIF.

