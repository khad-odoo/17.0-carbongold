/** @odoo-module **/

import { DocumentsSearchModel } from "@documents/views/search/documents_search_model";
import { patch } from '@web/core/utils/patch';

const isCategoryFilter = (s) => s.type === "filter" && s.fieldName === "document_category_ids";


patch(DocumentsSearchModel.prototype, {
    /**
     * @returns {Object[]}
     */
    getCategories() {
        const { values } = this.getSections(isCategoryFilter)[0];
        return [...values.values()].sort((a, b) => {
            if (a.group_sequence === b.group_sequence) {
                return a.sequence - b.sequence;
            } else {
                return a.group_sequence - b.group_sequence;
            }
        });
    },

    /**
     * Updates the tag ids of a record matching the given value.
     * @param {number[]} recordIds
     * @param {number} valueId
     * @param {number} x2mCommand command (4 to add a tag, 3 to remove it)
     */
    async updateRecordCategoryId(recordIds, valueId, x2mCommand = 4) {
        await this.orm.write("documents.document", recordIds, {
            document_category_ids: [[x2mCommand, valueId]],
        });
        this.skipLoadClosePreview = true;
        this.trigger("update");
        await this._reloadSections();  // update the tag count
    }
});
