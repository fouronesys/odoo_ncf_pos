from odoo import models, fields, api, _

class PosOrder(models.Model):
    _inherit = 'pos.order'

    tipo_comprobante_id = fields.Many2one(
        'tipo.comprobante',
        string='Tipo de Comprobante'
    )
    ncf = fields.Char(string='NCF', size=11)
    es_fiscal = fields.Boolean(
        string='Es Fiscal',
        related='tipo_comprobante_id.es_fiscal',
        store=True
    )

    def action_assign_ncf(self):
        for order in self:
            if order.tipo_comprobante_id and order.tipo_comprobante_id.es_fiscal:
                seq = self.env['ncf.sequence'].get_active_sequence_for_type(
                    order.tipo_comprobante_id.id,
                    order.company_id.id
                )
                ncf_val = seq.get_next_ncf()
                order.ncf = ncf_val
                order.message_post(body=_('NCF asignado: %s') % ncf_val)
