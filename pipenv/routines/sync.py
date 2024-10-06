from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from pipenv import exceptions
from pipenv.routines.install import do_init, do_install_dependencies
from pipenv.utils import console, fileutils
from pipenv.utils.project import ensure_project

if TYPE_CHECKING:
    from pipenv.project import Project


def do_sync(
    project: Project,
    dev: bool = False,
    python: str | None = None,
    bare: bool = False,
    clear: bool = False,
    pypi_mirror: None = None,
    system: bool = False,
    deploy: bool = False,
    extra_pip_args: list[Any] | None = None,
    categories: list[Any] | None = None,
    site_packages: bool | None = False,
):
    # The lock file needs to exist because sync won't write to it.
    if not project.lockfile_exists:
        raise exceptions.LockfileNotFound("Pipfile.lock")

    # Ensure that virtualenv is available if not system.
    ensure_project(
        project,
        python=python,
        validate=False,
        system=system,
        deploy=deploy,
        pypi_mirror=pypi_mirror,
        clear=clear,
        site_packages=site_packages,
    )

    # Install everything.
    requirements_dir = fileutils.create_tracked_tempdir(
        suffix="-requirements", prefix="pipenv-"
    )
    if system:
        project.s.PIPENV_USE_SYSTEM = True
        os.environ["PIPENV_USE_SYSTEM"] = "1"
    do_init(
        project,
        allow_global=system,
        requirements_dir=requirements_dir,
        ignore_pipfile=True,  # Don't check if Pipfile and lock match.
        skip_lock=True,  # Don't re-lock
        pypi_mirror=pypi_mirror,
        deploy=deploy,
        system=system,
        extra_pip_args=extra_pip_args,
        categories=categories,
    )
    do_install_dependencies(
        project,
        dev=dev,
        allow_global=system,
        requirements_dir=requirements_dir,
        pypi_mirror=pypi_mirror,
        extra_pip_args=extra_pip_args,
        categories=categories,
    )
    if not bare:
        console.print("[green]All dependencies are now up-to-date![/green]")
