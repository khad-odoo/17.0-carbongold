/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";


export class DocumentReviewComponent extends Component {
    static template = "carbongold_document_management.DocumentReviewComponent";
    
    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        
        this.state = useState({
            reviews: [],
            showReviewForm: false,
            newReview: {
                comment: '',
                rating: 0,
                attachments: []
            },
            replyForms: {},
            loading: false,
            isLoggedIn: this.props.isLoggedIn || false,
            userHasReviewed: this.props.userHasReviewed || false,
            isDocumentOwner: this.props.isDocumentOwner || false
        });
        
        onWillStart(() => this.loadReviews());
    }
    
    get canWriteReview() {
        return this.state.isLoggedIn && !this.state.userHasReviewed && !this.state.isDocumentOwner;
    }
    
    get reviewButtonText() {
        if (this.state.userHasReviewed) {
            return _t("Edit Your Review");
        } else {
            return _t("Write a Review");
        }
    }
    
    get documentId() {
        return this.props.documentId;
    }
    
    get currentPartnerName() {
        return this.props.currentPartnerName || '';
    }
    
    async loadReviews() {
        if (!this.documentId) return;
        
        this.state.loading = true;
        try {
            const reviews = await this.rpc('/document/review/list/' + this.documentId);
            this.state.reviews = reviews;
        } catch (error) {
            this.notification.add(_t("Error loading reviews"), { type: "danger" });
        }
        this.state.loading = false;
    }
    
    toggleReviewForm() {
        if (!this.state.isLoggedIn) {
            window.location.href = '/web/login';
            return;
        }
        
        this.state.showReviewForm = !this.state.showReviewForm;
        if (this.state.showReviewForm) {
            this.state.newReview = { comment: '', rating: 0, attachments: [] };
        }
    }
    
    setRating(event) {
        const rating = parseInt(event.target.dataset.rating) || parseInt(event.currentTarget.dataset.rating);
        this.state.newReview.rating = rating;
    }

    onAttachmentButtonClick() {
        const fileInput = document.querySelector('.o_review_file_input');
        if (fileInput) {
            fileInput.click();
        }
    }

async onFileInputChange(event) {
    const files = event.target.files;
    if (!files.length) return;
    
    // Disable send button while uploading
    const sendButton = document.querySelector('.btn-primary');
    if (sendButton) sendButton.disabled = true;
    
    try {
        // Process all files
        const uploadPromises = Array.from(files).map(file => this._uploadAttachment(file));
        const results = await Promise.allSettled(uploadPromises);
        
        // Handle results
        results.forEach((result, index) => {
            if (result.status === 'fulfilled' && result.value) {
                result.value.state = 'pending';
                this.state.newReview.attachments.push(result.value);
            } else {
                const file = files[index];
                this.notification.add(
                    _t("Could not save file %s", file.name), 
                    { type: "warning", sticky: true }
                );
            }
        });
        
    } catch (error) {
        this.notification.add(_t("Error uploading files"), { type: "danger" });
    } finally {
        // Clear input and re-enable button
        event.target.value = null;
        if (sendButton) sendButton.disabled = false;
    }
}

async _uploadAttachment(file) {

    if (file.size > 5 * 1024 * 1024) {
        this.notification.add(
            _t("File %s is too large (max 5MB)", file.name), 
            { type: "warning" }
        );
        return null;
    }
    
    try {
        // Create FormData for the HTTP request
        const formData = new FormData();
        formData.append('name', file.name);
        formData.append('file', file);
        formData.append('res_model', 'document.review');
        formData.append('res_id', this.documentId);
        formData.append('access_token', ''); // No access token needed for authenticated users
        formData.append('csrf_token', this.props.csrfToken);
        
        // Use fetch for HTTP form upload (not RPC since it's type='http')
        const response = await fetch('/portal/attachment/add', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest', // Mark as AJAX request
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const attachment = await response.json();
        return attachment;
        
    } catch (error) {
        throw error;
    }
}

    // Updated submit method to handle attachment IDs properly
    async submitReview() {
        if (!this.state.isLoggedIn) {
            window.location.href = '/web/login';
            return;
        }
        
        if (this.state.isDocumentOwner) {
            this.notification.add(_t("Document owners cannot review their own documents"), { type: "warning" });
            return;
        }
        
        if (!this.state.newReview.rating) {
            this.notification.add(_t("Please select a rating"), { type: "warning" });
            return;
        }
        
        try {
            const result = await this.rpc('/document/review/submit', {
                document_id: this.documentId,
                comment: this.state.newReview.comment,
                rating: this.state.newReview.rating,
                // Send attachment IDs and access tokens for proper linking
                attachment_ids: this.state.newReview.attachments.map(a => a.id),
                attachment_tokens: this.state.newReview.attachments.map(a => a.access_token)
            });
            
            if (result.error) {
                this.notification.add(result.error, { type: "danger" });
            } else {
                this.notification.add(_t("Review submitted successfully!"), { type: "success" });
                this.state.showReviewForm = false;
                this.state.userHasReviewed = true;
                this.state.newReview = { comment: '', rating: 0, attachments: [] }; // Reset form
            }
        } catch (error) {
            this.notification.add(_t("Error submitting review"), { type: "danger" });
        }
    }

    
    removeAttachment(attachmentIndex) {
        this.state.newReview.attachments.splice(attachmentIndex, 1);
    }
    
    toggleReplyForm(reviewId) {
        if (!this.state.isLoggedIn) {
            window.location.href = '/web/login';
            return;
        }
        
        if (this.state.replyForms[reviewId]) {
            delete this.state.replyForms[reviewId];
        } else {
            this.state.replyForms[reviewId] = { comment: '' };
        }
    }
    
    async submitReply(reviewId) {
        if (!this.state.isLoggedIn) {
            window.location.href = '/web/login';
            return;
        }
        
        const reply = this.state.replyForms[reviewId];
        if (!reply || !reply.comment.trim()) {
            this.notification.add(_t("Please enter a reply"), { type: "warning" });
            return;
        }

        if (this.state.isDocumentOwner) {
        this.notification.add(_t("Document owners cannot reply to reviews"), { type: "warning" });
        return;
    }
    
        
        try {
            const result = await this.rpc('/document/review/reply', {
                review_id: reviewId,
                reply: reply.comment
            });
            
            if (result.error) {
                this.notification.add(result.error, { type: "danger" });
            } else {
                this.notification.add(_t("Reply submitted successfully!"), { type: "success" });
                delete this.state.replyForms[reviewId];
                // await this.loadReviews();
            }
        } catch (error) {
            this.notification.add(_t("Error submitting reply"), { type: "danger" });
        }
    }
    
    canReplyToReview(review) {
        if (!this.state.isLoggedIn) return false;
        if (review.author_name === this.currentPartnerName) return false;
        if (this.state.isDocumentOwner) return false;  

        // Check if user already replied to this review
        const userReplies = review.replies.filter(reply => 
            reply.author_name === this.currentPartnerName
        );
        
        return userReplies.length === 0; // Can reply only if not already replied
    }
}

registry.category("public_components").add("carbongold_document_management.document_review", DocumentReviewComponent);
