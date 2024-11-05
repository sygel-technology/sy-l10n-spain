import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-sygel-technology-sy-l10n-spain",
    description="Meta package for sygel-technology-sy-l10n-spain Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-l10n_es_aeat_mod303_print',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
