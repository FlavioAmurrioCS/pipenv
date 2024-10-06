from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from pipenv.routines.lock import do_lock
from pipenv.routines.outdated import do_outdated
from pipenv.routines.sync import do_sync
from pipenv.utils.dependencies import (
    expansive_install_req_from_line,
    get_pipfile_category_using_lockfile_section,
)
from pipenv.utils.project import ensure_project
from pipenv.utils.requirements import add_index_to_pipfile
from pipenv.utils.resolver import venv_resolve_deps
from pipenv.vendor import click

if TYPE_CHECKING:
    from pipenv.project import Project


def do_update(
    project: Project,
    python: str | None = None,
    pre: bool = False,
    system: bool = False,
    packages: list[Any] | None = None,
    editable_packages: list[Any] | None = None,
    site_packages: None = False,
    pypi_mirror: None = None,
    dev: bool = False,
    categories: list[Any] | None = None,
    index_url: None = None,
    extra_pip_args: list[Any] | None = None,
    quiet: bool = False,
    bare: bool = False,
    dry_run: None = None,
    outdated: bool = False,
    clear: bool = False,
    lock_only: bool = False,
):
    ensure_project(
        project,
        python=python,
        pypi_mirror=pypi_mirror,
        warn=(not quiet),
        site_packages=site_packages,
        clear=clear,
    )
    packages = [p for p in (packages or []) if p]
    editable = [p for p in (editable_packages or []) if p]
    if not outdated:
        outdated = bool(dry_run)
    if not packages:
        click.echo(
            "{} {} {} {}{}".format(
                click.style("Running", bold=True),
                click.style("$ pipenv lock", fg="yellow", bold=True),
                click.style("then", bold=True),
                click.style("$ pipenv sync", fg="yellow", bold=True),
                click.style(".", bold=True),
            )
        )
        do_lock(
            project,
            clear=clear,
            pre=pre,
            pypi_mirror=pypi_mirror,
            write=not outdated,
            extra_pip_args=extra_pip_args,
        )
    else:
        upgrade(
            project,
            pre=pre,
            system=system,
            packages=packages,
            editable_packages=editable,
            pypi_mirror=pypi_mirror,
            categories=categories,
            index_url=index_url,
            dev=dev,
            lock_only=lock_only,
            extra_pip_args=extra_pip_args,
        )

    if outdated:
        do_outdated(
            project,
            clear=clear,
            pre=pre,
            pypi_mirror=pypi_mirror,
        )
    else:
        do_sync(
            project,
            dev=dev,
            categories=categories,
            python=python,
            bare=bare,
            clear=clear,
            pypi_mirror=pypi_mirror,
            extra_pip_args=extra_pip_args,
        )


def upgrade(
    project: Project,
    pre: bool = False,
    system: bool = False,
    packages: list[Any] | None = None,
    editable_packages: list[Any] | None = None,
    pypi_mirror: None = None,
    index_url: None = None,
    categories: list[Any] | None = None,
    dev: bool = False,
    lock_only: bool = False,
    extra_pip_args: list[Any] | None = None,
):
    lockfile = project.lockfile()
    if not pre:
        pre = project.settings.get("allow_prereleases")
    if dev:
        categories = ["develop"]
    elif not categories:
        categories = ["default"]

    index_name = None
    if index_url:
        index_name = add_index_to_pipfile(project, index_url)

    if extra_pip_args:
        os.environ["PIPENV_EXTRA_PIP_ARGS"] = json.dumps(extra_pip_args)

    package_args = list(packages) + [f"-e {pkg}" for pkg in editable_packages]

    requested_install_reqs = defaultdict(dict)
    requested_packages = defaultdict(dict)
    for category in categories:
        pipfile_category = get_pipfile_category_using_lockfile_section(category)

        for package in package_args[:]:
            install_req, _ = expansive_install_req_from_line(package, expand_env=True)
            if index_name:
                install_req.index = index_name
            name, normalized_name, pipfile_entry = project.generate_package_pipfile_entry(
                install_req, package, category=pipfile_category
            )
            project.add_pipfile_entry_to_pipfile(
                name, normalized_name, pipfile_entry, category=pipfile_category
            )
            requested_packages[pipfile_category][normalized_name] = pipfile_entry
            requested_install_reqs[pipfile_category][normalized_name] = install_req

        if project.pipfile_exists:
            packages = project.parsed_pipfile.get(pipfile_category, {})
        else:
            packages = project.get_pipfile_section(pipfile_category)

        if not package_args:
            click.echo("Nothing to upgrade!")
            sys.exit(0)

        # Resolve package to generate constraints of new package data
        upgrade_lock_data = venv_resolve_deps(
            requested_packages[pipfile_category],
            which=project._which,
            project=project,
            lockfile={},
            category="default",
            pre=pre,
            allow_global=system,
            pypi_mirror=pypi_mirror,
        )
        if not upgrade_lock_data:
            click.echo("Nothing to upgrade!")
            sys.exit(0)

        for package_name, pipfile_entry in requested_packages[pipfile_category].items():
            if package_name not in packages:
                packages.append(package_name, pipfile_entry)
            else:
                packages[package_name] = pipfile_entry

        full_lock_resolution = venv_resolve_deps(
            packages,
            which=project._which,
            project=project,
            lockfile={},
            category=pipfile_category,
            pre=pre,
            allow_global=system,
            pypi_mirror=pypi_mirror,
        )
        # Mutate the existing lockfile with the upgrade data for the categories
        for package_name in upgrade_lock_data:
            correct_package_lock = full_lock_resolution.get(package_name)
            if correct_package_lock:
                lockfile[category][package_name] = correct_package_lock

    lockfile.update({"_meta": project.get_lockfile_meta()})
    project.write_lockfile(lockfile)
