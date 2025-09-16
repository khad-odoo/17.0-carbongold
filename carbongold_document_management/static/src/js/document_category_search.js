/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.DocumentCategorySearch = publicWidget.Widget.extend({
    selector: "#doc_category_form",
    events: {
        "change .doc-cat-checkbox": "_onCategoryChange",
    },
    _onCategoryChange: function () {
        this.el.submit();
    },
});
