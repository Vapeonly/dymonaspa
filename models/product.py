# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import datetime

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_dhz_quick_print_label(self):
        self.ensure_one()
        # Update x_studio_cos_magazin_id with current date
        if hasattr(self, 'x_studio_cos_magazin_id'):
            current_date = datetime.now().strftime('%d.%m.%Y')
            self.x_studio_cos_magazin_id = current_date
        product_id = self.id
        url = f"/dhz_label/quick_print?model=product.product&ids={product_id}"
        return {'type': 'ir.actions.act_url', 'name': 'DHZ Quick Print', 'url': url, 'target': 'new'}

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_dhz_quick_print_label(self):
        self.ensure_one()
        # Get the product variant with archived products included
        product = self.with_context(active_test=False).product_variant_id
        # Update x_studio_cos_magazin_id with current date on the product variant
        if product and hasattr(product, 'x_studio_cos_magazin_id'):
            current_date = datetime.now().strftime('%d.%m.%Y')
            product.x_studio_cos_magazin_id = current_date
        product_id = product.id if product else False
        url = f"/dhz_label/quick_print?model=product.product&ids={product_id}"
        return {'type': 'ir.actions.act_url', 'name': 'DHZ Quick Print', 'url': url, 'target': 'new'}
