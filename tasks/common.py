# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from __future__ import print_function

import errno
import os
import shutil
import tempfile
import yaml

from builtins import input

from contextlib import contextmanager
from invoke import exceptions

try:
    import git_aggregator.config
    import git_aggregator.main
    import git_aggregator.repo
except ImportError:
    print('Please install git-aggregator')


def root_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def build_path(path, from_root=True, from_file=None):
    if not from_file and from_root:
        base_path = root_path()
    else:
        if from_file is None:
            from_file = __file__
        base_path = os.path.dirname(os.path.realpath(from_file))

    return os.path.join(base_path, path)


VERSION_FILE = build_path('odoo/VERSION')
HISTORY_FILE = build_path('HISTORY.rst')
PENDING_MERGES = build_path('odoo/pending-merges.yaml')
MIGRATION_FILE = build_path('odoo/migration.yml')
COOKIECUTTER_CONTEXT = build_path('.cookiecutter.context.yml')

GIT_REMOTE_NAME = 'camptocamp'
TEMPLATE_GIT = 'git@github.com:camptocamp/odoo-template.git'


def cookiecutter_context():
    with open(COOKIECUTTER_CONTEXT, 'rU') as f:
        return yaml.load(f.read())


def exit_msg(message):
    print(message)
    raise exceptions.Exit(1)


@contextmanager
def cd(path):
    prev = os.getcwd()
    os.chdir(os.path.expanduser(path))
    try:
        yield
    finally:
        os.chdir(prev)


def current_version():
    with open(VERSION_FILE, 'rU') as fd:
        version = fd.read().strip()
    return version


def ask_or_abort(message):
    r = input(message + ' (y/N) ')
    if r not in ('y', 'Y', 'yes'):
        exit_msg('Aborted')


def check_git_diff(ctx, direct_abort=False):
    try:
        ctx.run('git diff --quiet --exit-code')
        ctx.run('git diff --cached --quiet --exit-code')
    except exceptions.Failure:
        if direct_abort:
            exit_msg('Your repository has local changes. Abort.')
        ask_or_abort('Your repository has local changes, '
                     'are you sure you want to continue?')


@contextmanager
def tempdir():
    name = tempfile.mkdtemp()
    try:
        yield name
    finally:
        try:
            shutil.rmtree(name)
        except OSError as e:
            # already deleted
            if e.errno != errno.ENOENT:
                raise


def search_replace(file_path, old, new):
    """ Replace a text in a file on each lines """
    shutil.move(file_path, file_path + '.bak')
    with open(file_path + '.bak', 'r') as f_r:
        with open(file_path, 'w') as f_w:
            for line in f_r:
                f_w.write(line.replace(old, new))


def fix_repo_path(path):
    # FIXME: diry fix to make sure submodule path is correct.
    # Premise: gitaggregator assumes paths are relative to pending merge file
    # (odoo/pending-merges.yml as of today)
    # but we run it from the root of the project, which leads to repo.cwd like:
    # /home/sorsi/dev/projects/fluxdock/external-src/connector-interfaces
    # which is not correct! Here we hack it to make it absolutely correct
    # and then we'll have to adatp it or trash or fix gitaggregator
    # when we move pending merges to separated files in proj root (#225).
    if '/odoo/' in path:
        return path
    proj_path = root_path()
    repo_path = path.replace(proj_path.rstrip('/'), '').strip('/')
    return proj_path + '/odoo/' + repo_path


def get_aggregator_repositories():
    repositories = git_aggregator.config.load_config(
        build_path(PENDING_MERGES)
    )
    for repo_dict in repositories:
        repo_dict['cwd'] = fix_repo_path(repo_dict['cwd'])
        yield git_aggregator.repo.Repo(**repo_dict)


def get_aggregator_repo(submodule_path):
    """Build the git_aggregator repo object.

    Parses the pending merges file and creates the repo object
    for the one that has the right submodule path.
    """
    repo = None
    found = False
    for repo in get_aggregator_repositories():
        if git_aggregator.main.match_dir(repo.cwd, submodule_path):
            found = True
            break
    if not found:
        exit_msg(
            'No submodule found in pending-merges matching path {}'.format(
                submodule_path)
        )
    return repo
