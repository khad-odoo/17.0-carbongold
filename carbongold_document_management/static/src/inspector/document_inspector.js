/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { DocumentsInspector } from "@documents/views/inspector/documents_inspector";
import { patch } from '@web/core/utils/patch';


patch(DocumentsInspector.prototype, {
    getCommonCategories() {
        const searchModelTags = this.env.searchModel.getCategories().reduce((res, cat) => {
            res[cat.id] = cat;
            return res;
        }, {});
        return this._getCommonM2M("document_category_ids")
            .filter((rec) => searchModelTags[rec.resId])
            .map((rec) => {
                const cat = searchModelTags[rec.resId];
                return {
                    id: rec.resId,
                    name: cat.display_name,
                };
            });
    },

    getAdditionalCategories(commonCategories) {
        return this.env.searchModel.getCategories().filter((tag) => {
            return !commonCategories.find((cTag) => cTag.id === tag.id);
        });
    },

    async addCategory(category, { input }) {
        const resIds = this.props.documents.map((r) => r.resId);
        await this.env.searchModel.updateRecordCategoryId(resIds, category.value);
        input.focus();
    },

    getCategoryAutocompleteProps(additionalCategories) {
        return {
            value: "",
            onSelect: this.addCategory.bind(this),
            sources: [
                {
                    options: (request) => {
                        request = request.toLowerCase();
                        return additionalCategories
                            .filter((tag) =>
                                (tag.display_name)
                                    .toLowerCase()
                                    .includes(request)
                            )
                            .map((tag) => {
                                return {
                                    id: tag.id,
                                    value: tag.id,
                                    label: tag.display_name,
                                };
                            });
                    },
                },
            ],
            placeholder: _t(" + Add a Category"),
        };
    },

    async removeCategory(category) {
        const resIds = this.props.documents.map((r) => r.resId);
        await this.env.searchModel.updateRecordCategoryId(resIds, category.id, 3);
    }
});
