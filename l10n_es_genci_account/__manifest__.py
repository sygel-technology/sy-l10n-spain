# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Tasa Genci",
    "summary": "Gestión tarifas GENCI",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Sygel",
    "website": "https://github.com/sygel-technology/sy-l10n-spain",
    "category": "Accounting",
    "depends": [
        "account",
        "account_invoice_margin",
    ],
    "data": [
        "data/data.xml",
        "security/ir.model.access.csv",
        "security/genci_groups.xml",
        "views/l10n_es_genci_views.xml",
        "views/product_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/account_move_views.xml",
        "views/account_fiscal_position_views.xml",
        "report/report_invoice.xml",
    ],
    "installable": True,
}
