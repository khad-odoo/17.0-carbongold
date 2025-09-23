/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { post } from "@web/core/network/http_service";
import { RPCError } from "@web/core/network/rpc_service";
import { escape } from "@web/core/utils/strings";
import { Picker, usePicker } from "../emoji/picker";
import { markEventHandled } from "@web/core/utils/misc";
import { useRef } from "@odoo/owl";

export class DocumentReviewComponent extends Component {
    static template = "carbongold_document_management.DocumentReviewComponent";
    static components = { Picker }

    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.emojiButton = useRef("emoji-button");
        this.picker = usePicker({
            buttons: [this.emojiButton],
            pickers: {
                emoji: (emoji) => this.addEmoji(emoji), // see next step
            },
            close: () => { }, 
            position: "top-end",
        });

        this.state = useState({
            reviews: this.props.reviews || [],
            showReviewForm: false,
            newReview: {
                comment: '',
                rating: 0,
                attachments: []
            },
            replyForms: {},
            loading: false,
            csrfToken: this.props.csrfToken,
            isLoggedIn: this.props.isLoggedIn || false,
            userHasReviewed: this.props.userHasReviewed || false,
            isDocumentOwner: this.props.isDocumentOwner || false
        });

        // onWillStart(() => this.loadReviews());
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

    addEmoji(emoji) {
        const comment = this.state.newReview.comment || "";
        this.state.newReview.comment = comment + emoji;
    }

    onClickAddEmoji(ev) {
        markEventHandled(ev, "Composer.onClickAddEmoji");
    }

    // async loadReviews() {
    //     if (!this.documentId) return;

    //     this.state.loading = true;
    //     try {
    //         const reviews = await this.rpc('/document/review/list/' + this.documentId);
    //         this.state.reviews = reviews;
    //     } catch (error) {
    //         this.notification.add(_t("Error loading reviews"), { type: "danger" });
    //     }
    //     this.state.loading = false;
    // }

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

        this.state.loading = true;

        try {
            await Promise.all([...files].map(file => this._uploadSingleFile(file)));
        } catch (error) {
            console.error('Upload error:', error);
        } finally {
            // Clear input and reset loading
            event.target.value = null;
            this.state.loading = false;
        }
    }

    async _uploadSingleFile(file) {
        const data = {
            name: file.name,
            file: file,
            res_model: 'document.review',
            res_id: 0, // Pending state
            csrf_token: this.state.csrfToken,
        };

        try {
            const attachment = await post('/review/attachment/add', data);

            if (attachment.error) {
                this.notification.add(
                    _t(attachment.error),
                    { type: 'warning', sticky: true }
                )
            }
            attachment.state = 'pending';
            this.state.newReview.attachments.push(attachment);
        } catch (error) {
            if (error instanceof RPCError) {
                this.notification.add(
                    _t("Could not save file <strong>%s</strong>", escape(file.name)),
                    { type: 'warning', sticky: true }
                );
            }
        }
    }

    async removeAttachment(attachmentIndex) {
        const attachment = this.state.newReview.attachments[attachmentIndex];
        if (!attachment) return;

        try {
            this.state.loading = true;
            await this.rpc('/review/attachment/remove', {
                attachment_id: attachment.id,
                access_token: attachment.access_token,
            });

            this.state.newReview.attachments.splice(attachmentIndex, 1);

        } catch (error) {
            console.error('Failed to remove attachment:', error);
            this.notification.add(
                _t("Could not remove attachment %s", attachment.name),
                { type: "warning" }
            );
        } finally {
            this.state.loading = false;
        }
    }


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
                comment: this.state.newReview.comment || '',
                rating: this.state.newReview.rating,
                attachment_ids: this.state.newReview.attachments.map(a => a.id),
                attachment_tokens: this.state.newReview.attachments.map(a => a.access_token),
            });

            if (result.error) {
                this.notification.add(result.error, { type: "danger" });
            }
            this.notification.add(_t("Review submitted successfully!"), { type: "success" });
            this.state.showReviewForm = false;
            this.state.userHasReviewed = true;
            this.state.newReview = { comment: '', rating: 0, attachments: [] };
        } catch (error) {
            console.error('Error submitting review:', error);
            this.notification.add(_t("Error submitting review"), { type: "danger" });
        }
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

    getFileIcon(mimetype, filename = '') {
        // Keep your existing file icon logic
        if (mimetype.startsWith('video/') || /\.(mp4|avi|mov|wmv|flv|webm|mkv)$/i.test(filename)) {
            return 'fa-file-video-o';
        }
        if (mimetype.startsWith('audio/') || /\.(mp3|wav|ogg|m4a|aac|flac)$/i.test(filename)) {
            return 'fa-file-audio-o';
        }
        if (mimetype.startsWith('image/') || /\.(jpg|jpeg|png|gif|bmp|svg|webp)$/i.test(filename)) {
            return 'fa-file-image-o';
        }
        if (mimetype === 'application/pdf' || filename.toLowerCase().endsWith('.pdf')) {
            return 'fa-file-pdf-o';
        }
        if (mimetype.includes('word') || mimetype.includes('officedocument.wordprocessingml') ||
            /\.(doc|docx)$/i.test(filename)) {
            return 'fa-file-word-o';
        }
        if (mimetype.includes('excel') || mimetype.includes('spreadsheetml') ||
            /\.(xls|xlsx)$/i.test(filename)) {
            return 'fa-file-excel-o';
        }
        if (mimetype.includes('powerpoint') || mimetype.includes('presentationml') ||
            /\.(ppt|pptx)$/i.test(filename)) {
            return 'fa-file-powerpoint-o';
        }
        if (mimetype.startsWith('text/') || /\.(txt|rtf)$/i.test(filename)) {
            return 'fa-file-text-o';
        }
        if (/\.(zip|rar|7z|tar|gz)$/i.test(filename)) {
            return 'fa-file-archive-o';
        }
        if (/\.(js|css|html|php|py|java|cpp|c)$/i.test(filename)) {
            return 'fa-file-code-o';
        }
        return 'fa-file-o';
    }

}

registry.category("public_components").add("carbongold_document_management.document_review", DocumentReviewComponent);
