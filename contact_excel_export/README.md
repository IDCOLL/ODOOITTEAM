# Contact Excel Export

## Overview

This Odoo module adds Excel export functionality to contact forms, allowing users to download contact information in a well-formatted Excel spreadsheet.

## Features

- **One-Click Export**: Download contact information with a single button click
- **Detailed Information**: Exports name, phone, mobile, email, and complete address
- **Address Breakdown**: Separate columns for street, street2, city, state, ZIP, and country
- **Professional Formatting**: Excel file includes formatted headers and borders
- **Smart File Naming**: Files are automatically named after the contact
- **Error Handling**: Graceful handling of missing data and export errors

## Installation

1. Copy the `contact_excel_export` folder to your Odoo addons directory
2. Update the apps list in Odoo
3. Install the "Contact Excel Export" module

## Usage

1. Navigate to Contacts menu
2. Open any contact record
3. Click the "Download Excel" button in the form header
4. The Excel file will be downloaded automatically

## Excel File Structure

The exported Excel file contains the following columns:

- Name
- Phone
- Mobile
- Email
- Street
- Street 2
- City
- State
- ZIP
- Country

## Technical Details

- **Odoo Version**: 19.0
- **Dependencies**: base, contacts
- **Python Library**: xlsxwriter (included in Odoo)
- **License**: LGPL-3

## Requirements

- Odoo 19.0 or higher
- xlsxwriter Python library (standard in Odoo)

## Support

For support and questions, please contact THE IT TEAM (Pty) Ltd.

## Author

THE IT TEAM (Pty) Ltd

## License

LGPL-3
