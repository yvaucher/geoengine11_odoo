# -*- coding: utf-8 -*-
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os

from base64 import b64encode
from pkg_resources import resource_string

import anthem

from ..common import req


@anthem.log
def setup_company(ctx):
    """ Setup company """
    # load logo on company
    logo_content = resource_string(req, 'data/images/company_main_logo.png')
    b64_logo = b64encode(logo_content)

    values = {
        'name': "geo_11",
        'street': "",
        'zip': "",
        'city': "",
        'country_id': ctx.env.ref('base.ch').id,
        'phone': "+41 00 000 00 00",
        'fax': "+41 00 000 00 00",
        'email': "contact@geo_11.ch",
        'website': "http://www.geo_11.ch",
        'vat': "VAT",
        'logo': b64_logo,
        'currency_id': ctx.env.ref('base.CHF').id,
    }
    ctx.env.ref('base.main_company').write(values)


@anthem.log
def setup_language(ctx):
    """ Installing language and configuring locale formatting """
    for code in ('fr_FR',):
        ctx.env['base.language.install'].create({'lang': code}).lang_install()
    ctx.env['res.lang'].search([]).write({
        'grouping': [3, 0],
        'date_format': '%d/%m/%Y',
    })


@anthem.log
def admin_user_password(ctx):
    """ Changing admin password """
    # TODO: default admin password, must be changed.
    # Please add your new password in lastpass with the following name:
    # [odoo-test] geo_11 test admin user
    # In the lastpass directory: Shared-C2C-Odoo-External
    # To get an encrypted password:
    # $ docker-compose run --rm odoo python -c \
    # "from passlib.context import CryptContext; \
    #  print CryptContext(['pbkdf2_sha512']).encrypt('my_password')"
    if os.environ.get('RUNNING_ENV') == 'dev':
        ctx.log_line('Not changing password for dev RUNNING_ENV')
        return
    ctx.env.user.password_crypt = (
        '$pbkdf2-sha512$19000$tVYq5dwbI0Tofc85RwiBcA$a1tNyzZ0hxW9kXKIyEwN1'
        'j84z5gIIi1PQmvtFHuxQ4rNA2RaXSGLjXnEifl6ZQZ/wiBJK6fZkeaGgF3DW9A2Bg'
    )


@anthem.log
def main(ctx):
    """ Main: creating base config """
    setup_company(ctx)
    setup_language(ctx)
    admin_user_password(ctx)
