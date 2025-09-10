{
    'name': 'POS NCF Integration',
    'version': '1.0',
    'summary': 'Agrega selección de tipo de comprobante y NCF en POS Restaurant',
    'description': 'Permite elegir tipo de comprobante fiscal y generar NCF usando secuencias del módulo odoo_ncf_module',
    'category': 'Point of Sale',
    'author': 'Four One Solutions',
    'website': 'https://fourone.com.do',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'odoo_ncf_module'],
    'data': [
        'views/pos_order_views.xml',
        'views/templates.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'odoo_ncf_pos/static/src/js/pos_ncf.js',
        ],
        'web.assets_qweb': [
            'odoo_ncf_pos/static/src/xml/pos_ncf_templates.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
