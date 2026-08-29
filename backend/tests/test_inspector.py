from pathlib import Path

from app.agent.inspector import read_repository_files
from app.agent.inspector import (
    detect_file_extensions,
    find_important_files,
    find_test_files,
    list_repository_files,
)


def create_test_repository(tmp_path: Path) -> Path:
    """Create a small fake repository for testing."""

    repo = tmp_path / "repo"

    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir(parents=True)
    (repo / ".git" / "objects").mkdir(parents=True)
    (repo / "node_modules" / "package").mkdir(parents=True)

    (repo / "src" / "main.py").write_text("print('hello')")

    (repo / "src" / "utils.py").write_text("def add(a, b): return a + b")

    (repo / "tests" / "test_main.py").write_text("def test_main(): pass")

    (repo / "README.md").write_text("# Test Repository")

    (repo / "requirements.txt").write_text("pytest")

    (repo / ".git" / "objects" / "fake").write_text("should be ignored")

    (repo / "node_modules" / "package" / "fake.js").write_text("should be ignored")

    return repo


def test_list_repository_files(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    files = list_repository_files(str(repo))

    assert "src/main.py" in files
    assert "src/utils.py" in files
    assert "tests/test_main.py" in files
    assert "README.md" in files

    assert ".git/objects/fake" not in files
    assert "node_modules/package/fake.js" not in files


def test_find_test_files(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    test_files = find_test_files(str(repo))

    assert "tests/test_main.py" in test_files


def test_find_test_files_multilanguage(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    (repo / "calc.go").write_text("package calc")
    (repo / "calc_test.go").write_text("package calc")
    (repo / "lib.rs").write_text("fn main() {}")
    (repo / "lib_test.rs").write_text("fn main() {}")
    (repo / "sum.ts").write_text("export const sum = (a, b) => a + b")
    (repo / "sum.test.ts").write_text("import { sum } from './sum'")
    (repo / "sum.spec.tsx").write_text("import { sum } from './sum'")
    (repo / "helper.js").write_text("const helper = 1")
    (repo / "helper.test.js").write_text("test('ok', () => {})")

    test_files = find_test_files(str(repo))

    assert "calc_test.go" in test_files
    assert "lib_test.rs" in test_files
    assert "sum.test.ts" in test_files
    assert "sum.spec.tsx" in test_files
    assert "helper.test.js" in test_files

    assert "calc.go" not in test_files
    assert "sum.ts" not in test_files
    assert "helper.js" not in test_files


def test_find_important_files(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    important_files = find_important_files(str(repo))

    assert "README.md" in important_files
    assert "requirements.txt" in important_files


def test_find_important_files_go_and_rust(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    (repo / "go.mod").write_text("module example.com/demo")
    (repo / "Cargo.toml").write_text("[package]")
    (repo / "Makefile").write_text("all:")

    important_files = find_important_files(str(repo))

    assert "go.mod" in important_files
    assert "Cargo.toml" in important_files
    assert "Makefile" in important_files


def test_detect_file_extensions(tmp_path: Path) -> None:
    repo = create_test_repository(tmp_path)

    extensions = detect_file_extensions(str(repo))

    assert extensions[".py"] == 3


def test_read_repository_files(tmp_path: Path) -> None:
    calculator = tmp_path / "calculator.py"

    calculator.write_text("def add(a, b):\n" "    return a - b\n")

    result = read_repository_files(
        str(tmp_path),
        ["calculator.py"],
    )

    assert "calculator.py" in result
    assert "return a - b" in result["calculator.py"]
