import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Step a: Find account_account_tag ids matching Standard Rate or 15/ (100% (non-negated)
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
    _logger.info("Step a: Found %d account_account_tag ids: %s", len(tag_ids), tag_ids)

    # Step b: Reset tax_tag_invert on posted out_invoice lines linked to those tags
    if tag_ids:
        cr.execute("""
            UPDATE account_move_line aml
            SET tax_tag_invert = FALSE
            FROM account_account_tag_account_move_line_rel rel,
                 account_move am
            WHERE rel.account_account_tag_id = ANY(%s)
              AND rel.account_move_line_id = aml.id
              AND am.id = aml.move_id
              AND am.move_type = 'out_invoice'
              AND am.state = 'posted'
              AND aml.tax_tag_invert = TRUE
        """, (tag_ids,))
        _logger.info("Step b: Updated %d account_move_line rows (tax_tag_invert -> FALSE)", cr.rowcount)
    else:
        _logger.info("Step b: No matching tags found, skipping account_move_line update")

    # Step c: Mark IoT/POS hardware modules as uninstalled where they are uninstallable
    cr.execute("""
        UPDATE ir_module_module
        SET state = 'uninstalled'
        WHERE name IN (
            'hw_drivers',
            'hw_escpos',
            'hw_l10n_eg_eta',
            'hw_posbox_homepage',
            'pos_hr_l10n_be'
        )
        AND state = 'uninstallable'
    """)
    _logger.info("Step c: Updated %d ir_module_module rows (state -> uninstalled)", cr.rowcount)

    # Step d: Remove obsolete modules and their metadata/dependencies
    modules_to_remove = (
        'account_reports_fix',
        'partner_statement',
        'partner_statement_v14_10',
        'bi_customer_overdue_statement',
    )

    cr.execute("""
        DELETE FROM ir_model_data
        WHERE module = ANY(%s)
    """, (list(modules_to_remove),))
    _logger.info("Step d1: Deleted %d ir_model_data rows", cr.rowcount)

    cr.execute("""
        DELETE FROM ir_module_module_dependency
        WHERE module_id IN (
            SELECT id FROM ir_module_module WHERE name = ANY(%s)
        )
    """, (list(modules_to_remove),))
    _logger.info("Step d2: Deleted %d ir_module_module_dependency rows", cr.rowcount)

    cr.execute("""
        DELETE FROM ir_module_module
        WHERE name = ANY(%s)
    """, (list(modules_to_remove),))
    _logger.info("Step d3: Deleted %d ir_module_module rows", cr.rowcount)
