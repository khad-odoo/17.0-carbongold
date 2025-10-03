/** @odoo-module **/

import {Component, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";

export class CategorySelector extends Component {
    static template = "carbongold_document_management.categorySelector";

    setup() {
        this.state = useState({
            selectedCategories: [],
            allCategories: this.props.all_cat_ids || [],
        });
    }

    onSelectChange(ev) {
        const selectedId = parseInt(ev.target.value);
        if (!selectedId || selectedId === 0) return;
        const cat = this.state.allCategories.find((t) => t.id === selectedId);
        if (cat && !this.state.selectedCategories.some((t) => t.id === cat.id)) {
            this.state.selectedCategories.push(cat);
        }
        ev.target.value = "0";
    }

    removeCategory(catId) {
        this.state.selectedCategories = this.state.selectedCategories.filter((t) => t.id !== catId);
    }

    getCategoriesAsJSON() {
        return JSON.stringify(this.state.selectedCategories.map((t) => t.id));
    }
}

registry.category("public_components").add("category_component", CategorySelector);
