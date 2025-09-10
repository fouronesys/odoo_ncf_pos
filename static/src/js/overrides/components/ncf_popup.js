/** @odoo-module */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

export class NCFPopup extends AbstractAwaitablePopup {
    static template = "odoo_ncf_pos.NCFPopup";
    static defaultProps = {
        confirmText: _t("Confirmar"),
        cancelText: _t("Cancelar"),
        title: _t("Información Fiscal NCF"),
        body: "",
    };

    setup() {
        super.setup();
        this.state = useState({
            tipo_comprobante_id: this.props.order?.tipo_comprobante_id || null,
            ncf: this.props.order?.ncf || '',
            auto_generate: true,
        });
        
        this.tipos_comprobante = this.env.pos.db.get_tipos_comprobante() || [];
    }

    get selectedTipoComprobante() {
        if (this.state.tipo_comprobante_id) {
            return this.tipos_comprobante.find(t => t.id === this.state.tipo_comprobante_id);
        }
        return null;
    }

    get showNCFField() {
        const tipo = this.selectedTipoComprobante;
        return tipo && tipo.es_fiscal;
    }

    onTipoComprobanteChange(ev) {
        const tipo_id = parseInt(ev.target.value);
        this.state.tipo_comprobante_id = tipo_id;
        
        // Auto-generate NCF if fiscal type is selected
        if (this.state.auto_generate && this.selectedTipoComprobante?.es_fiscal) {
            this.generateNCF();
        } else if (!this.selectedTipoComprobante?.es_fiscal) {
            this.state.ncf = '';
        }
    }

    onNCFChange(ev) {
        this.state.ncf = ev.target.value;
    }

    onAutoGenerateChange(ev) {
        this.state.auto_generate = ev.target.checked;
        if (this.state.auto_generate && this.selectedTipoComprobante?.es_fiscal) {
            this.generateNCF();
        }
    }

    async generateNCF() {
        if (!this.state.tipo_comprobante_id) {
            return;
        }

        try {
            const result = await this.env.services.rpc({
                model: 'pos.order',
                method: 'generate_ncf_for_pos',
                args: [[], this.state.tipo_comprobante_id],
                context: this.env.pos.user.context,
            });
            
            if (result && result.ncf) {
                this.state.ncf = result.ncf;
            }
        } catch (error) {
            console.error('Error generating NCF:', error);
            this.env.services.notification.add(
                _t('Error al generar NCF: %s', error.message),
                { type: 'danger' }
            );
        }
    }

    async confirm() {
        if (this.selectedTipoComprobante?.es_fiscal && !this.state.ncf) {
            this.env.services.notification.add(
                _t('Se requiere NCF para comprobantes fiscales'),
                { type: 'danger' }
            );
            return;
        }

        this.props.resolve({
            confirmed: true,
            payload: {
                tipo_comprobante_id: this.state.tipo_comprobante_id,
                ncf: this.state.ncf,
                es_fiscal: this.selectedTipoComprobante?.es_fiscal || false,
            }
        });
    }

    cancel() {
        this.props.resolve({ confirmed: false });
    }
}