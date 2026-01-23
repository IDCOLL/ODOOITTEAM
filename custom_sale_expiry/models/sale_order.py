# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    """Extend Sale Order to add personal expiry date field."""
    
    _inherit = 'sale.order'

    personal_expiry_date = fields.Date(
        string='Personal Expiry Date',
        help='Date when this sales order expires for personal tracking purposes',
        tracking=True,
        copy=False,
    )