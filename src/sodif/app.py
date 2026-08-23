"""Streamlit entry point for the SODIF demonstrator."""

from sodif.settings import load_settings
from sodif.ui.shell import configure_page, render_foundation_shell


def main() -> None:
    """Render the application shell for the current delivery step."""
    settings = load_settings()
    configure_page(settings)
    render_foundation_shell(settings)


if __name__ == "__main__":
    main()

