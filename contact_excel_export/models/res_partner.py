# -*- coding: utf-8 -*-

import base64
import io
import logging
import re
from odoo import models, api, _
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Extend res.partner to add Excel export functionality."""
    
    _inherit = 'res.partner'

    def _sanitize_filename(self, name):
        """Sanitize filename to remove invalid characters.
        
        Args:
            name (str): The original filename
            
        Returns:
            str: Sanitized filename safe for file systems
        """
        if not name:
            return 'Contact'
        # Remove or replace invalid filename characters
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        # Replace spaces with underscores
        name = name.replace(' ', '_')
        # Limit length to avoid filesystem issues
        return name[:50] if name else 'Contact'

    @api.model
    def _get_excel_headers(self):
        """Define Excel column headers.
        
        Returns:
            list: List of column header names
        """
        return [
            'Name',
            'Phone',
            'Email',
            'Street',
            'Street 2',
            'City',
            'State',
            'ZIP',
            'Country',
        ]

    def _get_contact_data(self):
        """Extract contact data for Excel export.
        
        Returns:
            list: List containing contact field values
        """
        self.ensure_one()
        return [
            self.name or '',
            self.phone or '',
            self.email or '',
            self.street or '',
            self.street2 or '',
            self.city or '',
            self.state_id.name if self.state_id else '',
            self.zip or '',
            self.country_id.name if self.country_id else '',
        ]

    def action_export_contact_excel(self):
        """Generate and download Excel file with contact information.
        
        Returns:
            dict: Action to download the generated Excel file
            
        Raises:
            UserError: If xlsxwriter is not available or file generation fails
        """
        self.ensure_one()
        
        if not xlsxwriter:
            raise UserError(_(
                'The xlsxwriter Python library is not installed. '
                'Please contact your system administrator.'
            ))
        
        try:
            # Create Excel file in memory
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Contact Information')
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
            })
            
            data_format = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'top',
                'text_wrap': True,
            })
            
            # Write headers
            headers = self._get_excel_headers()
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
            
            # Write contact data
            contact_data = self._get_contact_data()
            for col, value in enumerate(contact_data):
                worksheet.write(1, col, value, data_format)
            
            # Adjust column widths
            worksheet.set_column(0, 0, 25)  # Name
            worksheet.set_column(1, 2, 15)  # Phone, Mobile
            worksheet.set_column(3, 3, 30)  # Email
            worksheet.set_column(4, 5, 30)  # Street, Street2
            worksheet.set_column(6, 6, 20)  # City
            worksheet.set_column(7, 7, 20)  # State
            worksheet.set_column(8, 8, 12)  # ZIP
            worksheet.set_column(9, 9, 20)  # Country
            
            # Set row height for data row
            worksheet.set_row(1, 30)
            
            # Close workbook and get file content
            workbook.close()
            excel_data = output.getvalue()
            output.close()
            
            # Generate filename
            safe_name = self._sanitize_filename(self.name)
            filename = f'{safe_name}_Contact.xlsx'
            
            # Create attachment
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(excel_data),
                'res_model': 'res.partner',
                'res_id': self.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })
            
            # Return download action
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }
            
        except Exception as e:
            _logger.error(
                'Error generating Excel file for contact %s: %s',
                self.id,
                str(e),
                exc_info=True
            )
            raise UserError(_(
                'An error occurred while generating the Excel file: %s'
            ) % str(e))
