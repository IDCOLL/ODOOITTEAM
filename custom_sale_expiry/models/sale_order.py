# -*- coding: utf-8 -*-

from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    personal_expiry_date = fields.Date(
        string='Personal Expiry Date',
        help='Personal expiry date for tracking purposes',
        tracking=True,
        copy=False,
    )
