# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import datetime

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _dhz_do_print(self):
        """Helper method to print label"""
        self.ensure_one()
        product_id = self.id
        url = f"/dhz_label/quick_print?model=product.product&ids={product_id}"
        return {'type': 'ir.actions.act_url', 'name': 'DHZ Quick Print', 'url': url, 'target': 'new'}

    def action_dhz_quick_print_original(self):
        """Print without updating date"""
        return self._dhz_do_print()

    def action_dhz_quick_print_label(self):
        """Print and update Cos ID magazin with current date"""
        self.ensure_one()
        try:
            current_date = datetime.now().strftime('%d.%m.%Y')
            self.write({'x_studio_cos_magazin_id': current_date})
        except Exception as e:
            pass  # Field doesn't exist, ignore
        return self._dhz_do_print()

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _dhz_do_print(self):
        """Helper method to print label"""
        self.ensure_one()
        product = self.with_context(active_test=False).product_variant_id
        product_id = product.id if product else False
        url = f"/dhz_label/quick_print?model=product.product&ids={product_id}"
        return {'type': 'ir.actions.act_url', 'name': 'DHZ Quick Print', 'url': url, 'target': 'new'}

    def action_dhz_quick_print_original(self):
        """Print without updating date"""
        return self._dhz_do_print()

    def action_dhz_quick_print_label(self):
        """Print and update Cos ID magazin with current date"""
        self.ensure_one()
        product = self.with_context(active_test=False).product_variant_id
        if product:
            try:
                current_date = datetime.now().strftime('%d.%m.%Y')
                product.write({'x_studio_cos_magazin_id': current_date})
            except Exception as e:
                pass  # Field doesn't exist, ignore
        return self._dhz_do_print()
