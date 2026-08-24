# Pasul 5 — permis criptografic unic de execuție

## Obiectiv

Transformarea unei decizii semantice acceptate într-o autorizație tehnică scurtă, verificată
direct față de acțiunea API care urmează să fie executată și inutilizabilă a doua oară.

## Lanțul de legare

Permisul include digesturi SHA-256 pentru:

1. rezultatul complet al verificării adaptive;
2. consensul semantic final;
3. manifestul de intenție rezultat din document;
4. planul de execuție, incluzând metoda, ruta, audiența și parametrii;
5. politica sub care a fost autorizată interpretarea.

Digesturile, documentul, revizia, emitentul, audiența și intervalul de valabilitate formează
un obiect canonic RFC 8785 semnat Ed25519. Orice schimbare a acțiunii sau a contextului
invalidează legătura ori semnătura.

## Condiții de emitere

- verificarea adaptivă trebuie să fie `accepted`, nu `blocked` sau `escalated`;
- consensul final trebuie să fie acceptat automat;
- documentul și revizia trebuie să coincidă în verificare și manifest;
- digestul manifestului trebuie să coincidă cu cel folosit de planul de execuție;
- politica manifestului trebuie să coincidă cu politica verificării;
- durata cerută trebuie să se încadreze în limita emitentului.

## Condiții de autorizare

- cheia emitentului este de încredere, activă și nerevocată la emitere;
- semnătura acoperă integral revendicările permisului;
- permisul este în fereastra temporală acceptată de verificator;
- audiența și digestul planului coincid cu acțiunea prezentată;
- identificatorul permisului nu a fost consumat anterior.

## Consum unic

Bariera anti-replay înregistrează atomic consumul permisului. Chiar dacă mai multe cereri
concurente prezintă simultan același permis valid, numai una primește autorizarea; celelalte
sunt respinse cu motivul `permit_replayed`. O reîncercare necesită un permis nou.

## Delimitare

Pasul autorizează acțiunea, dar nu efectuează încă apelul HTTP. Motorul de scenarii va lega
autorizarea de un adaptor API controlat și va produce dovezile complete ale execuției.

## Criterii de acceptare

- numai consensul automat acceptat poate produce permis;
- orice modificare a planului sau audienței este respinsă înainte de consum;
- permisul expirat, viitor, supradimensionat temporal sau semnat cu o cheie invalidă este
  respins fail-closed;
- reutilizarea secvențială și concurentă permite exact o singură autorizare;
- Ruff, mypy strict și întreaga suită pytest sunt integral verzi;
- repository-ul este curat după commitul separat al Pasului 5.
