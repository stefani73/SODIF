# Dovada de invariabilitate semantică legată de execuție

## Scop

Mecanismul urmărește ca valorile văzute și aprobate în documentul semnat să rămână aceleași
în acțiunea API executată. Controlul operează la nivel de câmp și păstrează proveniența
tehnică a fiecărei valori.

## Flux implementat

1. Revizia și semnătura sunt validate peste conținutul PDF primit.
2. După această validare, un nonce al serverului generează provocarea semantică și ordinea
   profilurilor vizuale folosite în rulare.
3. `pypdf` citește structura internă a documentului.
4. MuPDF la 300 DPI cu Tesseract PSM 6 citește forma randată a paginii.
5. La extinderea adaptivă, Poppler la 360 DPI cu Tesseract PSM 11 produce a doua dovadă
   vizuală.
6. Valorile sunt normalizate conform schemei: identificator, număr zecimal, monedă, dată,
   întreg, boolean sau text.
7. Un câmp critic este stabil numai când dovezile structurale și vizuale concordă. Un
   dezacord calificat conduce la escaladare.
8. Pentru fiecare câmp stabil se calculează un angajament SHA-256 care acoperă numele, tipul,
   valoarea, caracterul critic și referințele de proveniență.
9. Angajamentele ordonate formează o rădăcină Merkle a valorilor aprobate.
10. Fiecare parametru API este asociat cu un câmp stabil; valoarea canonică, locația
    parametrului și angajamentul câmpului intră în rădăcina legăturilor de execuție.
11. Permisul Ed25519 acoperă dovada, rădăcina câmpurilor, provocarea și digestul acțiunii.
12. Gateway-ul reverifică integral dovada și consumă permisul atomic la prima rutare validă.

## Caz de securitate demonstrat

Scenariul `semantic-conflict` folosește un PDF valid în care pagina randată arată totalul
`1250.00`, iar stratul structural invizibil expune `9250.00`. Calea structurală și cele două
căi OCR produc rezultate observabile diferite. Consensul critic este escaladat, dovada de
execuție nu este creată, permisul nu este emis, iar API-ul rămâne neapelat.

## Proprietăți verificabile

- provocarea depinde de revizie, politica aplicată, dovezile semnăturii și nonce-ul serverului;
- câmpurile critice cer simultan proveniență structurală și vizuală;
- fiecare parametru API are acoperire completă într-un angajament al câmpului;
- modificarea valorii, provenienței, rădăcinii, metodei, rutei ori destinației invalidează
  dovada sau permisul;
- permisul produce cel mult o singură execuție;
- raportul și jurnalul exportă digestul provocării, rădăcina câmpurilor și digestul dovezii.

## Limita validării

Implementarea validează mecanismul în mediu de laborator, pentru schema controlată a unei
comenzi de achiziție și un API local. Profilele, schemele și adaptoarele sunt contracte
modulare care permit introducerea altor tipuri de documente și motoare de extragere.

Cele două trasee vizuale sunt distincte prin renderer, DPI și segmentare, dar folosesc același
motor OCR Tesseract. Diversificarea cu motoare OCR/HTR independente și integrarea cu un API
extern aparțin etapelor ulterioare de dezvoltare și validare.
