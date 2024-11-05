import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-sygel-technology-sy-l10n-spain",
    description="Meta package for sygel-technology-sy-l10n-spain Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-l10n_es_aeat_mod303_print>=15.0dev,<15.1dev',
        'odoo-addon-l10n_es_facturae_custom_rounding>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
