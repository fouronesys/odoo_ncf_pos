# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class TipoComprobante(models.Model):
    _name = 'tipo.comprobante'
    _description = 'Tipos de Comprobantes Fiscales Dominicanos'
    _order = 'codigo'

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre del tipo de comprobante fiscal'
    )
    codigo = fields.Char(
        string='Código',
        required=True,
        size=2,
        help='Código de dos dígitos del tipo de comprobante'
    )
    descripcion = fields.Text(
        string='Descripción',
        help='Descripción detallada del tipo de comprobante'
    )
    secuencia_id = fields.Many2one(
        'ir.sequence',
        string='Secuencia NCF',
        help='Secuencia para generar los números de comprobante fiscal'
    )
    activo = fields.Boolean(
        string='Activo',
        default=True,
        help='Indica si el tipo de comprobante está activo'
    )
    es_fiscal = fields.Boolean(
        string='Es Fiscal',
        default=True,
        help='Indica si el comprobante es fiscal'
    )
    para_venta = fields.Boolean(
        string='Para Ventas',
        default=True,
        help='Indica si se usa para ventas'
    )
    para_compra = fields.Boolean(
        string='Para Compras',
        default=False,
        help='Indica si se usa para compras'
    )
    requiere_rnc = fields.Boolean(
        string='Requiere RNC',
        default=True,
        help='Indica si requiere RNC del cliente'
    )

    @api.constrains('codigo')
    def _check_codigo(self):
        """Valida que el código sea de 2 dígitos numéricos"""
        for record in self:
            if not re.match(r'^\d{2}$', record.codigo):
                raise ValidationError(
                    _('El código debe ser de 2 dígitos numéricos')
                )

    @api.constrains('codigo')
    def _check_codigo_unique(self):
        """Valida que el código sea único"""
        for record in self:
            existing = self.search([
                ('codigo', '=', record.codigo),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(
                    _('Ya existe un tipo de comprobante con el código %s') % record.codigo
                )

    def name_get(self):
        """Retorna el nombre con el código"""
        result = []
        for record in self:
            name = f"[{record.codigo}] {record.name}"
            result.append((record.id, name))
        return result

    @api.model
    def create_sequence(self, codigo, name):
        """Crea una secuencia para el tipo de comprobante"""
        sequence_vals = {
            'name': f'NCF {name}',
            'code': f'ncf.{codigo}',
            'prefix': f'B{codigo}',
            'suffix': '',
            'padding': 8,
            'number_next': 1,
            'number_increment': 1,
            'implementation': 'standard',
        }
        return self.env['ir.sequence'].create(sequence_vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Crea automáticamente la secuencia si no existe"""
        records = super().create(vals_list)
        for record in records:
            if not record.secuencia_id:
                sequence = self.create_sequence(record.codigo, record.name)
                record.secuencia_id = sequence.id
        return records


class NCFSequence(models.Model):
    _name = 'ncf.sequence'
    _description = 'Secuencias NCF por Empresa'
    _order = 'company_id, fecha_inicio desc'
    _rec_name = 'display_name'

    name = fields.Char(
        string='Nombre',
        required=True
    )
    display_name = fields.Char(
        string='Nombre Completo',
        compute='_compute_display_name',
        store=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company
    )
    tipo_comprobante_id = fields.Many2one(
        'tipo.comprobante',
        string='Tipo de Comprobante',
        required=True
    )
    serie = fields.Char(
        string='Serie',
        required=True,
        size=1,
        help='Serie del NCF (A, B, E, etc.)'
    )
    secuencia_desde = fields.Integer(
        string='Desde',
        required=True,
        help='Número inicial de la secuencia'
    )
    secuencia_hasta = fields.Integer(
        string='Hasta',
        required=True,
        help='Número final de la secuencia'
    )
    secuencia_actual = fields.Integer(
        string='Número Actual',
        help='Próximo número a asignar de la secuencia',
        default=0
    )
    fecha_inicio = fields.Date(
        string='Fecha Inicio',
        required=True,
        default=fields.Date.context_today
    )
    fecha_fin = fields.Date(
        string='Fecha Vencimiento',
        required=True
    )
    activa = fields.Boolean(
        string='Activa',
        default=True
    )
    agotada = fields.Boolean(
        string='Agotada',
        compute='_compute_estado',
        store=True
    )
    vencida = fields.Boolean(
        string='Vencida',
        compute='_compute_estado',
        store=True
    )
    disponibles = fields.Integer(
        string='NCF Disponibles',
        compute='_compute_disponibles',
        store=True
    )
    usados = fields.Integer(
        string='NCF Usados',
        compute='_compute_disponibles',
        store=True
    )
    total = fields.Integer(
        string='Total NCF',
        compute='_compute_disponibles',
        store=True
    )
    porcentaje_usado = fields.Float(
        string='% Usado',
        compute='_compute_disponibles',
        store=True
    )
    estado = fields.Selection([
        ('activa', 'Activa'),
        ('agotada', 'Agotada'),
        ('vencida', 'Vencida'),
        ('inactiva', 'Inactiva')
    ], string='Estado', compute='_compute_estado', store=True)
    alerta_stock_bajo = fields.Boolean(
        string='Alerta Stock Bajo',
        compute='_compute_alertas',
        store=True
    )
    alerta_vencimiento = fields.Boolean(
        string='Alerta Vencimiento Próximo',
        compute='_compute_alertas',
        store=True
    )
    limite_alerta_stock = fields.Integer(
        string='Límite Alerta Stock',
        default=10,
        help='Cantidad mínima de NCF para mostrar alerta'
    )
    dias_alerta_vencimiento = fields.Integer(
        string='Días Alerta Vencimiento',
        default=30,
        help='Días antes del vencimiento para mostrar alerta'
    )

    @api.depends('company_id', 'name', 'tipo_comprobante_id', 'serie')
    def _compute_display_name(self):
        """Calcula el nombre para mostrar"""
        for record in self:
            record.display_name = f"[{record.company_id.name}] {record.serie}{record.tipo_comprobante_id.codigo} - {record.name}"

    @api.depends('secuencia_actual', 'secuencia_hasta', 'fecha_fin', 'activa')
    def _compute_estado(self):
        """Calcula el estado de la secuencia"""
        today = fields.Date.context_today(self)
        for record in self:
            if not record.activa:
                record.estado = 'inactiva'
                record.agotada = False
                record.vencida = False
            elif record.fecha_fin and record.fecha_fin < today:
                record.estado = 'vencida'
                record.agotada = False
                record.vencida = True
            elif record.secuencia_actual >= record.secuencia_hasta:
                record.estado = 'agotada'
                record.agotada = True
                record.vencida = False
            else:
                record.estado = 'activa'
                record.agotada = False
                record.vencida = False

    @api.depends('secuencia_desde', 'secuencia_hasta', 'secuencia_actual')
    def _compute_disponibles(self):
        """Calcula los NCF disponibles y usados"""
        for record in self:
            record.total = record.secuencia_hasta - record.secuencia_desde + 1
            record.usados = max(0, record.secuencia_actual - record.secuencia_desde)
            record.disponibles = record.total - record.usados
            if record.total > 0:
                record.porcentaje_usado = (record.usados / record.total) * 100
            else:
                record.porcentaje_usado = 0

    @api.depends('disponibles', 'limite_alerta_stock', 'fecha_fin', 'dias_alerta_vencimiento', 'estado')
    def _compute_alertas(self):
        """Calcula las alertas de stock bajo y vencimiento próximo"""
        today = fields.Date.context_today(self)
        for record in self:
            # Alerta de stock bajo
            record.alerta_stock_bajo = (
                record.estado == 'activa' and 
                record.disponibles <= record.limite_alerta_stock and 
                record.disponibles > 0
            )
            
            # Alerta de vencimiento próximo
            if record.fecha_fin:
                dias_restantes = (record.fecha_fin - today).days
                record.alerta_vencimiento = (
                    record.estado == 'activa' and 
                    dias_restantes <= record.dias_alerta_vencimiento and 
                    dias_restantes > 0
                )
            else:
                record.alerta_vencimiento = False

    @api.constrains('secuencia_desde', 'secuencia_hasta')
    def _check_secuencia_range(self):
        """Valida el rango de la secuencia"""
        for record in self:
            if record.secuencia_desde >= record.secuencia_hasta:
                raise ValidationError(
                    _('El número inicial debe ser menor al número final')
                )

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        """Valida las fechas"""
        for record in self:
            if record.fecha_inicio and record.fecha_fin and record.fecha_inicio >= record.fecha_fin:
                raise ValidationError(
                    _('La fecha de inicio debe ser anterior a la fecha de fin')
                )

    def get_next_ncf(self):
        """Obtiene el próximo NCF de la secuencia con validaciones completas"""
        self.ensure_one()
        
        # Validaciones de estado
        if not self.activa:
            raise ValidationError(
                _('La secuencia NCF "%s" no está activa') % self.display_name
            )
        
        if self.vencida:
            raise ValidationError(
                _('La secuencia NCF "%s" está vencida. Fecha límite: %s') % 
                (self.display_name, self.fecha_fin)
            )
        
        if self.agotada:
            raise ValidationError(
                _('La secuencia NCF "%s" está agotada. No hay más números disponibles.') % 
                self.display_name
            )
        
        # Inicializar secuencia si es necesario
        if self.secuencia_actual < self.secuencia_desde:
            self.secuencia_actual = self.secuencia_desde
        else:
            self.secuencia_actual += 1
        
        # Validar que no se exceda el límite
        if self.secuencia_actual > self.secuencia_hasta:
            raise ValidationError(
                _('Se ha excedido el límite de la secuencia NCF "%s"') % self.display_name
            )
        
        # Formatear el NCF (Serie + Código + Número con 8 dígitos)
        ncf = f"{self.serie}{self.tipo_comprobante_id.codigo}{str(self.secuencia_actual).zfill(8)}"
        
        # Verificar que el NCF no esté ya asignado
        existing_ncf = self.env['account.move'].search([
            ('ncf', '=', ncf),
            ('company_id', '=', self.company_id.id)
        ])
        
        if existing_ncf:
            raise ValidationError(
                _('El NCF %s ya está asignado a la factura %s') % (ncf, existing_ncf[0].name)
            )
        
        return ncf
    
    @api.model
    def get_active_sequence_for_type(self, tipo_comprobante_id, company_id=None):
        """Obtiene la secuencia activa para un tipo de comprobante específico"""
        if not company_id:
            company_id = self.env.company.id
        
        today = fields.Date.context_today(self)
        
        sequence = self.search([
            ('tipo_comprobante_id', '=', tipo_comprobante_id),
            ('company_id', '=', company_id),
            ('activa', '=', True),
            ('fecha_inicio', '<=', today),
            ('fecha_fin', '>=', today),
            ('estado', '=', 'activa')
        ], order='fecha_inicio desc', limit=1)
        
        if not sequence:
            tipo_comprobante = self.env['tipo.comprobante'].browse(tipo_comprobante_id)
            raise ValidationError(
                _('No hay secuencia NCF activa configurada para el tipo de comprobante %s en la empresa %s') % 
                (tipo_comprobante.name, self.env.company.name)
            )
        
        return sequence
    
    def get_alert_message(self):
        """Obtiene mensaje de alerta si aplica"""
        self.ensure_one()
        messages = []
        
        if self.alerta_stock_bajo:
            messages.append(
                _('⚠️ Stock bajo: Solo quedan %d NCF disponibles en la secuencia %s') % 
                (self.disponibles, self.display_name)
            )
        
        if self.alerta_vencimiento:
            dias_restantes = (self.fecha_fin - fields.Date.context_today(self)).days
            messages.append(
                _('⚠️ Vencimiento próximo: La secuencia %s vence en %d días (%s)') % 
                (self.display_name, dias_restantes, self.fecha_fin)
            )
        
        return '\n'.join(messages) if messages else ''
    
    @api.model
    def check_all_alerts(self):
        """Método para verificar todas las alertas del sistema"""
        sequences_with_alerts = self.search([
            '|', ('alerta_stock_bajo', '=', True), ('alerta_vencimiento', '=', True),
            ('activa', '=', True)
        ])
        
        alerts = []
        for sequence in sequences_with_alerts:
            alert_msg = sequence.get_alert_message()
            if alert_msg:
                alerts.append(alert_msg)
        
        return alerts
