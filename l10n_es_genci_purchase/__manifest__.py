# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Tasa Genci - Compras",
    "summary": "Gestión tarifas GENCI - Compras",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "author": "Sygel",
    "website": "https://github.com/sygel-technology/sy-l10n-spain",
    "category": "Accounting",
    "depends": [
        "purchase",
        "l10n_es_genci_account",
    ],
    "data": [
        "views/purchase_order_views.xml",
        "report/purchase_report_template.xml",
    ],
    "installable": True,
}
