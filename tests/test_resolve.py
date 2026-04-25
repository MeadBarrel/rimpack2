import pytest

from rimpack.core.config import Config
from rimpack.core.resolve import resolve_mod


@pytest.mark.usefixtures("rimworld_root_mods")
@pytest.mark.usefixtures("rimworld_workshop_mods")
@pytest.mark.parametrize(
    ["package_id", "name"],
    [
        ("fluffy.blueprints", "Blueprints"),
        ("fluffy.colonymanager", "Colony Manager"),
        ("haplo.miscellaneous.robots", "Misc. Robots"),
    ],
)
def test_resolve_mod_by_package_id(rimpack_config: Config, package_id: int, name: str):
    result = resolve_mod(rimpack_config, package_id)
    assert result.about.name == name


@pytest.mark.usefixtures("rimworld_root_mods")
@pytest.mark.usefixtures("rimworld_workshop_mods")
@pytest.mark.parametrize(
    ["package_id", "name"],
    [
        ("fluffy.blueprints", "Blueprints"),
        ("fluffy.colonymanager", "Colony Manager"),
        ("haplo.miscellaneous.robots", "Misc. Robots"),
    ],
)
def test_resolve_mod_by_package_id_with_prefix(
    rimpack_config: Config, package_id: str, name: str
):
    result = resolve_mod(rimpack_config, f"packageid:{package_id}")
    assert result.about.name == name
