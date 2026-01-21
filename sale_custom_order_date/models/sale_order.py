# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    """Extend Sale Order to add custom order date field."""
    
    _inherit = 'sale.order'

    custom_order_date = fields.Date(
        string='Custom Order',
        help='Custom date field for manual date selection on sales orders and quotes.',
        copy=False,
        tracking=True,
    )

    @api.constrains('custom_order_date')
    def _check_custom_order_date(self):
        """Validate that custom order date is not in the far future if set.
        
        This is a soft validation to prevent accidental typos in date entry.
        """
        for order in self:
            if order.custom_order_date:
                # Allow dates up to 10 years in the future
                max_date = fields.Date.today().replace(year=fields.Date.today().year + 10)
                if order.custom_order_date > max_date:
                    _logger.warning(
                        'Custom order date %s on SO %s is more than 10 years in the future',
                        order.custom_order_date,
                        order.name
                    )
