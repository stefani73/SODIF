# Reproducerea validării SODIF TRL 4

Pachetul de validare se construiește numai dintr-un checkout Git curat, aflat exact pe tagul release-ului. Dependențele Python se instalează din `requirements.lock`, iar componentele native sunt verificate față de `repro/toolchain.lock.json`.

1. Se creează mediul `.venv` cu Python 3.12.14.
2. Se instalează proiectul fără dependențe și apoi fișierul `requirements.lock`.
3. Se instalează Tesseract 5.5.0.20241111 cu limbile `eng` și `ron` și Poppler 26.07.0.
4. Se rulează `scripts/verify-toolchain.ps1`.
5. Din checkout-ul etichetat se rulează `scripts/build-trl4-release.ps1`.

Scriptul de release verifică toolchain-ul, execută Ruff, mypy și întreaga suită pytest cu branch coverage, generează cele trei rapoarte operaționale, arhivează sursa tagului și produce manifestul SHA-256 și pachetul de reproducere.
