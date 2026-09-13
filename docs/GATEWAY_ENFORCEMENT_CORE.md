# SODIF Gateway — controlul tranzacțional la limita API

## Rol

SODIF Gateway aplică la limita API dreptul tranzacțional emis de `SODIF Security`. Modulul nu
reinterpretează documentul și nu repetă analiza semantică. El verifică
dacă cererea concretă păstrează exact acțiunea autorizată și decide fail-closed între rutare și
blocare.

Diferența față de un API Gateway clasic este obiectul autorizării:

- gateway-ul clasic verifică identitatea, ruta și politici tehnice;
- SODIF verifică suplimentar că metoda, resursa, parametrii și destinația sunt cele legate
  criptografic de aprobarea din documentul semnat.

## Contract de intrare

`GatewayRequest` folosește protocolul versionat `sodif.gateway-request/v1` și conține:

- identificatorul requestului;
- ruta de gateway selectată;
- planul exact al acțiunii API;
- permisul criptografic emis de modulul de securitate.

Planul include metoda HTTP, calea, audiența, parametrii canonici și amprenta intenției. Permisul
conține amprenta planului autorizat, audiența, perioada de valabilitate și semnătura emitentului.

## Politica rutei

`GatewayRoutePolicy` definește explicit:

- identificatorul rutei;
- serviciul destinație (`audience`);
- metodele HTTP permise;
- prefixele de cale protejate;
- limita de parametri acceptată.

Prefixele respectă segmente complete: politica `/purchase-orders` acceptă resursa exactă și
subresursele sale, dar nu acceptă `/purchase-orders-external`.

## Ordinea controalelor

Motorul aplică verificările într-o ordine care evită consumarea inutilă a permisului:

1. existența rutei;
2. potrivirea destinației;
3. metoda HTTP permisă;
4. resursa inclusă în limita protejată;
5. complexitatea requestului;
6. emitentul și cheia de încredere a permisului;
7. semnătura și fereastra de valabilitate;
8. potrivirea exactă dintre amprenta acțiunii autorizate și request;
9. consumarea atomică, o singură dată, a permisului;
10. transmiterea către adaptorul serviciului protejat.

Orice control eșuat oprește procesarea și nu produce efect asupra API-ului. Consumul unic este
atomic, astfel încât prezentările concurente ale aceluiași permis pot produce cel mult o rutare.

## Contract de ieșire

`GatewayDecision` folosește protocolul `sodif.gateway-decision/v1` și conține:

- rezultatul `routed` sau `blocked`;
- codul și explicația deciziei;
- ruta, destinația și permisul evaluate;
- amprenta requestului;
- amprenta acțiunii observate și amprenta acțiunii autorizate;
- registrul ordonat al controalelor aplicate;
- autorizația și chitanța de execuție, exclusiv pentru rezultatul `routed`.

Decizia este serializată direct ca JSON în pachetul Transversal Flight. Jurnalul NDJSON
păstrează separat fiecare evaluare Gateway, inclusiv verificările aplicate, amprentele
acțiunii observate și autorizate și dovada efectului asupra API-ului.

## Acoperirea amenințărilor

| Situație | Control | Rezultat |
|---|---|---|
| Rută necunoscută | catalog explicit de rute | `route.not_found` |
| Destinație schimbată | audiență legată de permis și rută | `route.audience_mismatch` |
| Metodă ori cale nepermisă | politica rutei | blocare înaintea permisului |
| Parametri modificați | amprenta canonică a planului | `permit.action_mismatch` |
| Permis expirat sau emis în viitor | fereastra criptografică | blocare fail-closed |
| Emitent ori semnătură nevalidă | trust store și Ed25519 | blocare fail-closed |
| Reutilizare sau concurență | consum atomic | `permit.permit_replayed` |
| Refuz al adaptorului protejat | control al efectului extern | `upstream.execution_rejected` |

## Configurare

Workspace-ul produsului preia politica implicită din:

- `SODIF_GATEWAY_ROUTE_ID`;
- `SODIF_GATEWAY_AUDIENCE`;
- `SODIF_GATEWAY_PATH_PREFIX`;
- `SODIF_GATEWAY_MAXIMUM_PARAMETERS`.

Valorile sunt validate la pornire. Ruta și audiența nu pot fi vide, prefixul trebuie să fie
absolut și fără separator final, iar limita parametrilor trebuie să fie între 1 și 256.

## Separarea adaptoarelor

Motorul depinde numai de contractele `PermitAuthorizer`, `ApiExecutor` și `Clock`. Adaptorul de
referință produce o chitanță deterministă fără efecte de rețea. Același nucleu poate controla
ulterior un reverse proxy sau un gateway existent prin înlocuirea adaptorului, fără modificarea
politicilor criptografice ori a deciziei de domeniu.

## Criterii de acceptare

- o tranzacție conformă produce autorizație, chitanță și decizie `routed`;
- modificarea planului este blocată fără consumarea permisului;
- a doua utilizare și prezentările concurente sunt blocate;
- controalele de rută preced verificarea și consumul permisului;
- semnătura nevalidă și refuzul adaptorului sunt fail-closed;
- deciziile incompatibile cu rezultatul sunt respinse de modelele de domeniu;
- interfața permite evaluarea cazurilor reprezentative și exportul deciziei JSON.
- Transversal Flight folosește motorul Gateway real și corelează deciziile sale cu arhiva,
  permisul și rezultatul scenariului.
