# -*- coding: utf-8 -*-
{
    'name': 'Sale Custom Order Date',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Add Custom Order date field to Sales Orders',
    'description': """
        Sale Custom Order Date
        ======================
        This module adds a custom order date field to sales orders/quotations.
        
        Features:
        ---------
        * Adds 'Custom Order' date field to sale.order
        * Field is visible and editable on quotation/order form
        * Manually selectable by users
    """,
    'author': 'THE IT TEAM (Pty) Ltd',
    'website': 'https://www.theitteam.co.za',
    'depends': ['sale_management'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}