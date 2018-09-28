# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from __future__ import print_function
import psycopg2
import getpass
import requests
import gnupg
import time
from os.path import expanduser
from contextlib import contextmanager
from invoke import task
from datetime import datetime

from .common import cookiecutter_context


@contextmanager
def ensure_db_container_up(ctx):
    """ Ensure the DB container is up and running.

    :param ctx:
    :return: True if already up, False if it wasn't
    """
    try:
        ctx.run('docker-compose port db 5432', hide=True)
        started = True
    except Exception:
        ctx.run('docker-compose up -d db', hide=True)
        running = False
        # Wait for the container to start
        count = 0
        while not running:
            try:
                ctx.run('docker-compose port db 5432', hide=True)
                running = True
            except Exception as e:
                count += 1
                # Raise the error after 3 failed attempts
                if count >= 3:
                    raise e
                print('Waiting for DB container to start')
                time.sleep(0.3)
        started = False
    yield
    # Stop the container if it wasn't already up and running
    if not started:
        ctx.run('docker-compose stop db', hide=True)


def get_db_container_port(ctx):
    """Get and return DB container port"""
    run_res = ctx.run('docker-compose port db 5432', hide=True)
    return str(int(run_res.stdout.split(':')[-1]))


def expand_path(path):
    if path.startswith('~'):
        path = expanduser(path)
    return path


@task(name='list-versions')
def list_versions(ctx):
    """Print a table of DBs with Marabunta version and install date."""
    with ensure_db_container_up(ctx):
        db_port = get_db_container_port(ctx)
        dsn = "host=localhost dbname=postgres " \
              "user=odoo password=odoo port=%s" % db_port
        # Connect and list DBs
        with psycopg2.connect(dsn) as db_connection:
            with db_connection.cursor() as db_cursor:
                db_cursor.execute(
                    "SELECT datname "
                    "FROM pg_database "
                    "WHERE datistemplate = false "
                    "AND datname not in ('postgres', 'odoo');")
                databases_fetch = db_cursor.fetchall()
                db_list = [
                    db_name_tuple[0] for db_name_tuple in databases_fetch
                ]
        res = {}
        # Get version for each DB
        for db_name in db_list:
            dsn = "host=localhost dbname=%s user=odoo " \
                  "password=odoo port=%s" % (db_name, db_port)
            with psycopg2.connect(dsn) as db_connection:
                with db_connection.cursor() as db_cursor:
                    try:
                        db_cursor.execute(
                            "SELECT date_done, number "
                            "FROM marabunta_version "
                            "ORDER BY date_done DESC "
                            "LIMIT 1;")
                        version_tuple = db_cursor.fetchone()
                    except psycopg2.ProgrammingError:
                        # Error expected when marabunta_version table does not
                        # exist
                        res[db_name] = (None, 'unknown')
                        continue
                    res[db_name] = version_tuple
    print("{:<20} {:<10} {:<12}".format('DB Name', 'Version',
                                        'Install date'))
    print('=======              =======    ============')
    for db_name, version in sorted(res.iteritems(),
                                   key=lambda x: x[1][0] or datetime.min,
                                   reverse=True):
        if version[0]:
            time = version[0].strftime('%Y-%m-%d')
        else:
            time = 'unknown'
        print(
            "{:<20} {:<10} {:<12}".format(db_name, version[1], time))


@task(name='local-dump')
def local_dump(ctx, db_name='odoodb', path='.'):
    """Create a PG Dump for given database name.

    :param db_name: Name of the Database to dump
    :param path: Local path to store the dump
    :return: Dump file path
    """
    path = expand_path(path)
    with ensure_db_container_up(ctx):
        db_port = get_db_container_port(ctx)
        username = getpass.getuser()
        project_name = cookiecutter_context()['project_name']
        dump_name = '%s_%s-%s.pg' % (
            username, project_name, datetime.now().strftime('%Y%m%d-%H%M%S'))
        dump_file_path = '%s/%s' % (path, dump_name)
        ctx.run('pg_dump -h localhost -p %s --format=c -U odoo --file %s %s' % (
            db_port, dump_file_path, db_name
        ), hide=True)
        print('Dump succesfully generated at %s' % dump_file_path)
    return dump_file_path


def encrypt_for_dump_bags(ctx, dump_file_path):
    """Encrypt dump to GPG using keys from dump-bag.odoo.camptocamp.ch

    :param dump_file_path: Path of *.pg dump file
    :return: Path of the encrypted GPG dump
    """
    gpg_file_path = '%s.gpg' % dump_file_path
    r = requests.get('https://dump-bag.odoo.camptocamp.ch/keys')
    gpg = gnupg.GPG()
    gpg.import_keys(r.text)
    fingerprints = [str(rec['fingerprint']) for rec in gpg.list_keys()]
    with open(dump_file_path, 'rb') as dump_file:
        data = gpg.encrypt(dump_file, *fingerprints)
    with open(gpg_file_path, 'wb') as encrypted_dump:
        encrypted_dump.write(data.data)
    print('Dump successfully encrypted at %s' % gpg_file_path)
    return gpg_file_path


@task(name='share-on-dumps-bag')
def share_on_dumps_bag(ctx, dump_file_path):
    """Encrypt and push a dump to Odoo Dump bags manually.

    GPG dump will be pushed to url s3://odoo-dumps/your_username

    :param dump_file_path: Path of *.pg dump file
    """
    dump_file_path = expand_path(dump_file_path)
    gpg_file_path = encrypt_for_dump_bags(ctx, dump_file_path)
    username = getpass.getuser()
    ctx.run(
        'aws --profile=odoo-dumps s3 cp %s s3://odoo-dumps/%s' % (
            gpg_file_path, '/'.join([username, gpg_file_path.split('/')[-1]])
        ), hide=True)
    # Set ShortExpire tag for the dump to be auto deleted after 1 week
    ctx.run(
        'aws --profile=odoo-dumps s3api put-object-tagging '
        '--bucket odoo-dumps --key %s/%s '
        '--tagging="TagSet=[{Key=ShortExpire,Value=True}]"' % (
            username, gpg_file_path.split('/')[-1]), hide=True
    )
    print('Encrypted dump successfully shared on dumps bag.')
    print('Note this dump will be auto-deleted after 7 days.')


@task(name='dump-and-share')
def dump_and_share(ctx, db_name='odoodb', tmp_path='/tmp',
                   keep_local_dump=False):
    """Create a dump and share it on Odoo Dumps Bag.

    Usage : invoke database.dump-and-share --db-name=mydb

    :param db_name: Name of the Database to dump
    :param tmp_path: Temporary local path to store the dump
    :param keep_local_dump: Boolean to keep the generated and encrypted dumps
    locally
    """
    tmp_path = expand_path(tmp_path)
    dump_file_path = local_dump(ctx, db_name=db_name, path=tmp_path)
    share_on_dumps_bag(ctx, dump_file_path)
    if not keep_local_dump:
        ctx.run('rm %s' % dump_file_path)
        ctx.run('rm %s.gpg' % dump_file_path)


@task(name='empty-my-dump-bag')
def empty_my_dump_bag(ctx):
    """Empty the content of s3://odoo-dumps/your_username.

    Please call this function as soon as your recipient did download your dump.
    """
    username = getpass.getuser()
    ctx.run(
        'aws --profile=odoo-dumps s3 rm s3://odoo-dumps/%s/ --recursive' %
        username, hide=True
    )
    print('Your dumps bag has been emptied successfully.')
