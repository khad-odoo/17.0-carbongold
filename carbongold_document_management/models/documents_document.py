# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re

from odoo import api, fields, models

import re
import uuid

class Documents(models.Model):
    _name = "documents.document"
    _inherit = ["documents.document", "website.searchable.mixin", "website.published.multi.mixin"]

    document_category_id = fields.Many2one(comodel_name="category.category", string="Category")
    author = fields.Char("Author")
    doc_description = fields.Char("Description")
    document_click_count = fields.Integer("Document Click Count", default=0)
    document_download_count = fields.Integer("Document Download Count", default=0)
    reviews = fields.One2many('document.review', 'document_id', string='Reviews')
    access_token = fields.Char('Security Token', default=lambda self: uuid.uuid4().hex)
    # Computed rating fields
    rating_avg = fields.Float("Average Rating", compute='_compute_rating_stats', store=True)
    rating_count = fields.Integer("Review Count", compute='_compute_rating_stats', store=True)
    allow_reviews = fields.Boolean("Allow Reviews", default=True)

    @api.depends('reviews.rating', 'reviews.is_published')
    def _compute_rating_stats(self):
        for record in self:
            reviews_with_rating = record.reviews.filtered(lambda r: r.rating > 0 and r.is_published and not r.is_reply)
            if reviews_with_rating:
                record.rating_avg = sum(reviews_with_rating.mapped('rating')) / len(reviews_with_rating)
                record.rating_count = len(reviews_with_rating)
            else:
                record.rating_avg = 0.0
                record.rating_count = 0
                
    def action_publish(self):
        for record in self:
            if not record.is_published:
                record.is_published = True

    @api.model
    def _search_get_detail(self, website, order, options):
        with_image = options["displayImage"]
        with_description = options["displayDescription"]
        search_fields = ["name"]
        fetch_fields = ["id", "name", "type", "url_preview_image"]
        domain = [website.website_domain(), [("is_published", "!=", False)]]
        mapping = {
            "name": {"name": "name", "type": "text", "match": True},
            "website_url": {"name": "url", "type": "text", "truncate": False},
        }
        if with_description:
            search_fields.append("description")
            fetch_fields.append("description")
            mapping["description"] = {"name": "description", "type": "text", "match": True}
        if with_image:
            mapping["image_url"] = {"name": "image_url", "type": "html"}
        return {
            "model": "documents.document",
            "base_domain": domain,
            "requires_sudo": True,
            "search_fields": search_fields,
            "fetch_fields": fetch_fields,
            "mapping": mapping,
            "icon": "fa-rss-square",
            "order": "name desc, id desc" if "name desc" in order else "name asc, id desc",
        }

    def _search_render_results(self, fetch_fields, mapping, icon, limit):
        results_data = super()._search_render_results(fetch_fields, mapping, icon, limit)
        with_image = "image_url" in mapping
        for data in results_data:
            data["url"] = f"/document/{data['id']}"
            if with_image:
                if data["type"] == "binary":
                    data["image_url"] = f"/web/image/documents.document/{data['id']}/thumbnail"
                elif data["type"] == "url" and data["url_preview_image"]:
                    data["image_url"] = f"{data['url_preview_image']}"
                else:
                    data["image_url"] = "/base/static/img/avatar_grey.png"
        return results_data

    def _get_youtube_url_token(self):
        if not self.url:
            return False
        pattern = re.compile(
            r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|v/))([a-zA-Z0-9_-]{11})'
        )
        match = pattern.search(self.url)
        return match.group(1) if match else False
