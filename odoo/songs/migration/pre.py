# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import anthem
import os
from .helper import update_module_moved_models
from openupgradelib.openupgrade import update_module_names,\
    update_module_moved_fields


@anthem.log
def fix_path_on_attachments(ctx):
    """ Fix path on attachments """
    env = os.environ.get('RUNNING_ENV')
    if env in ('prod', 'integration'):
        # Update attachment given by odoo for the database migration
        ctx.env.cr.execute("""
    UPDATE
        ir_attachment
    SET
        store_fname = 's3://geo_11-odoo-%s/' || store_fname
    WHERE
        store_fname IS NOT NULL
    AND store_fname NOT LIKE 's3://%%';
            """ % (env,))
    else:
        # Remove the s3 attachment
        ctx.env.cr.execute("""
DELETE FROM
    ir_attachment
WHERE
    store_fname IS NOT NULL
AND store_fname LIKE 's3://%';
        """)


@anthem.log
def rename_modules(ctx):
    """ Rename modules """
    update_module_names(
        ctx.env.cr,
        [
            # Here we need to list:
            # all modules on which
            # the module is renamed between the old and new version

            # Example:
            # ('account_financial_report_webkit', 'account_financial_report'),
        ],
        merge_modules=True,
    )


@anthem.log
def update_moved_models(ctx):
    """ Update model moved to another module """

    # When a model is moved to another module,
    # if the new module is updated before the old module is uninstalled,
    # the model is removed.

    # That function will update the metadata of the model
    # to indicate to Odoo the new module of the model.

    # Example:

    # update_module_moved_models(
    #     ctx.env.cr,
    #     [
    #         # Here we need to list:
    #         # all models which are moved in another module
    #
    #         'my.custom.model'
    #     ],
    #     'old_module',  # Old module of the models
    #     'new_module',  # New module of the models
    # )


@anthem.log
def update_moved_fields(ctx):
    """ Update fields moved to another module """

    # When a field is moved to another module,
    # if the new module is updated before the old module is uninstalled,
    # the field is removed.

    # That function will update the metadata of the field
    # to indicate to Odoo the new module of the field.

    # Example:

    # update_module_moved_fields(
    #     ctx.env.cr,
    #     'product.template',  # Model of the field
    #     ['purchase_ok'],  # Fields moved
    #     'invoice_webkit',  # Old module of the fields
    #     'product',  # New module of the fields
    # )


@anthem.log
def pre(ctx):
    """ PRE: migration """
    fix_path_on_attachments(ctx)
    rename_modules(ctx)
    update_moved_models(ctx)
    update_moved_fields(ctx)
