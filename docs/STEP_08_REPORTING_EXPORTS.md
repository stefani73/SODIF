# SODIF Reporting and Evidence Exports

## Obiectiv

O singură rulare Assurance Flight produce atât o explicație pentru evaluare umană, cât și
dovezi verificabile automat. Toate formatele provin din același `FlightReport`; interfața
nu reconstruiește și nu modifică rezultatul motorului.

## Artefacte

- `SODIF_Assurance_Flight_Report.docx` — raport Word pentru evaluare, demonstrații și dosar;
- `sodif-flight-report.json` — reprezentarea completă a rezultatului de domeniu;
- `sodif-audit-log.ndjson` — evenimente ordonate pentru ingestie și audit;
- `sodif-evidence-manifest.json` — dimensiuni și amprente SHA-256 pentru fiecare artefact;
- `SODIF_Evidence_Package.zip` — pachetul complet, cu timestamp-uri ZIP normalizate.

## Raportul Word

Raportul folosește presetul `standard_business_brief` și modelul de deschidere
`memo_masthead`. Include:

- identitatea raportului, rezultatul și momentul sigilării;
- concluzia executivă;
- registrul comparabil al deciziilor și efectelor API;
- câte o fișă pentru fiecare situație, cu verdict, controale, rațiune, traseu și dovezi;
- antet discret și subsol cu identificatorul raportului și numărul paginii.

Geometria paginii, stilurile, spațierile și tabelul sunt definite explicit. Documentul este
normalizat la nivel OOXML/ZIP pentru a produce aceiași octeți din aceeași dovadă.

## Integritate și reproductibilitate

Manifestul înregistrează tipul media, dimensiunea și digestul SHA-256 al raportului Word,
al raportului JSON și al jurnalului. `evidence_root` leagă amprentele într-o rădăcină unică.
Arhiva folosește ordine stabilă, compresie fixă și timestamp-uri normalizate.

## Utilizare

Din interfață, după rularea Assurance Flight, sunt disponibile pachetul complet, raportul
Word, dovezile JSON și jurnalul auditabil.

Pentru export local reproductibil:

```powershell
.\scripts\export-flight.ps1
```

Fișierele sunt scrise atomic în `var/exports/`.

## Criterii de acceptare

- exporturi identice pentru două rulări ale aceluiași raport;
- raport JSON reîncărcabil în modelul strict `FlightReport`;
- jurnal NDJSON parseabil, ordonat și închis cu eveniment de sigilare;
- manifest coerent cu artefactele din ZIP;
- raport DOCX valid structural și verificat prin randarea tuturor paginilor;
- descărcări funcționale din Streamlit;
- toate testele și verificările de calitate verzi înainte de commit.
