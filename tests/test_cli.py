"""The CLI answers questions a user asks before starting a server.

A recorded fixture set is only useful if the tool can tell you what is in
it, whether it is still valid, and what it would match, without binding a
port or reaching the network. These tests drive the real entry point and
assert on what lands on stdout and in the exit code, because that is the
whole contract: the exit code is what a CI step reads and stdout is what a
human reads.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from mockrelay._15 import _40
from mockrelay._version import __version__


def _run(argv, capsys):
    """Run the CLI, returning (exit_code, stdout, stderr)."""
    code = 0
    try:
        _40(argv)
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
    out = capsys.readouterr()
    return code, out.out, out.err


# --version


def test_01_version_prints_the_package_version(capsys):
    code, out, _ = _run(["--version"], capsys)
    assert code == 0
    assert __version__ in out


def test_02_version_matches_the_installed_package(capsys):
    """The flag and the metadata cannot drift, because both read one file."""
    import importlib.metadata

    code, _out, _ = _run(["--version"], capsys)
    assert code == 0
    try:
        assert importlib.metadata.version("mockrelay") == __version__
    except importlib.metadata.PackageNotFoundError:
        pytest.skip("mockrelay is not installed in this environment")


def test_03_version_does_not_need_a_config_or_a_store(tmp_path, monkeypatch):
    """--version must not create a fixtures directory as a side effect."""
    monkeypatch.chdir(tmp_path)
    proc = subprocess.run(
        [sys.executable, "-m", "mockrelay", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert __version__ in proc.stdout
    assert not (tmp_path / "fixtures").exists()
