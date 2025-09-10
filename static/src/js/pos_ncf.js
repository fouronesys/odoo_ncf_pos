odoo.define('odoo_ncf_pos.pos_ncf', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class NCFPopup extends PosComponent {
        confirm() {
            const order = this.env.pos.get_order();
            const tipo_id = this.el.querySelector('[name="tipo_comprobante_id"]').value;
            const ncf_val = this.el.querySelector('[name="ncf"]').value;
            order.tipo_comprobante_id = parseInt(tipo_id);
            order.ncf = ncf_val;
            this.trigger('close-popup');
        }
    }

    NCFPopup.template = 'pos_ncf_popup';
    Registries.Component.add(NCFPopup);

    return NCFPopup;
});
