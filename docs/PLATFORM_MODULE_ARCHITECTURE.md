# Arhitectura modulară a platformei SODIF

## Scop

SODIF controlează continuitatea dintre aprobarea exprimată într-un document semnat și
acțiunea digitală care produce efectul. Platforma separă acest lanț în trei module cu
responsabilități, intrări și rezultate verificabile. Separarea permite extinderea pe domenii,
integrarea cu servicii externe și evoluția independentă a componentelor fără pierderea
garanțiilor comune.

## Module de produs

### Signed Intent Security

**Responsabilitate:** validează documentul și revizia, confirmă semantic valorile critice și
emite un permis criptografic legat de acțiunea API exactă.

- intrare: document semnat, dovada semnăturii, reprezentări independente ale intenției și
  acțiunea solicitată;
- control: integritate, consens semantic adaptiv, evaluare explicabilă a riscului, legarea
  metodei/rutei/parametrilor/destinației și protecție anti-replay;
- ieșire: decizie justificată și permis cu utilizare unică sau refuz fără efect extern.

Modulul nu arhivează documente și nu rutează trafic. Contractul său stabil este decizia
semnată împreună cu permisul de execuție.

### Verifiable Document Archive

**Responsabilitate:** păstrează documentele validate și relațiile dintre revizii într-o formă
care poate fi verificată independent.

- intrare: document validat, metadate semnate și amprenta reviziei precedente;
- control: deduplicare, continuitatea lanțului de revizii, integritate la citire și indexare;
- ieșire: înregistrare căutabilă, istoric verificabil și pachet portabil de dovezi.

Modulul nu interpretează intenția și nu autorizează execuții. El păstrează dovada exactă pe
care celelalte componente o pot referi.

### Semantic Execution Gateway

**Responsabilitate:** aplică dreptul tranzacțional la limita API și permite numai acțiunea
descrisă de permis.

- intrare: cerere API, permis criptografic și contextul serviciului destinație;
- control: autenticitatea și expirarea permisului, potrivirea exactă a metodei/rutei/
  parametrilor, audiența, mediul și consumul unic;
- ieșire: rutare permisă sau blocare motivată, însoțită de jurnalul deciziei.

Gateway-ul completează autentificarea, rate limiting-ul și rutarea clasică. Diferențiatorul
SODIF este verificarea relației dintre tranzacția cerută și intenția aprobată în document.

## Lanțul de încredere

```text
Document semnat
    -> verificare și consens semantic
    -> permis criptografic legat de acțiune
    -> arhivarea reviziei și a dovezilor
    -> enforcement asupra cererii API
    -> rutare sau blocare auditabilă
```

Security Flight izolează primul modul și demonstrează garanțiile nucleului. Fluxul transversal
va utiliza contractele tuturor celor trei module, fără a le amesteca responsabilitățile.

## Reguli arhitecturale

1. Modelele de domeniu și contractele nu depind de Streamlit.
2. Niciun modul nu deduce implicit rezultatul altui modul; schimbul se face prin artefacte
   explicite și versionate.
3. Orice decizie cu efect extern este fail-closed și produce o explicație auditabilă.
4. Extensiile de domeniu adaugă scheme, politici și adaptoare; nu modifică mecanismele
   criptografice comune.
5. UI-ul orchestrează cazuri de utilizare, dar nu conține logica de securitate.
6. Configurarea expunerii modulelor se face prin setări validate, nu prin ramificații ad-hoc.

## Configurare

Modulele sunt active implicit și pot fi expuse selectiv în shell prin:

- `SODIF_MODULE_SECURITY_ENABLED`;
- `SODIF_MODULE_ARCHIVE_ENABLED`;
- `SODIF_MODULE_GATEWAY_ENABLED`.

Sunt acceptate exclusiv valori booleene explicite. Catalogul canonic
`src/sodif/product/catalog.py` furnizează numele, promisiunea și contractul fiecărui modul.

## Criterii de acceptare ale separării modulare

- navigația prezintă distinct platforma, cele trei module și zona demonstrațiilor;
- fiecare modul are o pagină proprie și un contract intrare–control–ieșire;
- operațiunile de preluare și registru aparțin exclusiv arhivei;
- nicio pagină nu expune denumiri de pași interni, stări de dezvoltare sau justificări de
  implementare;
- dezactivarea unui modul îl elimină din navigație fără modificarea codului;
- analiza statică, verificarea tipurilor și toate testele trec integral.
