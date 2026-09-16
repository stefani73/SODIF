# Rezumat tehnic de continuitate

## Esența produsului

SODIF transformă intenția aprobată într-un document semnat într-o singură acțiune digitală
controlată, trasabilă și protejată împotriva modificării sau repetării.

## Nucleul diferențiator

Mecanismul **Execution-Bound Semantic Invariance** leagă verificabil:

1. revizia efectiv semnată;
2. câmpurile care produc efect;
3. proveniența structurală și vizuală a valorilor critice;
4. politica aplicată;
5. metoda, ruta și corpul cererii API;
6. angajamentele pe câmp și rădăcina Merkle a valorilor aprobate;
7. dovada integrală a legării parametrilor API de câmpurile aprobate;
8. un permis criptografic cu durată scurtă și consum unic;
9. dovada execuției sau a blocării;
10. înregistrarea verificabilă a reviziei acceptate în arhiva documentară locală;
11. preluarea controlată a perechii document–semnătură și continuitatea versiunilor;
12. consultarea documentului și a istoricului său printr-un registru care reverifică
    integritatea la fiecare deschidere.

Verificarea este adaptivă. Câmpurile critice sunt extrase din structura PDF și din randări OCR
independente. Procesarea extinsă este activată când dovezile inițiale sunt insuficiente sau
divergente. Orice extractor suplimentar rămâne o sursă cu proveniență verificată în consens.

## Flight-uri demonstrative TRL 4

Demonstratorul folosește un singur tip de document controlat — o comandă de achiziție PDF — și o
singură acțiune controlată local: `POST /purchase-orders`.

Aceleași situații sunt disponibile în două demonstrații: **Security Flight**, care izolează
nucleul tehnic de semnătură și securitate fără scrieri DMS, și **Transversal Flight**, care
traversează SODIF Security, SODIF Archive și SODIF Gateway până la
execuția sau blocarea API.

Situațiile obligatorii sunt:

- **S1 — execuție validă:** permis emis, exact o comandă creată;
- **S2 — conflict semantic:** PDF-ul afișează `1250.00`, stratul intern expune `9250.00`,
  consens eșuat și zero execuții;
- **S3 — payload modificat:** digest diferit, cerere blocată;
- **S4 — replay:** a doua utilizare a permisului este respinsă.

Registrul poate exporta documentul selectat împreună cu istoricul reviziilor, manifestul
SHA-256 și instrucțiunile necesare verificării offline.

## Principii de implementare

- nucleul nu depinde de Streamlit;
- toate contractele sunt tipizate și versionate;
- deciziile de autorizare sunt deterministe și fail-closed;
- adaptatoarele de document, AI și API sunt înlocuibile;
- logurile și dovezile nu includ implicit documentul integral;
- fiecare pas păstrează toate testele anterioare verzi;
- fiecare flight poate fi reprodus fără servicii comerciale externe.

## Limita demonstratorului

Demonstratorul nu implementează infrastructura completă a unui API Gateway, Kubernetes,
multi-cloud, arhivă juridică,
HSM de producție, integrare EUDI sau execuții financiare reale. Interfețele vor permite
adăugarea ulterioară a acestor capabilități fără schimbarea nucleului.
