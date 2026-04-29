# Copyright (C) 2021 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    net_weight = fields.Float(
        digits="Stock Weight",
        help="Net Weight of the product, container excluded.",
    )

    # Explicit field, renaming it
    weight = fields.Float(string="Gross Weight")



    def write(self, values):
        # Handle net_weight specially to avoid infinite recursion
        if 'net_weight' in values:
            net_weight = values['net_weight']
            # Make a copy of values without net_weight
            other_values = {k: v for k, v in values.items() if k != 'net_weight'}
            # Call super() with other_values first
            result = super().write(other_values)

            # Now handle net_weight directly without triggering write again
            for record in self:
                # Use SQL to update the net_weight directly to avoid recursion
                # This ensures that the value is only updated for the current variant
                self.env.cr.execute(
                    "UPDATE product_product SET net_weight = %s WHERE id = %s",
                    (net_weight, record.id)
                )

                # If it's a single variant product, also update the template
                variant_count = len(record.product_tmpl_id.product_variant_ids)
                if variant_count == 1:
                    self.env.cr.execute(
                        "UPDATE product_template SET net_weight = %s WHERE id = %s",
                        (net_weight, record.product_tmpl_id.id)
                    )

                # Clear the cache to ensure the UI is updated
                record.invalidate_recordset(['net_weight'])
                if variant_count == 1:
                    record.product_tmpl_id.invalidate_recordset(['net_weight'])

            return result
        return super().write(values)

    @api.model_create_multi
    def create(self, vals_list):
        # First create the products without net_weight
        cleaned_vals_list = []
        net_weights = []

        for vals in vals_list:
            net_weights.append(vals.get('net_weight'))
            cleaned_vals = {k: v for k, v in vals.items() if k != 'net_weight'}
            cleaned_vals_list.append(cleaned_vals)

        products = super().create(cleaned_vals_list)

        # Now set the net_weight values directly using SQL
        for product, net_weight in zip(products, net_weights):
            if net_weight is not None:
                # Use SQL to update the net_weight directly
                self.env.cr.execute(
                    "UPDATE product_product SET net_weight = %s WHERE id = %s",
                    (net_weight, product.id)
                )

                # If it's a single variant product, also update the template
                variant_count = len(product.product_tmpl_id.product_variant_ids)
                if variant_count == 1:
                    self.env.cr.execute(
                        "UPDATE product_template SET net_weight = %s WHERE id = %s",
                        (net_weight, product.product_tmpl_id.id)
                    )

                # Clear the cache to ensure the UI is updated
                product.invalidate_recordset(['net_weight'])
                if variant_count == 1:
                    product.product_tmpl_id.invalidate_recordset(['net_weight'])

        return products

    @api.constrains("net_weight", "weight")
    def _check_net_weight(self):
        for product in self:
            if product.weight and product.net_weight > product.weight:
                raise ValidationError(
                    _("The net weight of product must be lower than gross weight.")
                )
