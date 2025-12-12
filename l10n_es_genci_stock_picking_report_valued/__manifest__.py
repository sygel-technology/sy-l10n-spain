# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "GENCI Report Picking Valued",
    "summary": "Show GENCI amount in valued stock pickings",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Sygel",
    "website": "https://github.com/sygel-technology/sy-l10n-spain",
    "category": "Accounting",
    "depends": [
        "stock_picking_report_valued",
        "l10n_es_genci_sale",
    ],
    "data": [
        "report/stock_picking_report_valued_template.xml",
    ],
    "installable": True,
}
