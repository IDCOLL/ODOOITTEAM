{
    'name': 'Tax Tag Invert Fix',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Fixes incorrect tax_tag_invert values on out_invoice lines',
    'depends': ['account'],
    'post_init_hook': 'post_init_hook',
    'auto_install': False,
    'license': 'LGPL-3',
}
