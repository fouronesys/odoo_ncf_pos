# -*- coding: utf-8 -*-
"""
Demostración Web del Módulo POS NCF Integration para Odoo 17
Esta aplicación simula la funcionalidad del módulo NCF en un entorno de demostración
"""

from flask import Flask, render_template_string, jsonify, request
import json
import random
from datetime import datetime

app = Flask(__name__)

# Datos de demostración que simularían los datos de Odoo
TIPOS_COMPROBANTE = [
    {"id": 1, "codigo": "01", "name": "Factura con Valor Fiscal", "es_fiscal": True, "para_venta": True, "requiere_rnc": True},
    {"id": 2, "codigo": "02", "name": "Factura para Consumidores Finales", "es_fiscal": True, "para_venta": True, "requiere_rnc": False},
    {"id": 3, "codigo": "03", "name": "Nota de Débito", "es_fiscal": True, "para_venta": True, "requiere_rnc": True},
    {"id": 4, "codigo": "04", "name": "Nota de Crédito", "es_fiscal": True, "para_venta": True, "requiere_rnc": True},
    {"id": 5, "codigo": "11", "name": "Registro de Proveedores Informales", "es_fiscal": False, "para_venta": False, "requiere_rnc": False},
]

SECUENCIAS_NCF = {
    1: {"serie": "B", "codigo": "01", "actual": 1234, "limite": 9999},
    2: {"serie": "B", "codigo": "02", "actual": 5678, "limite": 9999},
    3: {"serie": "B", "codigo": "03", "actual": 100, "limite": 999},
    4: {"serie": "B", "codigo": "04", "actual": 50, "limite": 999},
}

@app.route('/')
def index():
    """Página principal que simula la interfaz POS con NCF"""
    return render_template_string(INDEX_TEMPLATE, tipos_comprobante=TIPOS_COMPROBANTE)

@app.route('/api/generate_ncf', methods=['POST'])
def generate_ncf():
    """API que simula la generación de NCF"""
    try:
        data = request.get_json()
        tipo_id = data.get('tipo_comprobante_id')
        
        if not tipo_id:
            return jsonify({"success": False, "error": "Tipo de comprobante requerido"})
        
        tipo_id = int(tipo_id)
        tipo_comprobante = next((t for t in TIPOS_COMPROBANTE if t["id"] == tipo_id), None)
        
        if not tipo_comprobante:
            return jsonify({"success": False, "error": "Tipo de comprobante no encontrado"})
        
        if not tipo_comprobante["es_fiscal"]:
            return jsonify({"success": True, "ncf": "", "es_fiscal": False})
        
        # Simular generación de NCF
        if tipo_id in SECUENCIAS_NCF:
            seq = SECUENCIAS_NCF[tipo_id]
            seq["actual"] += 1
            ncf = f"{seq['serie']}{seq['codigo']}{str(seq['actual']).zfill(8)}"
            
            return jsonify({
                "success": True,
                "ncf": ncf,
                "es_fiscal": True,
                "message": "NCF generado exitosamente"
            })
        else:
            return jsonify({"success": False, "error": "No hay secuencia configurada para este tipo"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/validate_ncf', methods=['POST'])
def validate_ncf():
    """API que simula la validación de NCF"""
    try:
        data = request.get_json()
        ncf = data.get('ncf', '').strip()
        
        if not ncf:
            return jsonify({"valid": False, "error": "NCF es requerido"})
        
        if len(ncf) != 11:
            return jsonify({"valid": False, "error": "NCF debe tener 11 caracteres"})
        
        if not ncf.isalnum():
            return jsonify({"valid": False, "error": "NCF solo puede contener letras y números"})
        
        # Simular validación adicional
        if ncf.startswith('B'):
            return jsonify({"valid": True, "message": "NCF válido"})
        else:
            return jsonify({"valid": False, "error": "NCF debe comenzar con la serie correcta"})
            
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)})

# Template HTML para la demostración
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Demostración - Módulo POS NCF Integration para Odoo 17</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .pos-container { max-width: 1200px; margin: 0 auto; }
        .pos-header { background: linear-gradient(135deg, #007bff, #0056b3); color: white; }
        .order-summary { background: #f8f9fa; border-radius: 10px; }
        .ncf-info { background: #e3f2fd; border-left: 4px solid #2196f3; }
        .btn-ncf { background: linear-gradient(135deg, #28a745, #20c997); border: none; }
        .btn-ncf:hover { background: linear-gradient(135deg, #20c997, #28a745); }
        .demo-badge { position: fixed; top: 10px; right: 10px; z-index: 9999; }
    </style>
</head>
<body>
    <div class="demo-badge">
        <span class="badge bg-warning text-dark fs-6">
            <i class="fas fa-flask"></i> DEMO - Módulo Odoo 17
        </span>
    </div>

    <div class="pos-header py-4 mb-4">
        <div class="container">
            <div class="row align-items-center">
                <div class="col-md-8">
                    <h1 class="mb-0">
                        <i class="fas fa-cash-register me-3"></i>
                        POS NCF Integration - Odoo 17
                    </h1>
                    <p class="mb-0 opacity-75">Integración de Números de Comprobantes Fiscales para República Dominicana</p>
                </div>
                <div class="col-md-4 text-end">
                    <div class="badge bg-success fs-6">
                        <i class="fas fa-check-circle me-1"></i>
                        Actualizado para Odoo 17
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="container pos-container">
        <div class="row">
            <!-- Área de Productos (Simulación) -->
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-shopping-cart me-2"></i>Orden Actual - POS</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Producto</th>
                                        <th>Qty</th>
                                        <th>Precio</th>
                                        <th>Total</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>Café Dominicano Premium</td>
                                        <td>2</td>
                                        <td>RD$ 150.00</td>
                                        <td>RD$ 300.00</td>
                                    </tr>
                                    <tr>
                                        <td>Pan Tostado</td>
                                        <td>1</td>
                                        <td>RD$ 75.00</td>
                                        <td>RD$ 75.00</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        
                        <div class="text-end">
                            <h4>Subtotal: <span class="text-primary">RD$ 375.00</span></h4>
                            <h5>ITBIS (18%): <span class="text-secondary">RD$ 67.50</span></h5>
                            <h3>Total: <span class="text-success">RD$ 442.50</span></h3>
                        </div>
                    </div>
                </div>

                <!-- Área de Información Fiscal -->
                <div class="card mt-3 ncf-info">
                    <div class="card-header bg-primary text-white">
                        <h6 class="mb-0">
                            <i class="fas fa-file-invoice me-2"></i>
                            Información Fiscal NCF
                        </h6>
                    </div>
                    <div class="card-body">
                        <div id="ncf-display" class="d-none">
                            <div class="row">
                                <div class="col-md-6">
                                    <strong>Tipo de Comprobante:</strong>
                                    <div id="tipo-selected" class="fs-5 text-primary"></div>
                                </div>
                                <div class="col-md-6">
                                    <strong>NCF Generado:</strong>
                                    <div id="ncf-generated" class="fs-4 fw-bold text-success font-monospace"></div>
                                </div>
                            </div>
                            <div class="mt-2">
                                <small class="text-muted">
                                    <i class="fas fa-info-circle me-1"></i>
                                    NCF generado automáticamente según secuencias DGII
                                </small>
                            </div>
                        </div>
                        <div id="no-ncf" class="text-center text-muted">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            No hay información fiscal configurada para esta orden
                        </div>
                    </div>
                </div>
            </div>

            <!-- Panel de Control NCF -->
            <div class="col-md-4">
                <div class="card order-summary">
                    <div class="card-header bg-success text-white">
                        <h6 class="mb-0">
                            <i class="fas fa-cogs me-2"></i>
                            Control Fiscal NCF
                        </h6>
                    </div>
                    <div class="card-body">
                        <button class="btn btn-ncf text-white w-100 py-3 mb-3" onclick="showNCFModal()">
                            <i class="fas fa-file-text-o fs-1 d-block mb-2"></i>
                            <div class="fw-bold">Configurar NCF</div>
                            <small>Información Fiscal</small>
                        </button>

                        <div class="alert alert-info">
                            <h6><i class="fas fa-lightbulb me-2"></i>Funcionalidades:</h6>
                            <ul class="mb-0 small">
                                <li>Selección automática de tipo de comprobante</li>
                                <li>Generación automática de NCF</li>
                                <li>Validaciones fiscales en tiempo real</li>
                                <li>Integración con secuencias DGII</li>
                                <li>Compatible con Odoo 17 + OWL</li>
                            </ul>
                        </div>

                        <div class="alert alert-warning">
                            <small>
                                <i class="fas fa-info-circle me-1"></i>
                                <strong>Demo:</strong> Esta es una simulación del módulo real de Odoo 17
                            </small>
                        </div>
                    </div>
                </div>

                <!-- Información del Módulo -->
                <div class="card mt-3">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="fas fa-code me-2"></i>
                            Detalles Técnicos
                        </h6>
                    </div>
                    <div class="card-body">
                        <div class="small">
                            <div class="mb-2">
                                <strong>Framework:</strong> Odoo 17 + OWL 2.0
                            </div>
                            <div class="mb-2">
                                <strong>Patrón JS:</strong> Patch System
                            </div>
                            <div class="mb-2">
                                <strong>Bundle:</strong> point_of_sale._assets_pos
                            </div>
                            <div class="mb-2">
                                <strong>Dependencias:</strong> point_of_sale, odoo_ncf_module
                            </div>
                            <div class="mb-2">
                                <strong>Autor:</strong> Four One Solutions
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal NCF -->
    <div class="modal fade" id="ncfModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="fas fa-file-text-o me-2"></i>
                        Información Fiscal NCF
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <div class="col-12 mb-3">
                            <label class="form-label fw-bold">Tipo de Comprobante:</label>
                            <select class="form-select" id="tipoComprobanteSelect">
                                <option value="">-- Seleccionar Tipo --</option>
                                {% for tipo in tipos_comprobante %}
                                <option value="{{ tipo.id }}" 
                                        data-fiscal="{{ tipo.es_fiscal }}"
                                        data-codigo="{{ tipo.codigo }}"
                                        data-rnc="{{ tipo.requiere_rnc }}">
                                    [{{ tipo.codigo }}] {{ tipo.name }}
                                </option>
                                {% endfor %}
                            </select>
                        </div>
                    </div>

                    <div id="ncfSection" class="d-none">
                        <div class="row">
                            <div class="col-12 mb-3">
                                <label class="form-label fw-bold">NCF (Número de Comprobante Fiscal):</label>
                                <div class="input-group">
                                    <input type="text" class="form-control" id="ncfInput" 
                                           placeholder="Ej: B0100000001" maxlength="11">
                                    <button class="btn btn-outline-primary" type="button" onclick="generateNCF()">
                                        <i class="fas fa-refresh"></i>
                                    </button>
                                </div>
                                <small class="form-text text-muted">
                                    El NCF será generado automáticamente si está vacío
                                </small>
                            </div>
                        </div>

                        <div class="form-check mb-3">
                            <input class="form-check-input" type="checkbox" id="autoGenerate" checked>
                            <label class="form-check-label" for="autoGenerate">
                                Generar NCF automáticamente
                            </label>
                        </div>
                    </div>

                    <div id="tipoInfo" class="d-none">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i>
                            <strong>Información:</strong>
                            <ul class="mb-0 mt-2" id="tipoDetails">
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        <i class="fas fa-times me-2"></i>Cancelar
                    </button>
                    <button type="button" class="btn btn-primary" onclick="confirmNCF()">
                        <i class="fas fa-check me-2"></i>Confirmar
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentOrder = {
            tipo_comprobante_id: null,
            ncf: null,
            es_fiscal: false
        };

        function showNCFModal() {
            const modal = new bootstrap.Modal(document.getElementById('ncfModal'));
            modal.show();
        }

        document.getElementById('tipoComprobanteSelect').addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const isFiscal = selectedOption.dataset.fiscal === 'true';
            const codigo = selectedOption.dataset.codigo;
            const requiresRnc = selectedOption.dataset.rnc === 'true';

            // Mostrar/ocultar sección NCF
            const ncfSection = document.getElementById('ncfSection');
            const tipoInfo = document.getElementById('tipoInfo');
            
            if (this.value && isFiscal) {
                ncfSection.classList.remove('d-none');
                if (document.getElementById('autoGenerate').checked) {
                    generateNCF();
                }
            } else {
                ncfSection.classList.add('d-none');
                document.getElementById('ncfInput').value = '';
            }

            // Mostrar información del tipo
            if (this.value) {
                tipoInfo.classList.remove('d-none');
                const details = document.getElementById('tipoDetails');
                details.innerHTML = `
                    <li>Tipo: ${selectedOption.text}</li>
                    <li>Código: ${codigo}</li>
                    <li>Es Fiscal: <span class="badge ${isFiscal ? 'bg-success' : 'bg-secondary'}">${isFiscal ? 'Sí' : 'No'}</span></li>
                    ${isFiscal && requiresRnc ? '<li>Requiere RNC del cliente</li>' : ''}
                `;
            } else {
                tipoInfo.classList.add('d-none');
            }
        });

        async function generateNCF() {
            const tipoId = document.getElementById('tipoComprobanteSelect').value;
            if (!tipoId) return;

            try {
                const response = await fetch('/api/generate_ncf', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({tipo_comprobante_id: tipoId})
                });

                const result = await response.json();
                if (result.success) {
                    document.getElementById('ncfInput').value = result.ncf;
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error de conexión: ' + error.message);
            }
        }

        async function confirmNCF() {
            const tipoSelect = document.getElementById('tipoComprobanteSelect');
            const ncfInput = document.getElementById('ncfInput');
            
            if (!tipoSelect.value) {
                alert('Debe seleccionar un tipo de comprobante');
                return;
            }

            const selectedOption = tipoSelect.options[tipoSelect.selectedIndex];
            const isFiscal = selectedOption.dataset.fiscal === 'true';

            if (isFiscal && !ncfInput.value) {
                alert('Se requiere NCF para comprobantes fiscales');
                return;
            }

            // Actualizar orden actual
            currentOrder.tipo_comprobante_id = parseInt(tipoSelect.value);
            currentOrder.ncf = ncfInput.value;
            currentOrder.es_fiscal = isFiscal;

            // Actualizar UI
            updateNCFDisplay(selectedOption.text, ncfInput.value);

            // Cerrar modal
            bootstrap.Modal.getInstance(document.getElementById('ncfModal')).hide();
        }

        function updateNCFDisplay(tipoName, ncf) {
            document.getElementById('tipo-selected').textContent = tipoName;
            document.getElementById('ncf-generated').textContent = ncf || 'No fiscal';
            
            document.getElementById('ncf-display').classList.remove('d-none');
            document.getElementById('no-ncf').classList.add('d-none');
        }

        // Inicialización
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Demo del Módulo POS NCF Integration para Odoo 17 cargado');
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)