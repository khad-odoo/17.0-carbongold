# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class DocumentsCategory(models.Model):
    _name = "category.category"
    _description = "Documents Category"

    name = fields.Char()
    parent_id = fields.Many2one("category.category", string="Parent Category", ondelete="cascade")
    child_ids = fields.One2many("category.category", "parent_id", "Child Categories")

    @api.constrains("parent_id")
    def _check_category_recursion(self):
        for category in self:
            if not category._check_recursion() or category.parent_id.parent_id:
                raise ValidationError(_("You cannot create recursive categories."))

    def _get_all_subcategory_ids(self):
        category_ids = self.ids
        for category in self:
            if category.child_ids:
                category_ids += category.child_ids._get_all_subcategory_ids()
        return category_ids
