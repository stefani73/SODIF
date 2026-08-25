# Operaționalizarea produsului și auditul automat

## Obiectiv

Aplicația SODIF funcționează ca un spațiu operațional configurabil. Identitatea organizației,
domeniul, mediul și limita API sunt valori validate care controlează rulările, apar în
rapoarte și sunt păstrate pe durata sesiunii active.

## Profilul operațional

Profilul conține:

- organizația și denumirea spațiului operațional;
- domeniul tranzacțional și mediul activ;
- serviciul protejat, ruta Gateway și audiența autorizată;
- resursa API și limita de complexitate a cererii;
- un identificator opac al sesiunii, utilizat exclusiv pentru separarea artefactelor.

Valorile inițiale provin din setări și pot fi modificate în interfață. Salvarea unei noi
configurații invalidează rezultatele vechi din sesiune, astfel încât rapoartele afișate să nu
poată fi confundate cu o altă politică operațională.

## Efectul configurației

Configurația nu este doar metadată de prezentare:

1. audiența și resursa definesc planul API compilat;
2. ruta, audiența și limitele configurează Semantic Execution Gateway;
3. organizația, domeniul, mediul și serviciul apar în raportul operațional;
4. configurația integrală este inclusă în raportul JSON și în manifest;
5. jurnalul NDJSON înregistrează contextul la deschiderea rulării;
6. identificatorul sesiunii separă fizic exporturile locale.

## Finalizarea unei rulări

La încheierea fiecărui flight sunt generate automat șase artefacte:

- raport operațional Word;
- raport complet JSON;
- jurnal tehnic NDJSON;
- manifest SHA-256;
- pachet ZIP portabil;
- chitanță JSON pentru înscrierea în registrul criptografic al rulărilor.

Scrierea fiecărui fișier este atomică. Destinația urmează structura
`<export-root>/<session>/<flight-kind>/<report-id>/`, ceea ce evită amestecarea rulărilor și
permite preluarea ulterioară de către un sistem de audit, CI/CD sau arhivare.

În plus, toate rulările sunt legate într-un registru NDJSON comun. Fiecare intrare include
amprenta intrării precedente și amprentele pachetului ZIP și manifestului curent. Registrul
este verificat integral înaintea unei noi înscrieri; un istoric sau un pachet modificat
blochează extinderea lanțului.

## Principii de produs

- limbajul interfeței descrie operațiuni, politici și audit, nu etape interne de dezvoltare;
- flight-urile sunt rulări controlate ale produsului, nu pagini separate de logică;
- formatele pentru oameni și sisteme provin din același model validat;
- schimbarea configurației nu necesită modificarea codului;
- modulele rămân separate, dar raportul transversal le corelează rezultatele.

## Criterii de acceptare

- valorile preconfigurate sunt vizibile și editabile într-o pagină dedicată;
- valorile modificate rămân disponibile la navigarea între pagini în aceeași sesiune;
- ruta și audiența configurate controlează efectiv Transversal Flight;
- fiecare flight produce automat toate cele șase artefacte și o intrare în registru;
- registrul detectează modificarea unei intrări, a manifestului sau a pachetului ZIP;
- rapoartele includ profilul operațional și identificatorii de trasabilitate;
- interfața nu expune termeni precum POC, TRL, pași interni sau justificări de dezvoltare.
