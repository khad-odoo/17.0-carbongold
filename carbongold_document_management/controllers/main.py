# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import json
from odoo import http
from odoo.exceptions import UserError
from odoo.http import content_disposition, request
from odoo.osv import expression

from odoo.addons.portal.controllers.portal import pager as website_pager
from odoo.tools import image_process
from base64 import b64decode


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
    ".zip",
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
            domain = expression.AND([domain, [("document_category_ids", "in", category_ids)]])

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
                order="write_date DESC",
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
            "category_props": {"all_cat_ids" : request.env["category.category"].sudo().search_read([], ["id", "name"], order="name")}
        }
        return request.render("carbongold_document_management.all_documents", values)

    @http.route(["/document/<int:document_id>"], type="http", auth="public", website=True, sitemap=True)
    def document_detail(self, document_id, **kwargs):
        document = request.env["documents.document"].sudo().browse(document_id)
        if not document.is_published:
            return request.not_found()

        document.write({"document_click_count": document.document_click_count + 1})

        values = self._get_document_page_values(document, **kwargs)
        return request.render("carbongold_document_management.detail_document_page", values)

    @http.route(["/document/download/<int:document>"], type="http", auth="public", website=True)
    def document_download(self, document, **kwargs):
        document_id = request.env["documents.document"].sudo().browse(document)
        datas = document_id.attachment_id.datas
        extension = document_id.attachment_id.mimetype.replace('application/', '').replace(';base64', '')
        filename = f'{document_id.name}.{extension}'
        mimetype = document_id.attachment_id.mimetype or "application/octet-stream"

        if not document_id.attachment_id.datas:
            return request.not_found()

        try:
            content = base64.b64decode(datas)
        except Exception as error:
            raise UserError("Error downloading the document: %s" % error) from error

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
            "document_category_ids": [(6, 0, json.loads(post.get("category_ids") or []))],
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
                    raise UserError("Error saving the document: %s" % error) from error
            else:
                return request.make_json_response(False)

        document_id = document.sudo().create(vals)
        if document_id and attachment_type == "link":
            document_id._compute_name_and_preview()

        upload_thumbnail = request.httprequest.files.get("thumbnail")
        if upload_thumbnail and document_id:
            filename = upload_thumbnail.filename
            file_ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
            if file_ext not in {".jpg", ".jpeg", ".png", ".webp", ".svg"}:
                raise UserError("Only JPG and PNG images are supported.")

            try:
                file_content = upload_thumbnail.read()
                processed = base64.b64encode(file_content)
                document_id.write({"thumbnail": processed})

            except Exception as error:
                raise UserError("Error saving the document: %s" % error) from error

        return request.make_json_response(bool(document_id))

    def _get_document_page_values(self, document, **kwargs):
        current_user = request.env.user

        values = {
            "document": document,
            "rating_avg": document.rating_avg,
            "rating_count": document.rating_count,
        }

        public_user_id = request.env.ref("base.public_user").id
        is_anonymous = current_user.id == public_user_id
        is_authenticated = not is_anonymous  # Any user that's not the anonymous public user

        is_document_owner = False
        if is_authenticated and document.owner_id:
            is_document_owner = document.owner_id.id == current_user.id

        # Check if current authenticated user has already reviewed
        user_has_reviewed = False
        if is_authenticated and not is_document_owner:  # Only check if not owner
            user_reviews = document.reviews.filtered(
                lambda r: not r.is_reply and r.partner_id.id == current_user.partner_id.id
            )
            user_has_reviewed = bool(user_reviews)
        reviews_data = self._get_reviews_data(document)

        # Component props
        component_values = {
            "documentId": document.id,
            "documentName": document.name,
            "isLoggedIn": is_authenticated,
            "isDocumentOwner": is_document_owner,
            "userHasReviewed": user_has_reviewed,
            "currentUserId": current_user.id if is_authenticated else False,
            "currentPartnerName": current_user.partner_id.name if is_authenticated else "",
            "csrfToken": request.csrf_token(),
            "reviews": reviews_data,
        }

        values["component_values"] = component_values
        return values

    def _get_reviews_data(self, document):
        reviews_data = []

        for review in document.reviews:
            if not review.is_reply and review.is_published:
                review_data = {
                    "id": review.id,
                    "comment": review.comment,
                    "rating": review.rating,
                    "author_name": review.author_name,
                    "author_avatar": f"/web/image/res.partner/{review.partner_id.id}/avatar_128",
                    "create_date": review.create_date.strftime("%B %d, %Y at %I:%M %p"),
                    "attachment_ids": self._get_attachment_data(review.attachment_ids),
                    "replies": [],
                }

                published_replies = review.replies.filtered(lambda r: r.is_published)

                for reply in published_replies:
                    review_data["replies"].append({
                        "id": reply.id,
                        "comment": reply.comment,
                        "author_name": reply.author_name,
                        "author_avatar": f"/web/image/res.partner/{reply.partner_id.id}/avatar_128",
                        "create_date": reply.create_date.strftime("%B %d, %Y at %I:%M %p"),
                        "attachment_ids": self._get_attachment_data(reply.attachment_ids),
                    })

                reviews_data.append(review_data)

        return reviews_data

    def _get_attachment_data(self, attachments):
        return [
            {
                "id": att.id,
                "name": att.name,
                "mimetype": att.mimetype,
                "file_size": att.file_size,
                "access_token": att.access_token,
            }
            for att in attachments
        ]
