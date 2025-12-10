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
                # Returns tuple of (field_name, model_name, target_field_name)
                target_field = fname[8:]  # Remove 'default_' prefix
                result['default'].append((fname, field.default_model, target_field))
            else:
                # Skip fields without default_model instead of raising
                result['other'].append(fname)
        elif fname.startswith('group_'):
            if hasattr(field, 'implied_group') and field.implied_group:
                result['group'].append((fname, field.implied_group))
            else:
                result['other'].append(fname)
        elif fname.startswith('module_'):
            result['module'].append((fname, fname[7:]))  # Remove 'module_' prefix
        elif fname.startswith('config_'):
            result['config'].append((fname,))
        else:
            result['other'].append(fname)
    
    return result


BaseResConfigSettings._get_classified_fields = _get_classified_fields_fixed