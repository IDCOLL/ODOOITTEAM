# -*- coding: utf-8 -*-
{
    'name': 'Sales Order Expiry Date',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Add personal expiry date field to Sales Orders',
    'description': """
        Sales Order Expiry Date
        =======================
        
        This module adds a personal expiry date field to Sales Orders,
        allowing users to track expiry dates for personal purposes.
        
        Features:
        ---------
        * New date field on Sales Orders
        * Positioned below Payment Terms field
        * Tracked in chatter for audit trail
        * Accessible to all sales users
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
