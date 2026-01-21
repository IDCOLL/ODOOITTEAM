# -*- coding: utf-8 -*-
{
    'name': 'Sales Custom Order Date',
    'version': '19.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Add custom order date field to sales orders',
    'description': """
        Sales Custom Order Date
        =======================
        This module adds a custom order date field to sales orders and quotes,
        allowing users to manually set a custom date for tracking purposes.
    """,
    'author': 'THE IT TEAM (Pty) Ltd',
    'website': 'https://www.theitteam.co.za',
    'license': 'LGPL-3',
    'depends': ['sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
