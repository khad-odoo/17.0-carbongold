/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.DocumentCategoryFilter = publicWidget.Widget.extend({
    selector: ".carbon_category_list",
    events: {
        "change .parent-cat": "_onParentChange",
    },

    _onParentChange: function (ev) {
        var $parent = $(ev.currentTarget);
        var parentId = $parent.data("parent-id");
        var isChecked = $parent.is(":checked");
        this.$el
            .find('.child-cat[data-parent-id="' + parentId + '"]')
            .prop("checked", isChecked)
            .trigger("change");
    },
});
