from mockrelay._15 import _40


def test_init_writes_config(tmp_path):
    target = tmp_path / "mockrelay.yaml"
    _40(["init", str(target)])
    assert target.exists()
    text = target.read_text(encoding="utf-8")
    assert "listen:" in text
    assert "upstreams:" in text


def test_init_refuses_existing_file(tmp_path):
    target = tmp_path / "mockrelay.yaml"
    target.write_text("listen: '127.0.0.1:9999'\n", encoding="utf-8")
    _40(["init", str(target)])
    assert target.read_text(encoding="utf-8") == "listen: '127.0.0.1:9999'\n"


def test_init_force_overwrites_existing_file(tmp_path):
    target = tmp_path / "mockrelay.yaml"
    target.write_text("listen: '127.0.0.1:9999'\n", encoding="utf-8")
    _40(["init", str(target), "--force"])
    text = target.read_text(encoding="utf-8")
    assert "listen:" in text
    assert "9999" not in text
