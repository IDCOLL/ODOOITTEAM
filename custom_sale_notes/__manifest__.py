# -*- coding: utf-8 -*-
{
    'name': 'Sales Order Notes',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Add notes field to Sales Orders',
    'description': """
        Sales Order Notes
        =================
        This module adds a notes field to the sales order form where users can
        type additional information and notes related to the order.
        
        Features:
        ---------
        * Text field for notes on sales order
        * Visible in main section of sales order form
        * Easy access for sales team members
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