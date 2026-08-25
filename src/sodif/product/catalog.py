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
        name="Signed Intent Security",
        navigation_label="Securitate tranzacțională",
        promise="Transformă aprobarea semnată într-un drept de execuție precis și unic.",
        responsibility=(
            "Verifică documentul, confirmă intenția critică și emite permisul criptografic "
            "legat de acțiunea API autorizată."
        ),
        input_contract="Document semnat, reprezentări independente și acțiunea solicitată",
        output_contract="Decizie explicabilă și permis de execuție cu utilizare unică",
        icon=":material/shield_lock:",
        page="pages/security.py",
    ),
    ProductModule(
        key="archive",
        sequence="02",
        name="Verifiable Document Archive",
        navigation_label="Arhivă verificabilă",
        promise="Păstrează documentul și reviziile într-un istoric verificabil și auditabil.",
        responsibility=(
            "Preia numai revizii validate, menține lanțul criptografic și produce pachete "
            "portabile pentru audit independent."
        ),
        input_contract="Document validat, metadate semnate și legătura cu revizia anterioară",
        output_contract="Înregistrare indexată, istoric de revizii și pachet de audit",
        icon=":material/folder_managed:",
        page="pages/archive.py",
    ),
    ProductModule(
        key="gateway",
        sequence="03",
        name="Semantic Execution Gateway",
        navigation_label="Gateway semantic",
        promise="Permite API-ului să execute numai tranzacția aprobată în document.",
        responsibility=(
            "Validează permisul față de cererea API, aplică protecția anti-replay și decide "
            "controlat dacă tranzacția poate fi rutată."
        ),
        input_contract="Cerere API, permis criptografic și contextul destinației",
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
