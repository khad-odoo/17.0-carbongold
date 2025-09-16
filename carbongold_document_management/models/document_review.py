# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import uuid

class DocumentReview(models.Model):
    _name = "document.review"
    _description = "Document Review"
    _order = 'create_date desc, id desc'
    _rec_name = 'comment'

    create_date = fields.Datetime(string="Reviewed on", default=fields.Datetime.now)
    document_id = fields.Many2one('documents.document', string='Document', required=True, index=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Reviewer', required=True)
    comment = fields.Text('Review Comment', required=True)
    rating = fields.Float('Rating', default=0, help="Rating from 1 to 5 stars")
    attachment_ids = fields.Many2many('ir.attachment', 'review_attachment_rel', 'review_id', 'attachment_id', string='Attachments')
    is_reply = fields.Boolean('Is Reply', default=False)
    reply_to_id = fields.Many2one('document.review', string='Reply To', domain="[('is_reply', '=', False)]")
    access_token = fields.Char('Security Token', default=lambda self: uuid.uuid4().hex)
    is_published = fields.Boolean(string='Published', default=False)
    
    # Helper fields
    author_name = fields.Char(related='partner_id.name', string='Author Name', readonly=True)
    author_avatar = fields.Binary(related='partner_id.avatar_128', string='Author Avatar', readonly=True)
    replies = fields.One2many('document.review', 'reply_to_id', string='Replies')

    @api.constrains('rating')
    def _check_rating_range(self):
        for record in self:
            if record.rating and (record.rating < 0 or record.rating > 5):
                raise ValidationError("Rating must be between 0 and 5 stars.")

    @api.constrains('reply_to_id', 'partner_id')
    def _check_unique_reply(self):
        for record in self:
            if record.is_reply and record.reply_to_id and record.partner_id:
                count = self.search_count([
                    ('reply_to_id', '=', record.reply_to_id.id),
                    ('partner_id', '=', record.partner_id.id),
                    ('is_reply', '=', True),
                    ('id', '!=', record.id),
                ])
                if count:
                    raise ValidationError("You can only reply once per review.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            doc = self.env['documents.document'].sudo().browse(vals['document_id'])
            
            if hasattr(doc, 'owner_id') and doc.owner_id and vals.get('partner_id') == doc.owner_id.partner_id.id:
                raise ValidationError("Document owner can't review own document.")
            
            if vals.get('is_reply', False) and vals.get('reply_to_id'):
                parent = self.sudo().browse(vals['reply_to_id'])
                if parent and parent.partner_id and parent.partner_id.id == vals.get('partner_id'):
                    raise ValidationError("You can't reply to your own review.")
        
        return super().create(vals_list)