from pathlib import Path


def test_all_public_modules_have_docstrings():
    pkg = Path(__file__).resolve().parent.parent / "mockrelay"
    missing = []
    for path in sorted(pkg.glob("*.py")):
        if path.name.startswith("__"):
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        first_stmt = next((line for line in lines if line.strip()), "")
        if not first_stmt.startswith('"""'):
            missing.append(path.name)
    assert not missing, f"modules without a docstring: {missing}"
