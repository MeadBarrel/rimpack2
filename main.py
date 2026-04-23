from typer.testing import CliRunner
from rimpack.cli.main import app
import rimpack.cli.main
from unittest.mock import MagicMock

rimpack.cli.main.console.status = MagicMock()

runner = CliRunner()


def main():
    _ = runner.invoke(app, input="y\ny\ny\ny\n")


if __name__ == "__main__":
    main()
