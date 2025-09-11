# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class DocumentsCategory(models.Model):
    _name = "category.category"
    _description = "Documents Category"

    name = fields.Char(string="Name")
