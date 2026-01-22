# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleOrder(models.Model):
    """Extend Sale Order to add notes field."""
    
    _inherit = 'sale.order'

    order_notes = fields.Text(
        string='Order Notes',
        help='Additional notes and information for this sales order',
        tracking=True,
    )