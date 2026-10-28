import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core import simulation
from app.core.settings import Settings


def _load_cli_module():
    simulator_path = Path(__file__).resolve().parents[2] / "tools" / "security_simulator.py"
    spec = importlib.util.spec_from_file_location("security_simulator", simulator_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_requires_exact_authorized_https_hostname() -> None:
    simulator = _load_cli_module()

    assert simulator.validate_target(
        "https://demo.example.test",
        authorized_demo_host="demo.example.test",
    ) == "https://demo.example.test"
    with pytest.raises(ValueError):
        simulator.validate_target("https://other.example.test", authorized_demo_host="demo.example.test")
    with pytest.raises(ValueError):
        simulator.validate_target("http://demo.example.test", authorized_demo_host="demo.example.test")
    with pytest.raises(ValueError):
        simulator.validate_target("https://demo.example.test:8443", authorized_demo_host="demo.example.test")
    with pytest.raises(ValueError):
        simulator.validate_target(
            "https://demo.example.test/admin",
            authorized_demo_host="demo.example.test",
        )
    with pytest.raises(ValueError):
        simulator.validate_target(
            "https://user:password@demo.example.test",
            authorized_demo_host="demo.example.test",
        )


def test_remote_simulation_requires_demo_environment_and_explicit_enablement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        simulation,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="demo",
            simulation_demo_enabled=True,
            simulation_allowed_hosts="demo.example.test, api.demo.example.test",
        ),
    )

    assert simulation.simulation_enabled("demo.example.test")
    assert simulation.simulation_enabled("DEMO.EXAMPLE.TEST.")
    assert simulation.simulation_enabled("api.demo.example.test")
    assert not simulation.simulation_enabled("example.test")
    assert not simulation.simulation_enabled(None)

    monkeypatch.setattr(
        simulation,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="production",
            simulation_demo_enabled=True,
            simulation_allowed_hosts="demo.example.test",
        ),
    )
    assert not simulation.simulation_enabled("demo.example.test")

    monkeypatch.setattr(
        simulation,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="demo",
            simulation_demo_enabled=False,
            simulation_allowed_hosts="demo.example.test",
        ),
    )
    assert not simulation.simulation_enabled("demo.example.test")


def test_remote_simulation_gate_returns_not_found_for_unapproved_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        simulation,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="demo",
            simulation_demo_enabled=True,
            simulation_allowed_hosts="demo.example.test",
        ),
    )
    request = SimpleNamespace(
        url=SimpleNamespace(hostname="attacker.example.test", scheme="https", port=443)
    )

    with pytest.raises(simulation.HTTPException) as exc:
        simulation.require_simulation_enabled(request)

    assert exc.value.status_code == 404


def test_demo_environment_settings_are_read_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "demo")
    monkeypatch.setenv("SIMULATION_DEMO_ENABLED", "true")
    monkeypatch.setenv("SIMULATION_ALLOWED_HOSTS", "demo.example.test")

    settings = Settings(_env_file=None)

    assert settings.app_env == "demo"
    assert settings.simulation_demo_enabled is True
    assert settings.simulation_allowed_hosts == "demo.example.test"


@pytest.mark.parametrize(
    ("scheme", "port"),
    [("http", 80), ("https", 8443)],
)
def test_remote_simulation_requires_standard_https_origin(
    monkeypatch: pytest.MonkeyPatch, scheme: str, port: int
) -> None:
    monkeypatch.setattr(
        simulation,
        "get_settings",
        lambda: SimpleNamespace(
            app_env="demo",
            simulation_demo_enabled=True,
            simulation_allowed_hosts="demo.example.test",
        ),
    )
    request = SimpleNamespace(
        url=SimpleNamespace(hostname="demo.example.test", scheme=scheme, port=port)
    )

    with pytest.raises(simulation.HTTPException) as exc:
        simulation.require_simulation_enabled(request)

    assert exc.value.status_code == 404
