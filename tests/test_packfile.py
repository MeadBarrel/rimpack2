from rimpack.core.packfile import load_pack_file


def test_load_pack_file():
    source = """
    [pack]
    name="my pack"
    rimworld_version="1.0"

    [layout]
    mod_files = [
    "mods/1.list",
    "mods/2.list",
    ]
    """
    _, model = load_pack_file(source)
    assert model.pack.name == "my pack"
    assert model.pack.rimworld_version == "1.0"
    assert model.layout.mod_files == [
        "mods/1.list",
        "mods/2.list",
    ]
