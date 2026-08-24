import tomllib
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


class ProjectSetupTest(unittest.TestCase):
    def test_dependencies_are_declared_in_pyproject(self) -> None:
        # Arrange
        pyproject_path = PROJECT_ROOT / "pyproject.toml"

        # Act
        pyproject = tomllib.loads(pyproject_path.read_text())

        # Assert
        self.assertEqual(
            pyproject["project"]["dependencies"],
            ["aiohttp", "bring-api", "python-dotenv"],
        )

    def test_mise_tasks_use_one_project_virtualenv(self) -> None:
        # Arrange
        mise_path = PROJECT_ROOT / "mise.toml"

        # Act
        config = tomllib.loads(mise_path.read_text())

        # Assert
        self.assertEqual(config["tools"]["python"], "3.14.7")
        self.assertIn("python -m venv .venv", config["tasks"]["install"]["run"])
        self.assertIn(
            ".venv/bin/python -m pip install --editable .",
            config["tasks"]["install"]["run"],
        )
        self.assertEqual(config["tasks"]["start"]["depends"], ["install"])
        self.assertEqual(
            config["tasks"]["start"]["run"],
            ".venv/bin/python bring2knuspr.py",
        )


if __name__ == "__main__":
    unittest.main()
