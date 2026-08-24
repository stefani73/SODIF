# Pasul 4 — verificare adaptivă și consens semantic

## Obiectiv

Confirmarea sensului operațional al documentului prin reprezentări independente, fără a
executa permanent toate mecanismele disponibile și fără a permite unui singur extractor
să autorizeze acțiunea.

## Mecanism

1. O politică explicabilă evaluează semnătura, acțiunea solicitată și contextul politicii.
2. Nivelul V0 blochează, V1 pornește verificarea țintită, V2 folosește traseul extins, iar
   V3 produce obligatoriu revizuire umană.
3. Fluxul V1 compară două reprezentări independente: structurală și vizuală.
4. Valorile sunt normalizate determinist conform tipului semantic, fără rescriere liberă
   sau decizie generativă.
5. A treia reprezentare, orientată spre ținta API, este activată numai dacă nivelul inițial
   este V2/V3 ori primele dovezi sunt insuficiente sau contradictorii.
6. Consensul păstrează valoarea, încrederea, adaptorul și digestul provenienței pentru
   fiecare candidat.

## Reguli de siguranță

- sunt necesare minimum două reprezentări cu adaptoare și tipuri de vedere distincte;
- câmpurile critice nu sunt aprobate prin vot majoritar dacă există un dezacord calificat;
- câmpurile lipsă, tipurile incompatibile și valorile ne-normalizabile nu sunt inventate;
- o revizie, un document sau un adaptor inconsecvent este respins înainte de consens;
- un rezultat V3 rămâne escaladat chiar dacă reprezentările automate concordă.

## Optimizare demonstrată

Fiecare adaptor declară un cost relativ. Rezultatul înregistrează căile executate, costul
incremental și costul evitat. Pentru documentele cu risc redus și consens imediat, a treia
cale nu rulează; pentru ambiguități, costul suplimentar este limitat și justificat explicit.

## Extensibilitate AI

Un extractor AI/OCR poate implementa același contract ca un parser structural sau un
validator orientat spre API. Niciun model AI nu primește drept de autorizare unilaterală:
rezultatul său rămâne o reprezentare cu proveniență, comparată cu dovezi independente.

## Criterii de acceptare

- valori semantic echivalente ajung la aceeași reprezentare canonică;
- un acord valid V1 oprește traseul înaintea celui de-al treilea adaptor;
- lipsa dovezilor activează exact o extindere controlată;
- conflictul critic și nivelul V3 sunt escaladate;
- documentul blocat nu consumă resurse semantice;
- toate deciziile includ nivelul, motivele, proveniența și costul;
- Ruff, mypy strict și întreaga suită pytest sunt integral verzi;
- repository-ul este curat după commitul separat al Pasului 4.
