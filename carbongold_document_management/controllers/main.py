# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64

from odoo import http
from odoo.exceptions import UserError
from odoo.http import content_disposition, request
from odoo.osv import expression

from odoo.addons.portal.controllers.portal import pager as website_pager


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".pptx",
    ".xls",
    ".xlsx",
    ".csv",
    ".txt",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
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

        if category_ids:
            if isinstance(category_ids, str):
                category_ids = [int(x) for x in request.httprequest.args.getlist("category_ids")]
            else:
                category_ids = [int(category_ids)]
            domain = expression.AND([domain, [("document_category_id", "in", category_ids)]])

        document_count = request.env["documents.document"].sudo().search_count(domain)
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
            "parent_categories": request.env["category.category"].sudo().search([("parent_id", "=", False)]),
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
            'document_click_count': document.document_click_count + 1
        })

        values = self._get_document_page_values(document, **kwargs)
        return request.render("carbongold_document_management.detail_document_page", values)

    @http.route(["/document/download/<int:document>"], type="http", auth="public", website=True)
    def document_download(self, document, **kwargs):
        document_id = request.env["documents.document"].sudo().browse(document)
        datas = document_id.attachment_id.datas
        filename = document_id.name or document_id.attachment_id.name
        mimetype = document_id.attachment_id.mimetype or "application/octet-stream"

        if not document_id.attachment_id.datas:
            return request.not_found()

        try:
            content = base64.b64decode(datas)
        except Exception as error:
            raise UserError(error)

        document_id.write({"document_download_count": document_id.document_download_count + 1})

        return request.make_response(
            content,
            headers=[
                ("Content-Type", mimetype),
                ("Cache-Control", "no-store"),
                ("Content-Disposition", content_disposition(filename)),
            ],
        )

    @http.route(["/document/save_document"], type="http", auth="user", methods=["POST"], website=True, csrf=False)
    def save_document(self, **post):
        name = post.get("name")
        attachment_type = post.get("attachment_type")
        document = request.env["documents.document"]

        vals = {
            "name": name,
            "author": post.get("author", ""),
            "doc_description": post.get("description", ""),
            "owner_id": request.env.user.id,
            "document_category_id": int(post.get("category")),
            "folder_id": request.env.ref("carbongold_document_management.documents_upload_folder").id,
        }

        if attachment_type == "link":
            vals["url"] = post.get("document_link")
            vals["type"] = "url"
        else:
            upload_file = request.httprequest.files.get("document_file")
            if upload_file:
                try:
                    file_content = upload_file.read()
                    max_upload_size = document.get_document_max_upload_limit()
                    filename = upload_file.filename or ""
                    if max_upload_size and len(file_content) > max_upload_size:
                        return request.make_json_response(False)

                    file_ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
                    if file_ext not in ALLOWED_EXTENSIONS:
                        return request.make_json_response(False)

                    attachment = (
                        request.env["ir.attachment"]
                        .sudo()
                        .create({
                            "name": name,
                            "datas": base64.b64encode(file_content),
                            "mimetype": upload_file.content_type or "application/octet-stream",
                            "res_model": "documents.document",
                        })
                    )
                    if attachment:
                        vals["attachment_id"] = attachment.id
                        vals["type"] = "binary"
                except Exception as error:
                    raise UserError(error)
            else:
                return request.make_json_response(False)

        document_id = document.sudo().create(vals)
        if document_id and attachment_type == "link":
            document_id._compute_name_and_preview()

        return request.make_json_response(bool(document_id))


    
    def _get_document_page_values(self, document, **kwargs):
        current_user = request.env.user

        values = {
            'document': document,
            'rating_avg': document.rating_avg,
            'rating_count': document.rating_count,
        }

        
        public_user_id = request.env.ref('base.public_user').id
        is_anonymous = current_user.id == public_user_id
        is_authenticated = not is_anonymous  # Any user that's not the anonymous public user

        # Check if current authenticated user has already reviewed
        user_has_reviewed = False
        if is_authenticated:
            user_review = request.env['document.review'].search([
                ('document_id', '=', document.id),
                ('partner_id', '=', current_user.partner_id.id),
                ('is_reply', '=', False),
            ], limit=1)
            user_has_reviewed = bool(user_review)

        # Simple component props
        component_values = {
            'documentId': document.id,
            'documentName': document.name,
            'isLoggedIn': is_authenticated,
            'userHasReviewed': user_has_reviewed,
            'currentUserId': current_user.id if is_authenticated else False,
            'currentPartnerName': current_user.partner_id.name if is_authenticated else '',
            'csrfToken': request.csrf_token(),
        }

        values['component_values'] = component_values
        return values
