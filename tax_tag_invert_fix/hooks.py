import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    cr = env.cr

    cr.execute("""
        SELECT id
        FROM account_account_tag
        WHERE (
            name->>'en_US' ILIKE '%Standard Rate%'
            OR name->>'en_US' ILIKE '%15/ (100%'
        )
        AND tax_negate = FALSE
    """)
    tag_ids = [row[0] for row in cr.fetchall()]
    _logger.info("tax_tag_invert_fix: Found %d tag ids: %s", len(tag_ids), tag_ids)

    if not tag_ids:
        _logger.info("tax_tag_invert_fix: No matching tags found, nothing to fix")
        return

    cr.execute("""
        UPDATE account_move_line aml
        SET tax_tag_invert = FALSE
        FROM account_account_tag_account_move_line_rel rel,
             account_move am
        WHERE rel.account_account_tag_id = ANY(%s)
          AND rel.account_move_line_id = aml.id
          AND am.id = aml.move_id
          AND am.move_type = 'out_invoice'
          AND aml.tax_tag_invert = TRUE
    """, (tag_ids,))
    _logger.info("tax_tag_invert_fix: Updated %d account_move_line rows (tax_tag_invert -> FALSE)", cr.rowcount)
