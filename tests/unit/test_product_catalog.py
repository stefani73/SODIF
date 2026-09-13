"""Unit tests for the stable product module catalog."""

import pytest

from sodif.product import MODULES, product_module


def test_catalog_defines_three_distinct_product_boundaries() -> None:
    assert [module.key for module in MODULES] == ["security", "archive", "gateway"]
    assert len({module.name for module in MODULES}) == 3
    assert all(module.input_contract for module in MODULES)
    assert all(module.output_contract for module in MODULES)


def test_product_module_lookup_is_explicit() -> None:
    assert product_module("gateway").name == "SODIF Gateway"

    with pytest.raises(ValueError, match="Unknown product module"):
        product_module("missing")
