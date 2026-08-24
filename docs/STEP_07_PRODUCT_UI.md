# SODIF Product UI

## Obiectiv

Interfața prezintă SODIF ca produs de control al execuției, separând dovezile tehnice de
vocabularul intern al motorului. Landing page-ul comunică promisiunea produsului, iar
Assurance Flight demonstrează decizia și efectul asupra API-ului pentru fiecare situație.

## Suprafețe

### Prezentare

- poziționare Document-to-API trust layer;
- promisiunea „Exact ceea ce s-a semnat. O singură dată.”;
- lanțul de încredere: autenticitate, sens confirmat, permis unic și execuție controlată;
- protecțiile oferite și domeniile de aplicabilitate imediată.

### Assurance Flight

- stare inițială clară și o singură acțiune principală;
- rularea motorului flight real, fără duplicarea logicii în UI;
- verdict distinct pentru autorizare, blocare și revizuire;
- controale pentru document, sens aprobat și execuție;
- explicația deciziei, efectul asupra API-ului, traseul și dovezile verificabile;
- explorarea tuturor situațiilor dintr-un selector compact.

## Separarea responsabilităților

- `ui/shell.py` orchestrează navigarea și componentele Streamlit;
- `ui/presentation.py` traduce modelele domeniului în limbaj de produs;
- `ui/styles.py` definește sistemul vizual local, fără resurse externe;
- `demo/runner.py` rămâne sursa unică pentru execuția scenariilor.

## Reguli de prezentare

Interfața nu expune versiuni, etape de dezvoltare, framework-uri, porți de calitate,
unități interne de cost sau identificatori ai nivelurilor de procesare. Dovezile afișate
sunt limitate la elemente utile pentru trasabilitatea deciziei: amprente compacte,
identificatorul permisului, acțiunea, destinația și confirmarea API.

## Criterii de acceptare

- landing page-ul și Assurance Flight pornesc fără excepții;
- navigarea și acțiunea principală funcționează în aceeași sesiune;
- fiecare situație are verdict, controale, rațiune, efect API, traseu și dovezi;
- textele produsului nu expun vocabular intern;
- interfața este verificată vizual și funcțional în browser;
- toate testele și verificările de calitate sunt verzi înainte de commit.
