# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64

from odoo import http
from odoo.exceptions import UserError
from odoo.http import content_disposition, request
from odoo.osv import expression

from odoo.addons.portal.controllers.portal import pager as website_pager

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".pptx", ".xls", ".xlsx", ".csv", ".txt",
    ".jpg", ".jpeg", ".png", ".webp"
}

class DocumentController(http.Controller):
    @http.route(["/documents", "/documents/page/<int:page>"], type="http", auth="public", website=True, sitemap=True)
    def documents(self, category_ids=None, page=1, search="", view_type="grid", **kwargs):
        if category_ids is None:
            category_ids = []
        documents_per_page = 20
        domain = [("is_published", "!=", False)]

        if search:
            domain += [("name", "ilike", search)]

        document_count = request.env["documents.document"].sudo().search_count(domain)

        if category_ids:
            if isinstance(category_ids, str):
                category_ids = [int(x) for x in request.httprequest.args.getlist("category_ids")]
            else:
                category_ids = [int(category_ids)]
            domain = expression.AND([domain, [("document_category_id", "in", category_ids)]])

        pager = website_pager(
            url="/documents",
            total=document_count,
            page=page,
            step=documents_per_page,
            scope=20,
            url_args={"category_ids": category_ids, "search": search, "view_type": view_type},
        )

        documents = (
            request.env["documents.document"]
            .sudo()
            .search(
                domain,
                order="name asc",
                limit=documents_per_page,
                offset=pager["offset"],
            )
        )
        values = {
            "documents": documents,
            "pager": pager,
            "search": search,
            "view_type": view_type,
            "categories": request.env["category.category"].sudo().search([]),
            "search_count": document_count,
            "selected_categories": category_ids,
        }
        return request.render("carbongold_document_management.all_documents", values)

    @http.route(["/document/<string:name>/<int:document_id>"], type="http", auth="public", website=True, sitemap=True)
    def document_detail(self, name, document_id, **kwargs):
        document = request.env["documents.document"].sudo().browse(document_id)
        if not document.is_published:
            return request.not_found()

        document.write({
            'document_click_count': document.document_click_count+1
        })
        values = {"document": request.env["documents.document"].sudo().browse(document_id)}
        return request.render("carbongold_document_management.detail_document_page", values)

    @http.route(["/document/download/<int:document>"], type="http", auth="public", website=True)
    def document_download(self, document, **kwargs):
        document_id = request.env["documents.document"].sudo().browse(document)
        if not document_id.datas:
            return request.not_found()

        try:
            content = base64.b64decode(document_id.datas)
        except Exception as error:
            raise UserError(error)

        document_id.write({
            'document_download_count':document_id.document_download_count + 1
        })

        return request.make_response(
            content,
            headers=[
                ("Cache-Control", "no-store"),
                ("Content-Disposition", content_disposition(document_id.name)),
            ],
        )

    @http.route(['/document/save_document'], type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def save_document(self, **post):
        name = post.get("name")
        description = post.get("description")
        attachment_type = post.get("attachment_type")
        category_id = int(post.get("category"))
        author = post.get('author')

        vals = {
            "name": name,
            "author": author,
            "doc_description": description,
            "owner_id": request.env.user.id,
            "document_category_id": category_id,
            "folder_id": request.env.ref('carbongold_document_management.documents_upload_folder').id,
        }

        if attachment_type == "link":
            vals["url"] = post.get("document_link")
            vals["type"] = "url"
        else:
            upload_file = request.httprequest.files.get("document_file")
            if upload_file:
                try:
                    file_content = upload_file.read()
                    filename = upload_file.filename or ""
                    file_ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
                    if file_ext not in ALLOWED_EXTENSIONS:
                        return request.make_json_response(False)

                    attachment = request.env["ir.attachment"].sudo().create({
                        "name": name,
                        "datas": base64.b64encode(file_content),
                        "mimetype": upload_file.content_type or "application/octet-stream",
                        "res_model": "documents.document",
                    })
                    if attachment:
                        vals["attachment_id"] = attachment.id
                        vals["type"] = "binary"
                except Exception as error:
                    raise UserError(error)
            else:
                return request.make_json_response(False)

        document = request.env["documents.document"].sudo().create(vals)
        
        return request.make_json_response(bool(document))
