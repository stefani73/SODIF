# Pasul 6 — motor de scenarii și flight demonstrativ

## Obiectiv

Integrarea mecanismelor validate separat într-un traseu reproductibil, ușor de demonstrat
și suficient de limitat pentru evaluarea TRL 4. Flight-ul nu depinde de rețea și nu produce
efecte într-un sistem extern.

## Catalogul minim

| Scenariu | Control demonstrat | Rezultat așteptat |
|---|---|---|
| Flux valid | extragerea structurală și prima cale OCR concordă | executat |
| Recuperare adaptivă | o dovadă lipsește; al doilea profil OCR o confirmă | executat |
| Document modificat | octeții diferă de digestul semnat | blocat |
| Conflict semantic | stratul structural ascuns diferă de pagina randată | escaladat |
| Acțiune modificată | ruta API diferă după emiterea permisului | blocat |
| Replay | permisul este prezentat a doua oară | blocat |

## Traseul integrat

1. revizia PDF este amprentată și verificată Ed25519;
2. provocarea post-semnătură selectează profilurile independente de extragere;
3. pypdf citește structura internă, iar MuPDF/Poppler cu Tesseract citesc paginile randate;
4. motorul de consens acceptă, extinde sau escaladează;
5. valorile stabile produc angajamente pe câmp și o rădăcină Merkle;
6. consensul acceptat este asamblat într-un manifest tipizat;
7. manifestul este compilat într-un plan API determinist;
8. dovada leagă fiecare parametru de câmpul aprobat, iar permisul semnează întregul context;
9. autorizarea este reverificată față de acțiunea exactă;
10. adaptorul API local emite o chitanță fără efect extern.

## Natura adaptoarelor semantice

Flight-ul procesează PDF-uri reale prin biblioteci OSS instalate local. Calea structurală
folosește pypdf. Căile vizuale randază documentul cu MuPDF și Poppler, apoi execută Tesseract
cu profiluri diferite. Fixture-ul de recuperare maschează numai disponibilitatea unui câmp pe
prima cale, păstrând valoarea extrasă real. Cazul de conflict conține simultan text structural
invizibil și o pagină vizibilă cu altă valoare, astfel încât blocarea rezultă din procesarea
efectivă a documentului.

## Dovada produsă

Fiecare scenariu conține rezultatul așteptat și observat, cronologia workflow-ului, observații
ordonate, digesturi de artefacte, nivelul și costul verificării, digestul provocării, rădăcina
câmpurilor, digestul dovezii de execuție, identificatorul permisului, codul de respingere sau
chitanța execuției. Flight-ul agregă cele șase rezultate într-un model JSON versionat.

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
