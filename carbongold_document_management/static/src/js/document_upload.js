/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import {_t} from "@web/core/l10n/translation";

const MAX_FILE_SIZE_MB = 63;

publicWidget.registry.WebsiteDocument = publicWidget.Widget.extend({
    selector: ".website-document",

    events: {
        "change .document-att-type": "_onChangeAttachmentType",
        "click .saveDocumentBtn": "_onSaveDocument",
    },

    _onChangeAttachmentType(ev) {
        ev.preventDefault();
        const value = ev.target.value;
        const fileInput = this.el.querySelector("input[name='document_file']");
        const linkInput = this.el.querySelector("input[name='document_link']");

        if (value === "file") {
            fileInput.classList.remove("d-none");
            linkInput.classList.add("d-none");
        } else {
            fileInput.classList.add("d-none");
            linkInput.classList.remove("d-none");
        }
    },

    async _onSaveDocument(ev) {
        ev.preventDefault();

        const modal = document.getElementById("getDocumentModal");
        const messageBox = modal.querySelector(".validation-message");
        // Helper to show error in alert box
        const showError = (message) => {
            messageBox.textContent = _t(message);
            messageBox.classList.remove("d-none");
        };

        // Helper to clear error
        const clearError = () => {
            messageBox.textContent = "";
            messageBox.classList.add("d-none");
        };

        const name = this.el.querySelector("input[name='name']").value;
        const author = this.el.querySelector("input[name='author']").value;
        const description = this.el.querySelector("textarea[name='description']").value;
        const attachmentType = this.el.querySelector("select[name='attachment_type']").value;
        const category = this.el.querySelector("select[name='category']").value;
        const fileInput = this.el.querySelector("input[name='document_file']");
        const link = this.el.querySelector("input[name='document_link']").value.trim();
        const DocumentMessageBox = document.querySelector(".document-alert");
        const DocumentMessage = document.querySelector(".o_document_alert_msg");

        const showAlert = (message, alertClass) => {
            DocumentMessageBox.classList.remove("d-none");
            DocumentMessageBox.classList.add(alertClass);
            DocumentMessage.textContent = _t(message);
        };

        const file = fileInput.files[0];
        clearError();

        if (!name) return showError("Please enter the name of the document.");
        if (!category) return showError("Please select a document category.");
        if (attachmentType === "file") {
            if (!file) return showError("Please select a file to upload.");
            const maxSizeBytes = MAX_FILE_SIZE_MB * 1024 * 1024;
            if (file.size > maxSizeBytes) {
                return showError(`File size must not exceed ${MAX_FILE_SIZE_MB} MB.`);
            }
        }
        if (attachmentType === "link" && !link) {
            return showError("Please provide a valid document link.");
        }

        const formData = new FormData();
        formData.append("name", name);
        formData.append("author", author);
        formData.append("description", description);
        formData.append("attachment_type", attachmentType);
        formData.append("category", category);
        if (file) {
            formData.append("document_file", file);
        } else if (link) {
            formData.append("document_link", link);
        }

        try {
            const response = await fetch("/document/save_document", {
                method: "POST",
                body: formData,
            });
            const result = await response.json();

            if (result) {
                if (modal) modal.classList.remove("show");
                this._resetForm();
                showAlert("Your document uploaded successfully!", "alert-success");
            } else {
                showAlert("Document was not uploaded.", "alert-danger");
            }
        } catch (error) {
            showAlert("An error occurred while uploading.", "alert-danger");
        }
    },

    _resetForm() {
        this.el.querySelector("input[name='name']").value = "";
        this.el.querySelector("input[name='author']").value = "";
        this.el.querySelector("textarea[name='description']").value = "";
        this.el.querySelector("input[name='document_file']").value = "";
        this.el.querySelector("input[name='document_link']").value = "";
    },
});
