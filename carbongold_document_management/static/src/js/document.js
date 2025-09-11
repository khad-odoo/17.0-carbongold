/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";

const MAX_FILE_SIZE_MB = 5;

publicWidget.registry.WebsiteDocument = publicWidget.Widget.extend({
    selector: ".website-document",

    events: {
        "change .document-att-type": "_onChangeAttachmentType",
        "click .saveDocumentBtn": "_onSaveDocument",
    },

    init() {
        this.notification = this.bindService("notification");
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

        const name = this.el.querySelector("input[name='name']").value;
        const author = this.el.querySelector("input[name='author']").value;
        const description = this.el.querySelector("textarea[name='description']").value;
        const attachmentType = this.el.querySelector("select[name='attachment_type']").value;
        const category = this.el.querySelector("select[name='category']").value;
        const fileInput = this.el.querySelector("input[name='document_file']");
        const link = this.el.querySelector("input[name='document_link']").value.trim();

        const file = fileInput.files[0];
        // Validation
        if (!name || !author || !description) {
            this.notification.add(_t("Please enter all details."), { type: "warning" });
            return;
        }
        if (!category) {
            this.notification.add(_t("Please select a document category."), { type: "warning" });
            return;
        }
        if (attachmentType === "file") {
            if (!file) {
                this.notification.add(_t("Please select a file to upload."), { type: "warning" });
                return;
            }
            // Validate size
            const maxSizeBytes = MAX_FILE_SIZE_MB * 1024 * 1024;
            if (file.size > maxSizeBytes) {
                this.notification.add(_t(`File size must not exceed ${MAX_FILE_SIZE_MB} MB.`), { type: "danger" });
                return;
            }
        }
        if (attachmentType === "link" && !link) {
            this.notification.add(_t("Please enter a valid document link."), { type: "warning" });
            return;
        }

        const formData = new FormData();
        formData.append("name", name);
        formData.append("author", author);
        formData.append("description", description);
        formData.append("attachment_type", attachmentType);
        formData.append("category", category);
        if (file) {
            formData.append("document_file", file);
        }
        else if (link) {
            formData.append("document_link", link);
        }

        try {
            const response = await fetch("/document/save_document", {
                method: "POST",
                body: formData,
            });
            const result = await response.json();

            if (result) {
                this.notification.add(_t("Document uploaded successfully!"), { type: "success" });

                const modal = document.getElementById("getDocumentModal");
                if (modal) modal.classList.remove("show");

                this._resetForm();
            } else {
                this.notification.add(result.error || _t("Document was not uploaded."), { type: "danger" });
            }
        } catch (error) {
            this.notification.add(_t("An error occurred while uploading."), { type: "danger" });
        }
    },

    _resetForm() {
        this.el.querySelector("input[name='name']").value = "";
        this.el.querySelector("input[name='author']").value = "";
        this.el.querySelector("textarea[name='description']").value = "";
        this.el.querySelector("select[name='attachment_type']").value = "file";
        this.el.querySelector("input[name='document_file']").value = "";
        this.el.querySelector("input[name='document_link']").value = "";
    }
});
