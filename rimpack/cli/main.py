import typer
from rich.console import Console
from rich.prompt import Confirm
from tomlkit import TOMLDocument

from rimpack.core.config import Config, find_rimworld_root, find_rimworld_workshop_path

app = typer.Typer()

console = Console()


@app.callback(invoke_without_command=True)
def main_cli():
    _attempt_create_config()


def _attempt_create_config():
    config_path = Config.get_default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        config = Config(TOMLDocument())
    else:
        config = Config.from_toml(config_path)
    assert config.file_config is not None
    if config.rimworld_path is None and Confirm.ask(
        "[y]rimworld_path[/] is not set in config. Try to find automatically?",
        console=console,
    ):
        with console.status("Locating rimworld root"):
            rimworld_root = find_rimworld_root()
        if rimworld_root is None:
            console.print("Rimworld root could not be auto-detected.")
        elif Confirm.ask(
            f"Set [y]rimworld_root[/] to [y]{rimworld_root}[/]?", console=console
        ):
            config = config.with_rimworld_path(rimworld_root)
            config.save(config_path)
    if config.rimworld_workshop_path is None and Confirm.ask(
        "[y]rimworld_workshop_path[/] is not set in config. Try to find automatically?",
    ):
        with console.status("Locating rimworld workshop root"):
            rimworld_workshop_root = find_rimworld_workshop_path()
        if rimworld_workshop_root is None:
            console.print("Rimworld workshop root could not be auto-detected.")
        elif Confirm.ask(
            f"Set [y]rimworld_root[/] to [y]{rimworld_workshop_root}[/]?",
            console=console,
        ):
            config = config.with_rimworld_workshop_path(rimworld_workshop_root)
            config.save(config_path)


def main():
    app()
