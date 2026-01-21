# -*- coding: utf-8 -*-
{
    'name': 'Contact Excel Export',
    'version': '19.0.1.0.0',
    'category': 'Contacts',
    'summary': 'Export individual contact details to Excel',
    'description': """
        Contact Excel Export
        ====================
        This module adds an Excel export button to contact forms that allows
        downloading contact information including name, phone, and detailed
        address fields in Excel format.
        
        Features:
        ---------
        * Export button on contact form view
        * Excel file named after the contact
        * Detailed address breakdown (street, city, state, zip, country)
        * Includes phone, mobile, and email information
    """,
    'author': 'THE IT TEAM (Pty) Ltd',
    'website': 'https://www.theitteam.co.za',
    'license': 'LGPL-3',
    'depends': ['base', 'contacts'],
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
