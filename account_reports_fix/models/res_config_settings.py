from odoo.addons.base.models.res_config import ResConfigSettings as BaseResConfigSettings


original_get_classified_fields = BaseResConfigSettings._get_classified_fields


def _get_classified_fields_fixed(self, fnames):
    """Patch to skip fields that would raise due to missing default_model."""
    
    # Filter out problematic default_ fields before calling original
    safe_fnames = []
    skipped = []
    
    for fname in fnames:
        if fname.startswith('default_'):
            field = self._fields.get(fname)
            if field and (not hasattr(field, 'default_model') or not field.default_model):
                skipped.append(fname)
                continue
        safe_fnames.append(fname)
    
    # Call original with safe fields
    result = original_get_classified_fields(self, safe_fnames)
    
    # Add skipped fields to 'other'
    result['other'].extend(skipped)
    
    return result


BaseResConfigSettings._get_classified_fields = _get_classified_fields_fixed