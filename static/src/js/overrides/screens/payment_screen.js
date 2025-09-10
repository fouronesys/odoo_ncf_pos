/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { NCFPopup } from "../components/ncf_popup";
import { _t } from "@web/core/l10n/translation";

// Patch PaymentScreen to add NCF functionality
patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
    },

    async showNCFPopup() {
        const order = this.currentOrder;
        
        const { confirmed, payload } = await this.popup.add(NCFPopup, {
            title: _t('Información Fiscal NCF'),
            order: order,
        });

        if (confirmed && payload) {
            order.set_tipo_comprobante(payload.tipo_comprobante_id);
            order.set_ncf(payload.ncf);
            order.es_fiscal = payload.es_fiscal;
        }
    },

    async validateOrder(isForceValidate = false) {
        // Check if order requires NCF validation
        const order = this.currentOrder;
        
        // If no tipo_comprobante is selected, show popup
        if (!order.tipo_comprobante_id) {
            const { confirmed } = await this.showNCFPopup();
            if (!confirmed) {
                return false;
            }
        }

        // Validate fiscal requirements
        if (order.is_fiscal() && !order.get_ncf()) {
            this.popup.add(ErrorPopup, {
                title: _t('Error Fiscal'),
                body: _t('Se requiere NCF para comprobantes fiscales'),
            });
            return false;
        }

        return super.validateOrder(...arguments);
    }
});