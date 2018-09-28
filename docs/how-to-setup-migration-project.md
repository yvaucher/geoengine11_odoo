# How to setup a migration project

Summary:

* [Build steps](#build-steps)
* [Tools/Scripts to help the developer](#toolsscripts-to-help-the-developer)
* [Requirements/dependencies](#requirementsdependencies)

---

## Build steps

1. [Reset state for all modules](#reset-state-for-all-modules)
2. [Fix attachments path](#fix-attachments-path)
3. [Rename modules](#rename-modules)
4. [Update moved models](#update-moved-models)
5. [Update moved fields](#update-moved-fields)
6. [Install/Update all modules](#installupdate-all-modules)
7. [Uninstall modules](#uninstall-modules)
8. [Clean the database](#clean-the-database)
9. [Clean unavailable modules](#clean-unavailable-modules)

All these steps are launched from [migration.yml](../odoo/migration.yml)
in marabunta mode `migration`.

### Reset state for all modules

In migrated database:

* all modules installed in source version have the state `to upgrade`
* all new core modules to install have the state `to install`

We can't install/update a module unavailable in target code source.

So, we need to change the state of all modules to `uninstalled`.
And then, list in [migration.yml](../odoo/migration.yml) only modules we want to keep.

_Implementation_: [songs/migration/pre.sql](../odoo/songs/migration/pre.sql)

### Fix attachments path

In migrated database, we have 2 types of attachments:

* attachments stored directly in database in binary mode
* attachments stored in filestore

For filestore attachments,
it's necessary to customize the file path depending of the hosting.

With S3/SWIFT hosting,
the bucket/container name must be added at the beginning of the path.

_Implementation_: [songs/migration/pre.py](../odoo/songs/migration/pre.py)
in function `fix_path_on_attachments`.

### Rename modules

Some specific/OCA modules can be renamed between source and target version.
In this case, the module metadata must be updated before launching
the update of all modules to avoid build failures or loss of data.

You don’t need to update the models contained in the renamed modules,
when the module is renamed, all the models, fields, etc. will be renamed too.

_Implementation_: [songs/migration/pre.py](../odoo/songs/migration/pre.py)
in function `rename_modules`.

### Update moved models

Some models can be moved in other modules between source and target version.
So we need to update the models metadata before launching
the update of all modules to avoid build failures or loss of data.

_Implementation_: [songs/migration/pre.py](../odoo/songs/migration/pre.py)
in function `update_moved_models`.

### Update moved fields

For the fields moved in another module between source and target version,
you must update the fields metadata before launching
the update of all modules to avoid build failures or loss of data.

_Implementation_: [songs/migration/pre.py](../odoo/songs/migration/pre.py)
in function `update_moved_fields`.

### Install/Update all modules

In the migration build, all modules we want to :

* install,
* keep installed,
* update

must be listed in [migration.yml](../odoo/migration.yml)
in section `addons/upgrade`.

At the end of the build,
be sure that the list of installed modules is the same
for a migrated database (with marabunta mode `migration`)
than for a « from scratch » database (with marabunta mode `sample`).

### Uninstall modules

In target version,
if we don't want to keep some modules previously installed in source version,
we must uninstalled them to allow Odoo to remove all their metadata/data.

The source code for these modules is not required to uninstall them.

_Implementation_: [songs/migration/post.py](../odoo/songs/migration/post.py)
in function `uninstall_modules`.

### Clean the database

In migration process, a lot of metadata/data persist in database
even if the origin module have been uninstalled.

The following data can be cleaned:

* models
* columns/fields
* tables
* models data
* menus

See module `database_cleanup` to see what is exactly cleaned for each item.

_Implementation_: [songs/migration/post.py](../odoo/songs/migration/post.py)
in function `database_cleanup`.

### Clean unavailable modules

A lot of available modules not installed in source version
are still in the modules list of the target version,
but are now unavailable (because not updated for the new version).

These modules must be deleted from the list of modules.

_Implementation_: [songs/migration/post.py](../odoo/songs/migration/post.py)
in function `clean_unavailable_modules`.

## Tools/Scripts to help the developer

### Check fields

In migration build,
if a field is moved from a module to another,
the column/data can be lost during the process.

A script is available to check if the migrated database contains fields
which must be moved into another module.

This script will help you to know which fields you must move
to be sure to not lose datas during the process
(you will add this fields in the step [Update moved fields](#update-moved-fields)).

To launch the script, it's necessary to:

* be in `dev` environment
* launch the build with environment variable: `MIGRATION_CHECK_FIELDS`

:warning: **Be careful**, this script is here to help the developper,
but to be sure that no data have been lost, the best way is to test the migration.

_Implementation_:

* [songs/migration/pre_check_fields.py](../odoo/songs/migration/pre_check_fields.py)
* [songs/migration/post_check_fields.py](../odoo/songs/migration/post_check_fields.py)

## Requirements/dependencies

* Uncomment the `openupgradelib` import in [requirement.txt](../odoo/requirement.txt)
* Install the module `database_cleanup` in [migration.yml](../odoo/migration.yml)
  * Repository OCA for this module is `server-tools`
