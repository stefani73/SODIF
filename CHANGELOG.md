# Changelog

## 0.3.0 — Pasul 3

- validare minimală și limitare de dimensiune pentru artefacte PDF;
- semnătură detașată Ed25519 peste metadate canonice și digestul conținutului;
- registru local de chei de încredere, cu perioadă de activitate și revocare;
- lanț atomic de revizii care blochează salturi, ramificații și reutilizarea conținutului;
- coduri de respingere stabile și teste pentru modificare, chei nevalide și istoric inconsistent.

## 0.2.0 — Pasul 2

- modele de domeniu imutabile, stricte și versionabile;
- contracte pentru document, risc, consens, compilare și evidență;
- canonicalizare JSON deterministă și digesturi SHA-256;
- schemă generică pentru intenția operațională;
- mașină de stări pură, cu tranziții fail-closed;
- teste unitare și de arhitectură pentru independența față de Streamlit.

## 0.1.0 — Pasul 1

- structură modulară `src/`;
- mediu Python izolat și dependențe reproductibile;
- shell Streamlit minimal, cu identitate vizuală SODIF;
- porți automate: Ruff, mypy, pytest și coverage;
- documentație de continuitate și criterii de acceptare.
