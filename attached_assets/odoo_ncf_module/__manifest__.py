# -*- coding: utf-8 -*-
{
    'name': 'OdooNCFs - Comprobantes Fiscales Dominicanos',
    'version': '17.0.1.0.0',
    'summary': 'Gestión de NCF, RNC y reportes fiscales 606/607 para República Dominicana',
    'description': '''
        Módulo completo para gestión de comprobantes fiscales dominicanos:
        - Tipos de comprobantes fiscales (NCF)
        - Integración con RNC
        - Gestión de secuencias NCF
        - Integración con facturas y POS
        - Generación de reportes 606 y 607 para DGII
        - Validaciones según normativas fiscales dominicanas
    ''',
    'category': 'Accounting/Localizations',
    'author': 'Four One Solutions',
    'website': 'https://fourone.com.do',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale'
    ],
    'data': [
        'security/fiscal_groups.xml',
        'security/ir.model.access.csv',
        'data/tipo_comprobante_data.xml',
        'views/tipo_comprobante_views.xml',
        'views/account_move_views.xml',
        'views/pos_order_views.xml',
        'views/res_partner_views.xml',
        'wizard/reporte_606_wizard_views.xml',
        'wizard/reporte_607_wizard_views.xml',
        'reports/external_layout.xml',
        'reports/invoice_report.xml',
    ],
    'demo': [],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
}
