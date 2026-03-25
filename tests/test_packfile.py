from rimpack.core.packfile import PackConfig, load_pack_file


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
    assert model.layout.mod_files == (
        "mods/1.list",
        "mods/2.list",
    )


def test_initialize():
    pack = PackConfig.initialize("modpack", "1.6", ["abc", "abc2"])
    assert pack.name == "modpack"
    assert pack.rimworld_version == "1.6"
    assert pack.mod_files == ("abc", "abc2")


def test_with_added_mod_file():
    pack = PackConfig.initialize("modpack", "1.6", ["abc", "abc2"])
    new_pack = pack.with_added_mod_file("abc3")
    assert new_pack.mod_files == ("abc", "abc2", "abc3")
