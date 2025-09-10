/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/store/models";

// Extend POS Order model to support NCF functionality
patch(Order.prototype, {
    constructor() {
        super(...arguments);
        this.tipo_comprobante_id = null;
        this.ncf = null;
        this.es_fiscal = false;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.tipo_comprobante_id = json.tipo_comprobante_id || null;
        this.ncf = json.ncf || null;
        this.es_fiscal = json.es_fiscal || false;
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.tipo_comprobante_id = this.tipo_comprobante_id;
        json.ncf = this.ncf;
        json.es_fiscal = this.es_fiscal;
        return json;
    },

    set_tipo_comprobante(tipo_comprobante_id) {
        this.tipo_comprobante_id = tipo_comprobante_id;
        // Update fiscal status based on tipo_comprobante
        const tipo_comprobante = this.pos.db.get_tipo_comprobante_by_id(tipo_comprobante_id);
        if (tipo_comprobante) {
            this.es_fiscal = tipo_comprobante.es_fiscal;
            if (this.es_fiscal && !this.ncf) {
                // Auto-generate NCF if fiscal
                this.generate_ncf();
            }
        }
    },

    get_tipo_comprobante() {
        if (this.tipo_comprobante_id) {
            return this.pos.db.get_tipo_comprobante_by_id(this.tipo_comprobante_id);
        }
        return null;
    },

    set_ncf(ncf) {
        this.ncf = ncf;
    },

    get_ncf() {
        return this.ncf || '';
    },

    is_fiscal() {
        return this.es_fiscal || false;
    },

    async generate_ncf() {
        if (!this.tipo_comprobante_id) {
            return;
        }

        try {
            const result = await this.env.services.rpc({
                model: 'pos.order',
                method: 'generate_ncf_for_pos',
                args: [[], this.tipo_comprobante_id],
                context: this.pos.user.context,
            });
            
            if (result && result.ncf) {
                this.ncf = result.ncf;
                this.trigger('change', this);
            }
        } catch (error) {
            console.error('Error generating NCF:', error);
            this.env.services.notification.add(
                `Error al generar NCF: ${error.message}`,
                { type: 'danger' }
            );
        }
    },

    // Override finalize to ensure NCF is assigned
    finalize() {
        if (this.is_fiscal() && !this.ncf) {
            throw new Error('Se requiere NCF para comprobantes fiscales');
        }
        return super.finalize(...arguments);
    }
});