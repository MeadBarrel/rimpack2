from pathlib import Path
from typer.testing import CliRunner
from rimpack.cli.main import app
from rimpack.core.config import Config

runner = CliRunner()


def test_main_cli(fake_config_path: Path, rimworld_root: Path, workshop_root: Path):
    result = runner.invoke(app, input="y\ny\ny\ny\n")
    assert result.exit_code == 0
    assert fake_config_path.exists()
    config = Config.from_toml(fake_config_path)
    assert config.rimworld_path == rimworld_root
    assert config.rimworld_workshop_path == workshop_root
