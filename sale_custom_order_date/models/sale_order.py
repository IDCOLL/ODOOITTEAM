# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleOrder(models.Model):
    """Extend Sale Order to add custom order date field."""
    
    _inherit = 'sale.order'

    custom_order_date = fields.Date(
        string='Custom Order',
        help='Custom order date that can be manually set for this quotation/order',
        copy=False,
        tracking=True,
    )