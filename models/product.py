# -*- coding: utf-8 -*-
from odoo import models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_dhz_quick_print_label(self):
        self.ensure_one()
        url = f"/dhz_label/quick_print?model=product.product&ids={self.id}"
        return {'type': 'ir.actions.act_url', 'name': 'DHZ Quick Print', 'url': url, 'target': 'new'}

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_dhz_quick_print_label(self):
        self.ensure_one()
        product = self.product_variant_id
        url = f"/dhz_label/quick_print?model=product.product&ids={product.id}"
        return {'type': 'ir.actions.act_url', 'name': 'DHZ Quick Print', 'url': url, 'target': 'new'}
