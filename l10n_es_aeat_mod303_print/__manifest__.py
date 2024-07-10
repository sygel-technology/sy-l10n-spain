# Copyright 2020 Valentin Vinagre <valentin.vinagre@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "AEAT Modelo 303 Imprimir",
    "summary": "PDF del model 303",
    "version": "15.0.1.0.0",
    "category": "Uncategorized",
    "website": "https://github.com/sygel-technology/sy-l10n-spain",
    "author": "Sygel, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "l10n_es_aeat_mod303",
    ],
    "data": [
        "report/aeat_mod303.xml",
        "report/report_views.xml",
    ],
}
