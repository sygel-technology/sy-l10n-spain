# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Tasa Genci - Ventas",
    "summary": "Gestión tarifas GENCI - Ventas",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Sygel",
    "website": "https://github.com/sygel-technology/sy-l10n-spain",
    "category": "Accounting",
    "depends": ["sale", "l10n_es_genci_account", "account_invoice_margin_sale"],
    "data": [
        "views/sale_order_views.xml",
        "report/sale_report_template.xml",
    ],
    "installable": True,
}
