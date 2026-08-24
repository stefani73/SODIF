# Rezumat tehnic de continuitate

## Esența produsului

SODIF transformă intenția aprobată într-un document semnat într-o singură acțiune digitală
controlată, trasabilă și protejată împotriva modificării sau repetării.

## Nucleul diferențiator

Mecanismul **Signed Intent Execution** leagă verificabil:

1. revizia efectiv semnată;
2. câmpurile care produc efect;
3. consensul asupra valorilor critice;
4. politica aplicată;
5. metoda, ruta și corpul cererii API;
6. un permis criptografic cu durată scurtă și consum unic;
7. dovada execuției sau a blocării.
8. înregistrarea verificabilă a reviziei acceptate în arhiva documentară locală.

Verificarea este adaptivă. Câmpurile critice sunt reverificate independent, iar procesarea
extinsă este activată numai când riscul, incertitudinea sau impactul o justifică. AI poate
clasifica, extrage și explica, dar nu autorizează singur o acțiune.

## Flight demo TRL 4

POC-ul folosește un singur tip de document controlat — o comandă de achiziție PDF — și o
singură acțiune simulată: `POST /purchase-orders`.

Scenariile obligatorii sunt:

- **S1 — execuție validă:** permis emis, exact o comandă creată;
- **S2 — conflict semantic:** consens eșuat, zero execuții;
- **S3 — payload modificat:** digest diferit, cerere blocată;
- **S4 — replay:** a doua utilizare a permisului este respinsă.

## Principii de implementare

- nucleul nu depinde de Streamlit;
- toate contractele sunt tipizate și versionate;
- deciziile de autorizare sunt deterministe și fail-closed;
- adaptatoarele de document, AI și API sunt înlocuibile;
- logurile și dovezile nu includ implicit documentul integral;
- fiecare pas păstrează toate testele anterioare verzi;
- fiecare flight poate fi reprodus fără servicii comerciale externe.

## Limita demonstratorului

POC-ul nu implementează un API Gateway complet, Kubernetes, multi-cloud, arhivă juridică,
HSM de producție, integrare EUDI sau execuții financiare reale. Interfețele vor permite
adăugarea ulterioară a acestor capabilități fără schimbarea nucleului.
