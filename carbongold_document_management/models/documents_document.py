# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

from odoo.addons.http_routing.models.ir_http import slug
import re


class Documents(models.Model):
    _name = "documents.document"
    _inherit = ["documents.document", "website.searchable.mixin", "website.published.multi.mixin"]

    document_category_id = fields.Many2one(comodel_name="category.category", string="Category")
    rating_avg = fields.Integer()
    rating_count = fields.Integer()
    author = fields.Char("Author")
    doc_description = fields.Char("Description")
    document_click_count = fields.Integer("Document Click Count", default=0)
    document_download_count = fields.Integer("Document Download Count", default=0)

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
            document = self.env["documents.document"].browse(data["id"])
            data["url"] = f"/document/{slug(document)}/{data['id']}"
            if with_image:
                if data["type"] == "binary":
                    data["image_url"] = f"/web/image/documents.document/{data['id']}/thumbnail"
                elif data["type"] == "url" and data["url_preview_image"]:
                    data["image_url"] = f"{data['url_preview_image']}"
                else:
                    data["image_url"] = "/base/static/img/avatar_grey.png"
        return results_data

    def _get_youtubeUrlToken(self):
        if not self.url:
            return False
        pattern = re.compile(
            r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|v/))([a-zA-Z0-9_-]{11})'
        )
        match = pattern.search(self.url)
        return match.group(1) if match else False
