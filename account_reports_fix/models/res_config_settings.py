from odoo.addons.base.models.res_config import ResConfigSettings as BaseResConfigSettings


original_get_classified_fields = BaseResConfigSettings._get_classified_fields


def _get_classified_fields_fixed(self, fnames):
    """Patch to handle fields with missing default_model attribute."""
    result = {
        'default': [],
        'group': [],
        'module': [],
        'config': [],
        'other': [],
    }
    
    for fname in fnames:
        field = self._fields.get(fname)
        if not field:
            continue
            
        if fname.startswith('default_'):
            if hasattr(field, 'default_model') and field.default_model:
                result['default'].append(fname)
            else:
                # Skip fields without default_model instead of raising
                result['other'].append(fname)
        elif fname.startswith('group_'):
            result['group'].append(fname)
        elif fname.startswith('module_'):
            result['module'].append(fname)
        elif fname.startswith('config_'):
            result['config'].append(fname)
        else:
            result['other'].append(fname)
    
    return result


BaseResConfigSettings._get_classified_fields = _get_classified_fields_fixed