"""Canonical catalog of the independently deployable SODIF capabilities."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProductModule:
    """Product-facing identity and boundary of one SODIF module."""

    key: str
    sequence: str
    name: str
    navigation_label: str
    promise: str
    responsibility: str
    input_contract: str
    output_contract: str
    icon: str
    page: str


MODULES = (
    ProductModule(
        key="security",
        sequence="01",
        name="SODIF Security",
        navigation_label="Controlul execuției",
        promise="Protejează trecerea de la revizia semnată la dreptul unic de execuție.",
        responsibility=(
            "Confirmă invariabilitatea valorilor operaționale prin extragere structurală și "
            "vizuală, construiește dovada pe câmp și emite permisul criptografic legat de "
            "acțiunea API."
        ),
        input_contract="Document semnat, schemă de câmpuri și acțiunea solicitată",
        output_contract="Dovadă semantică verificabilă și permis de execuție cu utilizare unică",
        icon=":material/shield_lock:",
        page="pages/security.py",
    ),
    ProductModule(
        key="archive",
        sequence="02",
        name="SODIF Archive",
        navigation_label="Arhivă verificabilă",
        promise="Păstrează reviziile validate într-un istoric verificabil și auditabil.",
        responsibility=(
            "Înregistrează reviziile validate, menține continuitatea criptografică și produce "
            "pachete portabile pentru verificare independentă."
        ),
        input_contract="Document validat, metadate semnate și legătura cu revizia anterioară",
        output_contract="Înregistrare indexată, istoric de revizii și pachet de audit",
        icon=":material/folder_managed:",
        page="pages/archive.py",
    ),
    ProductModule(
        key="gateway",
        sequence="03",
        name="SODIF Gateway",
        navigation_label="Control API",
        promise="Aplică permisul SODIF asupra cererii API observate la execuție.",
        responsibility=(
            "Recanonicalizează cererea, verifică dovada fiecărui parametru și legarea de "
            "acțiunea autorizată, apoi aplică politica de rutare și protecția anti-replay."
        ),
        input_contract="Cerere API, dovadă semantică, permis criptografic și destinație",
        output_contract="Rutare permisă sau blocare motivată, însoțită de jurnal de audit",
        icon=":material/hub:",
        page="pages/gateway.py",
    ),
)


def product_module(key: str) -> ProductModule:
    """Return the canonical metadata for a product module."""
    try:
        return next(module for module in MODULES if module.key == key)
    except StopIteration as error:
        raise ValueError(f"Unknown product module: {key}") from error
