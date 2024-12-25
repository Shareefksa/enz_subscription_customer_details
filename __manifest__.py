{
    "name": "Enz Subscription",
    "description": """For Storing Customer and Subsciption Details""",
    "summary": """This app helps to interact with odoo
     backend with help of rest api requests""",
    "category": "Tools",
    "version": "16.0.1.0.0",
    'author': 'Enzapps',
    'company': 'Enzapps',
    'maintainer': 'Enzapps',
    'website': "https://www.enzapps.com",
    "depends": ['base', 'web','mail','contacts'],
    "data": [
        "data/sequence.xml",
        "security/ir.model.access.csv",
        'views/res_device_configuration.xml',
        'views/res_partner.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
