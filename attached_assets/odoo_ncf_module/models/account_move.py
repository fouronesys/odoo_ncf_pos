# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class AccountMove(models.Model):
    _inherit = 'account.move'

    tipo_comprobante_id = fields.Many2one(
        'tipo.comprobante',
        string='Tipo de Comprobante',
        help='Tipo de comprobante fiscal'
    )
    ncf = fields.Char(
        string='NCF',
        size=11,
        help='Número de Comprobante Fiscal (asignado automáticamente)'
    )
    ncf_modificado = fields.Char(
        string='NCF Modificado',
        size=11,
        help='NCF del documento que modifica (para notas de crédito/débito)'
    )
    es_fiscal = fields.Boolean(
        string='Es Fiscal',
        related='tipo_comprobante_id.es_fiscal',
        store=True,
        help='Indica si la factura es fiscal'
    )
    anulado = fields.Boolean(
        string='Anulado',
        default=False,
        help='Indica si el comprobante fue anulado'
    )
    fecha_anulacion = fields.Datetime(
        string='Fecha Anulación',
        help='Fecha y hora de anulación del comprobante'
    )
    motivo_anulacion = fields.Text(
        string='Motivo Anulación',
        help='Motivo de la anulación del comprobante'
    )
    rnc = fields.Char(
        string='RNC/Cédula',
        size=20,
        help='RNC o Cédula del cliente en la factura'
    )
    tipo_rnc = fields.Selection([
        ('rnc', 'RNC'),
        ('cedula', 'Cédula'),
        ('pasaporte', 'Pasaporte'),
    ], string='Tipo de Documento', 
       help='Tipo de documento de identificación del cliente')
    es_contribuyente = fields.Boolean(
        string='Es Contribuyente',
        help='Indica si el cliente es contribuyente registrado'
    )
    ncf_sequence_id = fields.Many2one(
        'ncf.sequence',
        string='Secuencia NCF Utilizada',
        help='Secuencia utilizada para generar el NCF',
        readonly=True
    )
    requiere_ncf = fields.Boolean(
        string='Requiere NCF',
        compute='_compute_requiere_ncf',
        store=True,
        help='Indica si esta factura debe tener NCF'
    )
    alerta_ncf = fields.Text(
        string='Alertas NCF',
        compute='_compute_alertas_ncf',
        help='Alertas relacionadas con secuencias NCF'
    )
    es_factura_fiscal = fields.Boolean(
        string='Es Factura Fiscal',
        compute='_compute_es_factura_fiscal',
        store=True
    )

    @api.depends('move_type', 'tipo_comprobante_id')
    def _compute_requiere_ncf(self):
        """Determina si la factura requiere NCF basado en el tipo de movimiento y comprobante"""
        for record in self:
            # Solo facturas de venta con tipo de comprobante fiscal requieren NCF
            record.requiere_ncf = (
                record.move_type in ['out_invoice', 'out_refund'] and
                record.tipo_comprobante_id and
                record.tipo_comprobante_id.es_fiscal
            )
    
    @api.depends('tipo_comprobante_id', 'move_type')
    def _compute_es_factura_fiscal(self):
        """Determina si es una factura fiscal"""
        for record in self:
            record.es_factura_fiscal = (
                record.move_type in ['out_invoice', 'out_refund'] and
                record.tipo_comprobante_id and
                record.tipo_comprobante_id.es_fiscal
            )
    
    @api.depends('tipo_comprobante_id', 'company_id')
    def _compute_alertas_ncf(self):
        """Calcula alertas relacionadas con NCF"""
        for record in self:
            if record.tipo_comprobante_id and record.es_factura_fiscal:
                try:
                    sequence = self.env['ncf.sequence'].get_active_sequence_for_type(
                        record.tipo_comprobante_id.id, 
                        record.company_id.id
                    )
                    record.alerta_ncf = sequence.get_alert_message()
                except ValidationError:
                    record.alerta_ncf = '❌ No hay secuencia NCF configurada para este tipo de comprobante'
            else:
                record.alerta_ncf = ''
    
    @api.onchange('partner_id', 'move_type')
    def _onchange_partner_tipo_comprobante(self):
        """Sugiere tipo de comprobante basado en el cliente y tipo de factura"""
        if self.partner_id and self.move_type in ['out_invoice', 'out_refund']:
            # Copiar información del partner a la factura
            if hasattr(self.partner_id, 'rnc') and self.partner_id.rnc:
                self.rnc = self.partner_id.rnc
                self.tipo_rnc = getattr(self.partner_id, 'tipo_rnc', 'rnc')
                self.es_contribuyente = getattr(self.partner_id, 'es_contribuyente', False)
            elif self.partner_id.vat:
                # Fallback al campo VAT estándar de Odoo
                self.rnc = self.partner_id.vat
                self.tipo_rnc = 'rnc'
                self.es_contribuyente = True
            else:
                self.rnc = False
                self.tipo_rnc = False
                self.es_contribuyente = False
            
            # Determinar tipo de comprobante apropiado
            self._suggest_tipo_comprobante()
    
    def _suggest_tipo_comprobante(self):
        """Sugiere el tipo de comprobante apropiado"""
        self.ensure_one()
        if not self.move_type in ['out_invoice', 'out_refund']:
            return
        
        domain = [('para_venta', '=', True), ('activo', '=', True)]
        
        # Determinar tipo basado en cliente
        if self.move_type == 'out_refund':
            # Notas de crédito
            codigo_tipo = '04'
        elif self.rnc and self.es_contribuyente:
            # Cliente con RNC - Factura con crédito fiscal
            codigo_tipo = '01'
        else:
            # Consumidor final - Factura de consumo
            codigo_tipo = '02'
        
        tipo_sugerido = self.env['tipo.comprobante'].search([
            ('codigo', '=', codigo_tipo)
        ] + domain, limit=1)
        
        if tipo_sugerido:
            self.tipo_comprobante_id = tipo_sugerido.id

    @api.onchange('tipo_comprobante_id')
    def _onchange_tipo_comprobante(self):
        """Valida y prepara NCF al seleccionar tipo de comprobante"""
        if self.tipo_comprobante_id:
            warnings = []
            
            # Validar RNC si es requerido
            if self.tipo_comprobante_id.requiere_rnc and not self.rnc:
                warnings.append(_('⚠️ El tipo de comprobante seleccionado requiere que el cliente tenga RNC.'))
            
            # Verificar si hay secuencia disponible
            if self.tipo_comprobante_id.es_fiscal:
                try:
                    sequence = self.env['ncf.sequence'].get_active_sequence_for_type(
                        self.tipo_comprobante_id.id, 
                        self.company_id.id
                    )
                    alert_msg = sequence.get_alert_message()
                    if alert_msg:
                        warnings.append(alert_msg)
                except ValidationError as e:
                    warnings.append(f'❌ {str(e)}')
            
            # Mostrar advertencias si las hay
            if warnings:
                return {
                    'warning': {
                        'title': _('Advertencias NCF'),
                        'message': '\n'.join(warnings)
                    }
                }

    @api.constrains('ncf')
    def _check_ncf_format(self):
        """Valida el formato del NCF"""
        for record in self:
            if record.ncf:
                if not re.match(r'^[A-Z]\d{10}$', record.ncf):
                    raise ValidationError(
                        _('El NCF debe tener el formato: 1 letra seguida de 10 dígitos')
                    )

    @api.constrains('ncf')
    def _check_ncf_unique(self):
        """Valida que el NCF sea único"""
        for record in self:
            if record.ncf:
                existing = self.search([
                    ('ncf', '=', record.ncf),
                    ('id', '!=', record.id),
                    ('anulado', '=', False)
                ])
                if existing:
                    raise ValidationError(
                        _('Ya existe una factura con el NCF %s') % record.ncf
                    )

    def action_post(self):
        """Genera NCF automáticamente al confirmar la factura con validaciones completas"""
        for record in self:
            # Simplificar la condición - solo verificar si es factura fiscal
            if record.es_factura_fiscal:
                # Validaciones antes de confirmar
                record._validate_before_post()
                
                # Generar NCF si no tiene uno
                if not record.ncf:
                    record._generate_ncf()
                    
                # Validar que el NCF se generó correctamente
                if not record.ncf:
                    raise ValidationError(
                        _('No se pudo generar el NCF para la factura. Verifique las secuencias configuradas.')
                    )
        
        # Llamar al método padre
        result = super().action_post()
        
        # Si se generó NCF, forzar refrescado de la vista
        if self.ncf and self.es_factura_fiscal:
            # Invalida cache para asegurar que la UI se actualice
            self.env.cache.invalidate()
            
        return result
    
    def _validate_before_post(self):
        """Validaciones completas antes de confirmar la factura"""
        self.ensure_one()
        
        # Validar tipo de comprobante
        if not self.tipo_comprobante_id:
            raise ValidationError(
                _('Debe seleccionar un tipo de comprobante fiscal para esta factura.')
            )
        
        # Validar RNC si es requerido
        if self.tipo_comprobante_id.requiere_rnc and not self.rnc:
            raise ValidationError(
                _('El tipo de comprobante "%s" requiere que el cliente tenga RNC/Cédula.') % 
                self.tipo_comprobante_id.name
            )
        
        # Validar secuencia disponible
        if self.tipo_comprobante_id.es_fiscal:
            try:
                sequence = self.env['ncf.sequence'].get_active_sequence_for_type(
                    self.tipo_comprobante_id.id, 
                    self.company_id.id
                )
                # Verificar que no esté agotada o vencida
                if sequence.estado != 'activa':
                    raise ValidationError(
                        _('La secuencia NCF para el tipo "%s" no está disponible. Estado: %s') % 
                        (self.tipo_comprobante_id.name, sequence.estado)
                    )
            except ValidationError as e:
                raise ValidationError(
                    _('Error de secuencia NCF: %s') % str(e)
                )

    def preview_next_ncf(self):
        """Muestra el próximo NCF que sería asignado (sin consumir)"""
        self.ensure_one()
        
        if not (self.tipo_comprobante_id and self.tipo_comprobante_id.es_fiscal):
            return False
        
        try:
            sequence = self.env['ncf.sequence'].get_active_sequence_for_type(
                self.tipo_comprobante_id.id, 
                self.company_id.id
            )
            
            # Calcular siguiente número sin consumir
            next_number = sequence.secuencia_actual + 1 if sequence.secuencia_actual >= sequence.secuencia_desde else sequence.secuencia_desde
            preview_ncf = f"{sequence.serie}{self.tipo_comprobante_id.codigo}{str(next_number).zfill(8)}"
            
            return {
                'ncf': preview_ncf,
                'sequence': sequence.display_name,
                'disponibles': sequence.disponibles
            }
            
        except ValidationError:
            return False

    def _generate_ncf(self):
        """Genera el NCF automáticamente con manejo robusto de errores"""
        self.ensure_one()
        
        # Log de debug para verificar condiciones
        if not self.tipo_comprobante_id:
            raise ValidationError(_('No hay tipo de comprobante seleccionado'))
        
        if not self.tipo_comprobante_id.es_fiscal:
            raise ValidationError(_('El tipo de comprobante %s no es fiscal') % self.tipo_comprobante_id.name)
        
        try:
            # Obtener secuencia activa
            sequence = self.env['ncf.sequence'].get_active_sequence_for_type(
                self.tipo_comprobante_id.id, 
                self.company_id.id
            )
            
            # Generar NCF y asociar secuencia usando write para bypass readonly
            ncf_generado = sequence.get_next_ncf()
            
            # Forzar la actualización usando sudo para bypass de cualquier restricción
            self.sudo().write({
                'ncf': ncf_generado,
                'ncf_sequence_id': sequence.id
            })
            
            # Refrescar el record para asegurar que se vean los cambios
            self.env.flush_all()
            self._compute_es_factura_fiscal()
            
            # Recargar el record desde la base de datos para refrescar todos los campos
            self.env.cache.invalidate()
            
            # Log para auditoría
            self.message_post(
                body=_('NCF %s asignado desde secuencia %s') % (ncf_generado, sequence.display_name)
            )
            
            return ncf_generado
            
        except ValidationError as e:
            raise ValidationError(
                _('Error al generar NCF para la factura: %s') % str(e)
            )

    def action_force_generate_ncf(self):
        """Método para generar NCF manualmente (para debug)"""
        self.ensure_one()
        if self.ncf:
            raise ValidationError(_('Esta factura ya tiene un NCF asignado: %s') % self.ncf)
        
        ncf_generado = self._generate_ncf()
        
        if ncf_generado:
            # Recargar la vista completa para mostrar el NCF asignado
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'current',
                'context': {
                    'show_notification': True,
                    'notification_message': _('NCF %s asignado exitosamente') % ncf_generado,
                    'notification_type': 'success'
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('No se pudo generar el NCF'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

    def action_anular_ncf(self):
        """Anula el NCF del comprobante"""
        for record in self:
            if record.state != 'posted':
                raise ValidationError(_('Solo se pueden anular facturas confirmadas'))
            
            record.write({
                'anulado': True,
                'fecha_anulacion': fields.Datetime.now(),
                'state': 'cancel'
            })

    def action_reactivar_ncf(self):
        """Reactiva el NCF del comprobante"""
        for record in self:
            record.write({
                'anulado': False,
                'fecha_anulacion': False,
                'motivo_anulacion': False
            })

    @api.model
    def get_facturas_606(self, fecha_desde, fecha_hasta):
        """Obtiene facturas para reporte 606 (ventas)"""
        domain = [
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', fecha_desde),
            ('invoice_date', '<=', fecha_hasta),
            ('anulado', '=', False),
            ('es_fiscal', '=', True)
        ]
        return self.search(domain)

    @api.model
    def get_facturas_607(self, fecha_desde, fecha_hasta):
        """Obtiene facturas para reporte 607 (compras)"""
        domain = [
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', fecha_desde),
            ('invoice_date', '<=', fecha_hasta),
            ('anulado', '=', False)
        ]
        return self.search(domain)

    def get_itbis_amount(self):
        """Calcula el monto de ITBIS"""
        self.ensure_one()
        itbis_amount = 0.0
        for line in self.line_ids:
            if line.tax_line_id and 'ITBIS' in line.tax_line_id.name.upper():
                itbis_amount += abs(line.balance)
        return itbis_amount

    def get_base_amount(self):
        """Calcula el monto base (sin impuestos)"""
        self.ensure_one()
        return abs(self.amount_untaxed)

    def get_total_amount(self):
        """Calcula el monto total"""
        self.ensure_one()
        return abs(self.amount_total)

    def write(self, vals):
        """Sobrescribir write para permitir actualización de NCF desde código interno"""
        return super().write(vals)
