# -*- coding: utf-8 -*-
{
    'name': 'Sales Order Personal Expiry Date',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Add personal expiry date field to Sales Orders',
    'description': """
        Sales Order Personal Expiry Date
        =================================
        This module adds a date field to Sales Orders for tracking personal expiry dates.
        
        Features:
        ---------
        * Adds a 'Personal Expiry Date' field to Sales Orders
        * Field is visible in the main form view
        * Changes are tracked in the chatter
        * Compatible with Odoo 19.0
    """,
    'author': 'THE IT TEAM (Pty) Ltd',
    'website': 'https://www.theitteam.co.za',
    'depends': ['sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}