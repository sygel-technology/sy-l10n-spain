# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Sy L10N ES AEAT SII OCA Manual Result",
    "summary": "Adds a wizard to edit Sii fields values on invoices",
    "version": "17.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/sygel-technology/sy-l10n-spain",
    "author": "Sygel",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "l10n_es_aeat_sii_oca",
    ],
    "data": [
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "wizards/account_move_manual_sii_result_wizard_views.xml",
    ],
}
