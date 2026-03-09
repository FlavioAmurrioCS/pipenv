"""Unit tests for the PIPENV_RESOLVER dispatcher pattern."""

from __future__ import annotations

from unittest.mock import patch

# ---------------------------------------------------------------------------
# resolve() dispatcher in pipenv.utils.resolver
# ---------------------------------------------------------------------------


class TestResolveDispatcher:
    """Tests for the resolve() dispatcher function."""

    def test_default_calls_pip_resolve(self, monkeypatch):
        """When PIPENV_RESOLVER is unset, resolve() calls _pip_resolve."""
        monkeypatch.delenv("PIPENV_RESOLVER", raising=False)

        with patch("pipenv.utils.resolver._pip_resolve") as mock_pip:
            mock_pip.return_value = "pip_result"
            from pipenv.utils.resolver import resolve

            result = resolve("cmd", "st", "project")
            mock_pip.assert_called_once_with("cmd", "st", "project")
            assert result == "pip_result"

    def test_pip_calls_pip_resolve(self, monkeypatch):
        """When PIPENV_RESOLVER=pip, resolve() calls _pip_resolve."""
        monkeypatch.setenv("PIPENV_RESOLVER", "pip")

        with patch("pipenv.utils.resolver._pip_resolve") as mock_pip:
            mock_pip.return_value = "pip_result"
            from pipenv.utils.resolver import resolve

            result = resolve("cmd", "st", "project")
            mock_pip.assert_called_once_with("cmd", "st", "project")
            assert result == "pip_result"

    def test_uv_pip_compile_calls_uv_resolve(self, monkeypatch):
        """When PIPENV_RESOLVER=uv-pip-compile, resolve() calls uv_resolve."""
        monkeypatch.setenv("PIPENV_RESOLVER", "uv-pip-compile")

        with patch("pipenv.uv.uv_resolve") as mock_uv:
            mock_uv.return_value = "uv_result"
            from pipenv.utils.resolver import resolve

            result = resolve("cmd", "st", "project")
            mock_uv.assert_called_once_with("cmd", "st", "project")
            assert result == "uv_result"

    def test_uv_lock_calls_uv_lock_resolve(self, monkeypatch):
        """When PIPENV_RESOLVER=uv-lock, resolve() calls uv_lock_resolve."""
        monkeypatch.setenv("PIPENV_RESOLVER", "uv-lock")

        with patch("pipenv.uv_lock.uv_lock_resolve") as mock_uv_lock:
            mock_uv_lock.return_value = "uv_lock_result"
            from pipenv.utils.resolver import resolve

            result = resolve("cmd", "st", "project")
            mock_uv_lock.assert_called_once_with("cmd", "st", "project")
            assert result == "uv_lock_result"

    def test_unknown_value_falls_back_to_pip(self, monkeypatch):
        """When PIPENV_RESOLVER has an unknown value, resolve() calls _pip_resolve."""
        monkeypatch.setenv("PIPENV_RESOLVER", "unknown-resolver")

        with patch("pipenv.utils.resolver._pip_resolve") as mock_pip:
            mock_pip.return_value = "pip_result"
            from pipenv.utils.resolver import resolve

            result = resolve("cmd", "st", "project")
            mock_pip.assert_called_once_with("cmd", "st", "project")
            assert result == "pip_result"


# ---------------------------------------------------------------------------
# pip_install_deps() dispatcher in pipenv.utils.pip
# ---------------------------------------------------------------------------


class TestPipInstallDepsDispatcher:
    """Tests for the pip_install_deps() dispatcher function."""

    def test_default_calls_pip_install_deps(self, monkeypatch):
        """When PIPENV_RESOLVER is unset, pip_install_deps() calls _pip_install_deps."""
        monkeypatch.delenv("PIPENV_RESOLVER", raising=False)

        with patch("pipenv.utils.pip._pip_install_deps") as mock_pip:
            mock_pip.return_value = "pip_result"
            from pipenv.utils.pip import pip_install_deps

            result = pip_install_deps("project", "deps", "sources")
            mock_pip.assert_called_once()
            assert result == "pip_result"

    def test_pip_calls_pip_install_deps(self, monkeypatch):
        """When PIPENV_RESOLVER=pip, pip_install_deps() calls _pip_install_deps."""
        monkeypatch.setenv("PIPENV_RESOLVER", "pip")

        with patch("pipenv.utils.pip._pip_install_deps") as mock_pip:
            mock_pip.return_value = "pip_result"
            from pipenv.utils.pip import pip_install_deps

            result = pip_install_deps("project", "deps", "sources")
            mock_pip.assert_called_once()
            assert result == "pip_result"

    def test_uv_pip_compile_calls_uv_pip_install_deps(self, monkeypatch):
        """When PIPENV_RESOLVER=uv-pip-compile, calls uv_pip_install_deps."""
        monkeypatch.setenv("PIPENV_RESOLVER", "uv-pip-compile")

        with patch("pipenv.uv.uv_pip_install_deps") as mock_uv:
            mock_uv.return_value = "uv_result"
            from pipenv.utils.pip import pip_install_deps

            result = pip_install_deps("project", "deps", "sources")
            mock_uv.assert_called_once()
            assert result == "uv_result"

    def test_uv_lock_calls_uv_pip_install_deps(self, monkeypatch):
        """When PIPENV_RESOLVER=uv-lock, calls uv_pip_install_deps."""
        monkeypatch.setenv("PIPENV_RESOLVER", "uv-lock")

        with patch("pipenv.uv.uv_pip_install_deps") as mock_uv:
            mock_uv.return_value = "uv_result"
            from pipenv.utils.pip import pip_install_deps

            result = pip_install_deps("project", "deps", "sources")
            mock_uv.assert_called_once()
            assert result == "uv_result"

    def test_unknown_value_falls_back_to_pip(self, monkeypatch):
        """When PIPENV_RESOLVER has an unknown value, falls back to _pip_install_deps."""
        monkeypatch.setenv("PIPENV_RESOLVER", "unknown-resolver")

        with patch("pipenv.utils.pip._pip_install_deps") as mock_pip:
            mock_pip.return_value = "pip_result"
            from pipenv.utils.pip import pip_install_deps

            result = pip_install_deps("project", "deps", "sources")
            mock_pip.assert_called_once()
            assert result == "pip_result"

    def test_passes_all_kwargs(self, monkeypatch):
        """Verify that all keyword arguments are forwarded to the backend."""
        monkeypatch.delenv("PIPENV_RESOLVER", raising=False)

        with patch("pipenv.utils.pip._pip_install_deps") as mock_pip:
            mock_pip.return_value = []
            from pipenv.utils.pip import pip_install_deps

            pip_install_deps(
                "proj",
                "deps",
                "srcs",
                allow_global=True,
                ignore_hashes=True,
                no_deps=True,
                requirements_dir="/tmp/r",
                use_pep517=False,
                extra_pip_args=["--no-binary", ":all:"],
            )
            mock_pip.assert_called_once_with(
                "proj",
                "deps",
                "srcs",
                allow_global=True,
                ignore_hashes=True,
                no_deps=True,
                requirements_dir="/tmp/r",
                use_pep517=False,
                extra_pip_args=["--no-binary", ":all:"],
            )
