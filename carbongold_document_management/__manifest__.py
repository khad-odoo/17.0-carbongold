# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Bitons Document Plus",
    "version": "17.0.1.0.0",
    "category": "Custome",
    "summary": "Bitons Document Plus",
    "description": """
Bitons Document Plus | TaskID: 5066289
================================================
Overview: Document Plus module extends the Odoo Document addon to enhance document management and 
presentation on the website. It enables administrators to easily publish and organize documents 
for public download, with improved control over display and user interaction.

Key Features:

Thumbnail Management: Generate, customize, and manage document thumbnails for improved visual presentation.
Website Integration: Easily embed documents into any webpage using the drag-and-drop Document+ block in the Odoo Website Editor.
Document Management Tools:
 - Rating and review system
 - Comment functionality
 - Categorization and tagging

Reporting & Analytics: Track document performance, downloads, and user engagement with built-in reports.

Benefits:
 - Streamlined document publishing with customizable thumbnails.
 - Enhanced user experience through interactive features.
 - Better insights into document usage and popularity.
""",

    "depends": ["website_documents"],
    "data": [
        "security/ir.model.access.csv",
        "data/website_data.xml",
        "views/documents_document.xml",
        "views/document_review_views.xml",
        "views/document_template_views.xml",
        "views/category_category_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "carbongold_document_management/static/src/js/**",
            "carbongold_document_management/static/src/xml/**",
            "carbongold_document_management/static/src/scss/**",
        ],
    },
    "installable": True,
    "license": "OEEL-1",
}
