# Pasul 6 — motor de scenarii și flight demonstrativ

## Obiectiv

Integrarea mecanismelor validate separat într-un traseu reproductibil, ușor de demonstrat
și suficient de limitat pentru evaluarea TRL 4. Flight-ul nu depinde de rețea și nu produce
efecte într-un sistem extern.

## Catalogul minim

| Scenariu | Control demonstrat | Rezultat așteptat |
|---|---|---|
| Flux valid | două reprezentări concordă; a treia nu rulează | executat |
| Recuperare adaptivă | o dovadă lipsește; a treia cale o confirmă | executat |
| Document modificat | octeții diferă de digestul semnat | blocat |
| Conflict semantic | valoarea critică diferă între reprezentări | escaladat |
| Acțiune modificată | ruta API diferă după emiterea permisului | blocat |
| Replay | permisul este prezentat a doua oară | blocat |

## Traseul integrat

1. revizia PDF este amprentată și verificată Ed25519;
2. riscul selectează nivelul inițial de verificare;
3. adaptoarele flight-ului produc reprezentări controlate și complet trasabile;
4. motorul de consens acceptă, extinde sau escaladează;
5. consensul acceptat este asamblat într-un manifest tipizat;
6. manifestul este compilat într-un plan API determinist;
7. permisul unic leagă criptografic verificarea de plan;
8. autorizarea este verificată față de acțiunea exactă;
9. adaptorul API local emite o chitanță fără efect extern.

## Natura adaptoarelor semantice

Flight-ul folosește adaptoare controlate cu rezultate explicite, astfel încât evaluarea să
fie reproductibilă și să nu depindă de un model extern. Aceste adaptoare reprezintă ieșirile
unui parser structural, ale unei căi vizuale și ale validării orientate spre API. Mecanismul
de consens, costul adaptiv, criptografia și protecțiile sunt executate real; conectarea unui
OCR/model AI OSS se poate face ulterior prin același contract.

## Dovada produsă

Fiecare scenariu conține rezultatul așteptat și observat, cronologia workflow-ului, observații
ordonate, digesturi de artefacte, nivelul și costul verificării, identificatorul permisului,
codul de respingere sau chitanța execuției. Flight-ul agregă cele șase rezultate într-un model
JSON versionat; exportul în fișiere și raportul prezentabil apar în Pasul 8.

## Rulare

```powershell
.\scripts\flight.ps1
```

## Criterii de acceptare

- toate cele șase scenarii produc rezultatul așteptat;
- fluxul valid economisește costul celei de-a treia căi;
- extensia adaptivă rulează exact când dovada este insuficientă;
- niciun scenariu blocat sau escaladat nu produce chitanță API;
- rulările repetate produc aceeași dovadă structurată;
- Ruff, mypy strict și întreaga suită pytest sunt integral verzi;
- repository-ul este curat după commitul separat al Pasului 6.
