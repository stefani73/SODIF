"""SODIF Gateway module entry point."""

from sodif.settings import GatewaySettings, load_settings
from sodif.ui.pages.gateway import render_gateway_module
from sodif.ui.state import initialize_operational_profile

app_settings = load_settings()
profile = initialize_operational_profile(app_settings)
render_gateway_module(
    GatewaySettings(
        route_id=profile.route_id,
        audience=profile.audience,
        path_prefix=profile.path_prefix,
        maximum_parameters=profile.maximum_parameters,
    )
)
