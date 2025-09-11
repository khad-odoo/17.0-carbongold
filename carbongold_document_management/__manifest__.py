# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "CarbonGold Document Management",
    "version": "17.0.1.0.0",
    "category": "Custome",
    "summary": "CarbonGold Document Management",
    "description": """
CarbonGold Document Management | TaskID: 5066289
================================================
The Goal of this module is enhance the show and upload
Document feature on portal side.
""",
    "depends": ["documents", "website_sale","website_documents"],
    "data": [
        "security/ir.model.access.csv",
        "data/website_data.xml",
        "views/documents_document.xml",
        "views/document_template_views.xml",
        "views/category_category_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "carbongold_document_management/static/src/js/**",
        ],
    },
    "installable": True,
    "license": "OEEL-1",
}
