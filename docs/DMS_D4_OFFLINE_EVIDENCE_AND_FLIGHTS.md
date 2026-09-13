# DMS D4 — pachet documentar offline și flight-uri distincte

## Rezultat

SODIF separă explicit demonstrația nucleului de securitate de demonstrația transversală:

- **Security Flight** validează documentul semnat, confirmă adaptiv intenția, leagă
  criptografic autorizarea de acțiunea API și blochează modificarea sau reutilizarea. Nu
  scrie în arhiva documentară.
- **Transversal Flight** rulează aceleași controale, păstrează reviziile acceptate în SODIF
  Archive și aplică permisul prin SODIF Gateway, cu toate deciziile incluse în dovezi.

Separarea permite evaluarea directă a dezvoltării aflate în nucleul proiectului, fără ca
extensia DMS să îi dilueze rezultatul, și demonstrează totodată integrarea ulterioară într-un
flux documentar complet.

## Pachet documentar verificabil offline

Pentru orice revizie deschisă după reconfirmarea integrității, registrul generează determinist
un fișier ZIP care conține:

- documentul selectat;
- istoricul complet al reviziilor;
- manifestul cu dimensiunea și amprenta SHA-256 a fiecărui fișier;
- rădăcina de integritate și identificatorul determinist al pachetului;
- instrucțiuni de verificare offline.

Verificatorul local nu accesează depozitul original. El controlează structura pachetului,
fișierele declarate, amprentele, rădăcina de integritate, corespondența documentului cu
înregistrarea selectată și continuitatea lanțului de revizii.

## Criterii de acceptare

- Security Flight nu produce nicio înregistrare DMS.
- Transversal Flight păstrează o singură înregistrare deduplicată pentru revizia validă.
- Deciziile de securitate sunt identice în cele două flight-uri.
- Pachetul documentar este reproductibil pentru aceeași revizie.
- Orice modificare a documentului din pachet este detectată offline.
- Ambele flight-uri și exporturile lor sunt disponibile separat în interfața produsului.
