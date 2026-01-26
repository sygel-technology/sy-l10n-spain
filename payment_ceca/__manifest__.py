# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Ceca Payment Acquirer",
    "version": "15.0.1.0.0",
    "category": "Payment",
    "website": "https://github.com/sygel-technology/sy-l10n-spain",
    "author": "Sygel, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "account",
        "payment",
        "sale",
    ],
    "data": [
        "views/payment_ceca_templates.xml",
        "views/payment_acquirer_view.xml",
        "data/payment_ceca_data.xml",
    ],
    "installable": True,
}
