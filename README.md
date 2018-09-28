[![Build Status](https://travis-ci.com/camptocamp/geo_11_odoo.svg?token=3A3ZhwttEcmdqp7JzQb7&branch=master)](https://travis-ci.com/camptocamp/geo_11_odoo)

# geo_11 Odoo

**Our internal id for this project is: 0000.**

This project uses Docker.
Travis builds a new image for each change on the branches and for each new tag.

The images built on the master branch are built as `camptocamp/geo_11_odoo:latest`.
The images built on other branches are built as `camptocamp/geo_11_odoo:<branch-name>`.
The ones built from tags are built as `camptocamp/geo_11_odoo:<tag-name>`.

Images are pushed on the registry only when Travis has a green build.

When a container starts, the database is automatically created and the
migration scripts automatically run.

## Project maintenance

Please keep this project up-to-date by:

* ensure the `FROM` image in `odoo/Dockerfile` is the latest release
* run regularly `invoke project.sync` to retrieve the last template's changes

## Links

* [General documentation](./docs/README.md)
* [Local documentation](./docs/README.local.md)
* [Changelog](HISTORY.rst).
* [Minions](https://geo_11.odoo-test.camptocamp.ch)
* [Base image documentation](https://github.com/camptocamp/docker-odoo-project)
