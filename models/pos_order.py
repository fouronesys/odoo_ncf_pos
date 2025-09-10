# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    tipo_comprobante_id = fields.Many2one(
        'tipo.comprobante',
        string='Tipo de Comprobante',
        help='Tipo de comprobante fiscal según DGII'
    )
    ncf = fields.Char(
        string='NCF', 
        size=11,
        help='Número de Comprobante Fiscal generado'
    )
    es_fiscal = fields.Boolean(
        string='Es Fiscal',
        related='tipo_comprobante_id.es_fiscal',
        store=True,
        help='Indica si la orden requiere NCF'
    )
    ncf_generado_automaticamente = fields.Boolean(
        string='NCF Generado Automáticamente',
        default=False,
        help='Indica si el NCF fue generado automáticamente'
    )

    @api.depends('tipo_comprobante_id')
    def _compute_es_fiscal(self):
        """Computa si la orden es fiscal basado en el tipo de comprobante"""
        for order in self:
            order.es_fiscal = order.tipo_comprobante_id.es_fiscal if order.tipo_comprobante_id else False

    @api.onchange('tipo_comprobante_id')
    def _onchange_tipo_comprobante(self):
        """Limpia el NCF cuando cambia el tipo de comprobante"""
        if self.tipo_comprobante_id:
            if not self.tipo_comprobante_id.es_fiscal:
                self.ncf = False
            self.es_fiscal = self.tipo_comprobante_id.es_fiscal
        else:
            self.ncf = False
            self.es_fiscal = False

    @api.constrains('tipo_comprobante_id', 'ncf')
    def _check_ncf_required(self):
        """Valida que se asigne NCF para comprobantes fiscales"""
        for order in self:
            if order.es_fiscal and order.state not in ['draft', 'cancel'] and not order.ncf:
                raise ValidationError(
                    _('Se requiere NCF para el comprobante fiscal de la orden %s') % order.name
                )

    @api.constrains('ncf')
    def _check_ncf_format(self):
        """Valida el formato del NCF"""
        for order in self:
            if order.ncf:
                if len(order.ncf) != 11:
                    raise ValidationError(
                        _('El NCF debe tener exactamente 11 caracteres')
                    )
                if not order.ncf.isalnum():
                    raise ValidationError(
                        _('El NCF solo puede contener letras y números')
                    )

    @api.constrains('ncf', 'company_id')
    def _check_ncf_unique(self):
        """Valida que el NCF sea único por empresa"""
        for order in self:
            if order.ncf:
                existing = self.search([
                    ('ncf', '=', order.ncf),
                    ('company_id', '=', order.company_id.id),
                    ('id', '!=', order.id)
                ])
                if existing:
                    raise ValidationError(
                        _('El NCF %s ya está asignado a la orden %s') % (order.ncf, existing[0].name)
                    )

    def action_assign_ncf(self):
        """Asigna NCF a las órdenes fiscales"""
        for order in self:
            if order.tipo_comprobante_id and order.tipo_comprobante_id.es_fiscal:
                if order.ncf:
                    _logger.info(f'La orden {order.name} ya tiene NCF asignado: {order.ncf}')
                    continue
                
                try:
                    seq = self.env['ncf.sequence'].get_active_sequence_for_type(
                        order.tipo_comprobante_id.id,
                        order.company_id.id
                    )
                    ncf_val = seq.get_next_ncf()
                    order.write({
                        'ncf': ncf_val,
                        'ncf_generado_automaticamente': True
                    })
                    order.message_post(
                        body=_('NCF asignado automáticamente: %s') % ncf_val,
                        message_type='notification'
                    )
                    _logger.info(f'NCF {ncf_val} asignado a la orden {order.name}')
                    
                except Exception as e:
                    _logger.error(f'Error al generar NCF para orden {order.name}: {str(e)}')
                    raise UserError(
                        _('Error al generar NCF para la orden %s: %s') % (order.name, str(e))
                    )

    @api.model
    def generate_ncf_for_pos(self, tipo_comprobante_id):
        """Método llamado desde JavaScript para generar NCF"""
        try:
            if not tipo_comprobante_id:
                raise ValidationError(_('Debe seleccionar un tipo de comprobante'))
            
            tipo_comprobante = self.env['tipo.comprobante'].browse(tipo_comprobante_id)
            if not tipo_comprobante.exists():
                raise ValidationError(_('Tipo de comprobante no encontrado'))
            
            if not tipo_comprobante.es_fiscal:
                return {'ncf': '', 'es_fiscal': False}
            
            seq = self.env['ncf.sequence'].get_active_sequence_for_type(
                tipo_comprobante_id,
                self.env.company.id
            )
            ncf_val = seq.get_next_ncf()
            
            return {
                'ncf': ncf_val,
                'es_fiscal': True,
                'success': True,
                'message': _('NCF generado exitosamente')
            }
            
        except Exception as e:
            _logger.error(f'Error en generate_ncf_for_pos: {str(e)}')
            return {
                'ncf': '',
                'es_fiscal': False,
                'success': False,
                'error': str(e)
            }

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Agrega campos NCF a los datos del POS"""
        fields = super()._load_pos_data_fields(config_id)
        fields.extend(['tipo_comprobante_id', 'ncf', 'es_fiscal'])
        return fields

    def _export_for_ui(self, order):
        """Exporta datos de la orden para la interfaz POS"""
        result = super()._export_for_ui(order)
        result.update({
            'tipo_comprobante_id': order.tipo_comprobante_id.id if order.tipo_comprobante_id else None,
            'ncf': order.ncf or '',
            'es_fiscal': order.es_fiscal,
        })
        return result

    def _prepare_invoice_vals(self):
        """Prepara valores para la factura incluyendo datos NCF"""
        vals = super()._prepare_invoice_vals()
        if self.tipo_comprobante_id:
            vals.update({
                'tipo_comprobante_id': self.tipo_comprobante_id.id,
                'ncf': self.ncf,
            })
        return vals

    @api.model
    def _order_fields(self, ui_order):
        """Extiende los campos de la orden con datos NCF"""
        fields = super()._order_fields(ui_order)
        fields.update({
            'tipo_comprobante_id': ui_order.get('tipo_comprobante_id'),
            'ncf': ui_order.get('ncf', ''),
            'es_fiscal': ui_order.get('es_fiscal', False),
        })
        return fields

    def write(self, vals):
        """Override write para validaciones adicionales"""
        # Auto-asignar NCF si se cambia a un tipo fiscal
        if 'tipo_comprobante_id' in vals:
            for order in self:
                if vals['tipo_comprobante_id']:
                    tipo = self.env['tipo.comprobante'].browse(vals['tipo_comprobante_id'])
                    if tipo.es_fiscal and not order.ncf and 'ncf' not in vals:
                        # Auto-generar NCF si no se especifica uno
                        try:
                            seq = self.env['ncf.sequence'].get_active_sequence_for_type(
                                tipo.id, order.company_id.id
                            )
                            vals['ncf'] = seq.get_next_ncf()
                            vals['ncf_generado_automaticamente'] = True
                        except Exception as e:
                            _logger.warning(f'No se pudo auto-generar NCF: {str(e)}')
        
        return super().write(vals)
