"""Streamlit entry point for SODIF."""

from sodif.settings import load_settings
from sodif.ui.shell import configure_page, render_product_shell


def main() -> None:
    """Render the SODIF product experience."""
    settings = load_settings()
    configure_page(settings)
    render_product_shell(settings)


if __name__ == "__main__":
    main()
