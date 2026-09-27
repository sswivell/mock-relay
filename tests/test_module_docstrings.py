import glob
import os


def test_all_public_modules_have_docstrings():
    here = os.path.dirname(os.path.abspath(__file__))
    pkg = os.path.join(here, "..", "mockrelay")
    missing = []
    for path in glob.glob(os.path.join(pkg, "*.py")):
        base = os.path.basename(path)
        if base.startswith("__"):
            continue
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        first_stmt = next((l for l in lines if l.strip()), "")
        if not first_stmt.startswith('"""'):
            missing.append(base)
    assert not missing, f"modules without a docstring: {missing}"
