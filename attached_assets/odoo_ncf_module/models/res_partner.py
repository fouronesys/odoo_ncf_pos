# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tipo_rnc = fields.Selection([
        ('rnc', 'RNC'),
        ('cedula', 'Cédula'),
        ('pasaporte', 'Pasaporte'),
    ], string='Tipo de Documento', 
       help='Tipo de documento de identificación')
    
    rnc = fields.Char(
        string='RNC/Cédula',
        help='Registro Nacional del Contribuyente o Cédula de Identidad'
    )
    
    es_contribuyente = fields.Boolean(
        string='Es Contribuyente',
        help='Indica si es contribuyente registrado en la DGII'
    )
    
    exento_itbis = fields.Boolean(
        string='Exento de ITBIS',
        help='Indica si está exento del pago de ITBIS'
    )

    @api.onchange('tipo_rnc', 'rnc')
    def _onchange_rnc_validation(self):
        """Valida formato de RNC/Cédula"""
        if self.rnc and self.tipo_rnc:
            rnc_clean = re.sub(r'[^0-9]', '', self.rnc)
            
            if self.tipo_rnc == 'rnc':
                if len(rnc_clean) != 9:
                    return {
                        'warning': {
                            'title': _('RNC Inválido'),
                            'message': _('El RNC debe tener 9 dígitos.')
                        }
                    }
                # Formatear RNC
                self.rnc = f"{rnc_clean[:1]}-{rnc_clean[1:3]}-{rnc_clean[3:8]}-{rnc_clean[8:9]}"
                self.vat = self.rnc
                self.es_contribuyente = True
                
            elif self.tipo_rnc == 'cedula':
                if len(rnc_clean) != 11:
                    return {
                        'warning': {
                            'title': _('Cédula Inválida'),
                            'message': _('La cédula debe tener 11 dígitos.')
                        }
                    }
                # Formatear Cédula
                self.rnc = f"{rnc_clean[:3]}-{rnc_clean[3:10]}-{rnc_clean[10:11]}"
                self.vat = self.rnc

    @api.constrains('rnc', 'tipo_rnc')
    def _check_rnc_format(self):
        """Valida el formato de RNC/Cédula"""
        for record in self:
            if record.rnc and record.tipo_rnc:
                rnc_clean = re.sub(r'[^0-9]', '', record.rnc)
                
                if record.tipo_rnc == 'rnc' and len(rnc_clean) != 9:
                    raise ValidationError(_('El RNC debe tener exactamente 9 dígitos'))
                
                if record.tipo_rnc == 'cedula' and len(rnc_clean) != 11:
                    raise ValidationError(_('La cédula debe tener exactamente 11 dígitos'))

    @api.constrains('rnc')
    def _check_rnc_unique(self):
        """Valida que el RNC sea único"""
        for record in self:
            if record.rnc:
                existing = self.search([
                    ('rnc', '=', record.rnc),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        _('Ya existe un contacto con el RNC/Cédula %s') % record.rnc
                    )

    def name_get(self):
        """Incluye RNC en el nombre si existe"""
        result = []
        for record in self:
            name = record.name or ''
            if record.rnc:
                name = f"{name} [{record.rnc}]"
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=100, order=None):
        """Permite buscar por RNC"""
        if domain is None:
            domain = []
        
        if name:
            # Buscar por RNC también
            domain = ['|', ('name', operator, name), ('rnc', operator, name)] + domain
        
        return self._search(domain, limit=limit, order=order)

    def action_validate_rnc_dgii(self):
        """Acción para validar RNC en DGII (placeholder)"""
        # Esta función podría implementarse para validar en línea con la DGII
        for record in self:
            if record.rnc and record.tipo_rnc == 'rnc':
                # Aquí iría la lógica de validación con la API de DGII
                # Por ahora, solo marcamos como contribuyente si tiene RNC válido
                rnc_clean = re.sub(r'[^0-9]', '', record.rnc)
                if len(rnc_clean) == 9:
                    record.es_contribuyente = True
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Validación RNC'),
                'message': _('RNC validado correctamente'),
                'type': 'success',
            }
        }
