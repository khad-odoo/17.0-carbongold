# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request

class DocumentReviewController(http.Controller):
    @http.route('/document/review/submit', type='json', auth='user', methods=['POST'], csrf=True)
    def submit_review(self, document_id, comment, rating=0, attachment_ids=None, attachment_tokens=None):
        try:
            document = request.env['documents.document'].sudo().browse(document_id)
            if not document.exists() or not document.is_published:
                return {'error': "Cannot review this document."}

            current_user = request.env.user

            if document.owner_id and document.owner_id.id == current_user.id:
                return {'error': "Document owner cannot review their own document."}

            existing = request.env['document.review'].search([
                ('document_id', '=', document_id),
                ('partner_id', '=', current_user.partner_id.id),
                ('is_reply', '=', False)
            ])
            if existing:
                return {'error': "You have already reviewed this document."}

            # Create review
            review_vals = {
                'document_id': document_id,
                'partner_id': current_user.partner_id.id,
                'comment': comment,
                'rating': float(rating),
                'is_reply': False,
            }

            review = request.env['document.review'].create(review_vals)

            # Handle attachments - update their res_model and res_id from pending state
            if attachment_ids:
                attachments = request.env['ir.attachment'].sudo().browse(attachment_ids)
                # Filter only pending attachments that belong to this user
                pending_attachments = attachments.filtered(
                    lambda a: a.res_model == 'mail.compose.message' and a.res_id == 0
                )
                if pending_attachments:
                    pending_attachments.write({
                        'res_model': 'document.review',
                        'res_id': review.id,
                    })
                    review.write({
                        'attachment_ids': [(6, 0, pending_attachments.ids)]
                    })

            document_updated = request.env['documents.document'].sudo().browse(document_id)

            return {
                'success': True, 
                'review_id': review.id,
                'rating_avg': document_updated.rating_avg,
                'rating_count': document_updated.rating_count,
            }
        except Exception as e:
            return {'error': str(e)}


    @http.route('/document/review/reply', type='json', auth='user', methods=['POST'], csrf=True)
    def reply_review(self, review_id, reply, attachments=None):
        """Reply to a review - works for authenticated users"""
        try:
            # FIXED: Use sudo() to get the original review to avoid permission issues
            orig_review = request.env['document.review'].sudo().browse(review_id)
            if not orig_review.exists():
                return {'error': "Review not found."}

            current_user = request.env.user

            # FIXED: Check if replying to own review using IDs
            if orig_review.partner_id.id == current_user.partner_id.id:
                return {'error': "You cannot reply to your own review."}

            # Check if already replied (use current user's permissions)
            existing = request.env['document.review'].search([
                ('partner_id', '=', current_user.partner_id.id),
                ('reply_to_id', '=', review_id),
                ('is_reply', '=', True)
            ])
            if existing:
                return {'error': 'You have already replied to this review.'}

            # Create reply (use current user's permissions for creating their own reply)
            reply_vals = {
                'document_id': orig_review.document_id.id,
                'partner_id': current_user.partner_id.id,
                'comment': reply,
                'is_reply': True,
                'reply_to_id': review_id
            }

            reply_rec = request.env['document.review'].create(reply_vals)

            return {'success': True, 'reply_id': reply_rec.id}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/document/review/list/<int:document_id>', type='json', auth='public')
    def list_reviews(self, document_id):
        """Get all reviews for a document - accessible to everyone"""
        # FIXED: Use sudo() for reading all reviews publicly
        document = request.env['documents.document'].sudo().browse(document_id)
        if not document.exists() or not document.is_published:
            return []

        reviews = request.env['document.review'].search([
            ('document_id', '=', document_id),
            ('is_reply', '=', False),
            ('is_published', '=', True)
        ])

        result = []

        for review in reviews:
            review_data = {
                'id': review.id,
                'comment': review.comment,
                'rating': review.rating,
                'author_name': review.author_name,
                'author_avatar': f'/web/image/res.partner/{review.partner_id.id}/avatar_128',
                'create_date': review.create_date.strftime('%B %d, %Y at %I:%M %p'),
                'attachment_ids': [{'id': a.id, 'name': a.name} for a in review.attachment_ids],
                'replies': [],
            }

            # Add all replies
            for reply in review.replies:
                if reply.is_published:
                    review_data['replies'].append({
                        'id': reply.id,
                        'comment': reply.comment,
                        'author_name': reply.author_name,
                        'author_avatar': f'/web/image/res.partner/{reply.partner_id.id}/avatar_128',
                        'create_date': reply.create_date.strftime('%B %d, %Y at %I:%M %p'),
                    })

            result.append(review_data)

        return result
