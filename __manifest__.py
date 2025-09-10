# -*- coding: utf-8 -*-
{
    'name': 'POS NCF Integration',
    'version': '17.0.1.0.0',
    'summary': 'Integración de NCF en POS para República Dominicana',
    'description': '''
        Módulo de integración NCF para Point of Sale:
        - Selección de tipo de comprobante fiscal en POS
        - Generación automática de NCF
        - Integración completa con odoo_ncf_module
        - Compatible con Odoo 17 y framework OWL
        - Validaciones fiscales en tiempo real
    ''',
    'category': 'Point of Sale',
    'author': 'Four One Solutions',
    'website': 'https://fourone.com.do',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'odoo_ncf_module'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_order_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'odoo_ncf_pos/static/src/js/models/*.js',
            'odoo_ncf_pos/static/src/js/overrides/**/*.js',
            'odoo_ncf_pos/static/src/xml/*.xml',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
