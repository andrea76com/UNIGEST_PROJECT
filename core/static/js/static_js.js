/**
 * UNIGEST - Custom JavaScript
 * File: core/static/js/script.js
 * Descrizione: Script JavaScript per funzionalità client-side
 */

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('UNIGEST - JavaScript initialized');
    
    // Inizializza tutte le funzionalità
    initTooltips();
    initConfirmDialogs();
    initFormValidation();
    initSearchFilters();
    initTableSorting();
    autoHideAlerts();
});

// ============================================================================
// TOOLTIPS
// ============================================================================

/**
 * Inizializza i tooltip di Bootstrap
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
    );
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ============================================================================
// CONFIRM DIALOGS
// ============================================================================

/**
 * Aggiunge conferma prima di eliminare
 */
function initConfirmDialogs() {
    // Conferma per eliminazioni
    const deleteButtons = document.querySelectorAll('.btn-delete, .delete-confirm');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Sei sicuro di voler eliminare questo elemento? L\'operazione non può essere annullata.')) {
                e.preventDefault();
                return false;
            }
        });
    });
    
    // Conferma per form di eliminazione
    const deleteForms = document.querySelectorAll('form[action*="elimina"], form[action*="delete"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Sei sicuro di voler procedere con l\'eliminazione?')) {
                e.preventDefault();
                return false;
            }
        });
    });
}

// ============================================================================
// FORM VALIDATION
// ============================================================================

/**
 * Validazione form lato client
 */
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Validazione Codice Fiscale italiano
    const cfInputs = document.querySelectorAll('input[name="codice_fiscale"]');
    cfInputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateCodiceFiscale(this);
        });
    });
}

/**
 * Valida formato Codice Fiscale
 */
function validateCodiceFiscale(input) {
    const cf = input.value.trim().toUpperCase();
    
    if (cf.length === 0) return true; // Campo opzionale
    
    if (cf.length !== 16) {
        showFieldError(input, 'Il Codice Fiscale deve essere di 16 caratteri');
        return false;
    }
    
    const cfPattern = /^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$/;
    if (!cfPattern.test(cf)) {
        showFieldError(input, 'Formato Codice Fiscale non valido');
        return false;
    }
    
    clearFieldError(input);
    return true;
}

/**
 * Mostra errore su campo form
 */
function showFieldError(input, message) {
    input.classList.add('is-invalid');
    
    let errorDiv = input.parentElement.querySelector('.invalid-feedback');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        input.parentElement.appendChild(errorDiv);
    }
    errorDiv.textContent = message;
}

/**
 * Rimuove errore da campo form
 */
function clearFieldError(input) {
    input.classList.remove('is-invalid');
    const errorDiv = input.parentElement.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// ============================================================================
// SEARCH & FILTERS
// ============================================================================

/**
 * Gestione filtri di ricerca
 */
function initSearchFilters() {
    // Auto-submit form di ricerca dopo selezione dropdown
    const filterSelects = document.querySelectorAll('.filter-select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            this.form.submit();
        });
    });
    
    // Ricerca in tempo reale nelle tabelle
    const tableSearchInputs = document.querySelectorAll('.table-search');
    tableSearchInputs.forEach(input => {
        input.addEventListener('keyup', function() {
            filterTable(this);
        });
    });
}

/**
 * Filtra righe tabella in base alla ricerca
 */
function filterTable(input) {
    const filter = input.value.toLowerCase();
    const tableId = input.getAttribute('data-table');
    const table = document.getElementById(tableId);
    
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(filter)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// ============================================================================
// TABLE SORTING
// ============================================================================

/**
 * Ordinamento colonne tabella
 */
function initTableSorting() {
    const sortableHeaders = document.querySelectorAll('th[data-sortable]');
    
    sortableHeaders.forEach(header => {
        header.style.cursor = 'pointer';
        header.innerHTML += ' <i class="bi bi-arrow-down-up text-muted"></i>';
        
        header.addEventListener('click', function() {
            sortTable(this);
        });
    });
}

/**
 * Ordina tabella per colonna
 */
function sortTable(header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentElement.children).indexOf(header);
    const isAscending = header.classList.contains('sort-asc');
    
    // Rimuovi indicatori da tutti gli header
    header.parentElement.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Ordina righe
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        // Prova a convertire in numero
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? bNum - aNum : aNum - bNum;
        }
        
        return isAscending 
            ? bValue.localeCompare(aValue, 'it') 
            : aValue.localeCompare(bValue, 'it');
    });
    
    // Applica ordinamento
    rows.forEach(row => tbody.appendChild(row));
    
    // Aggiorna indicatore
    header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
}

// ============================================================================
// AUTO-HIDE ALERTS
// ============================================================================

/**
 * Nasconde automaticamente gli alert dopo 5 secondi
 */
function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

// ============================================================================
// LOADING OVERLAY
// ============================================================================

/**
 * Mostra overlay di caricamento
 */
function showLoading(message = 'Caricamento in corso...') {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'spinner-overlay';
    overlay.innerHTML = `
        <div class="text-center">
            <div class="spinner-border spinner-border-lg text-light" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-light mt-3">${message}</p>
        </div>
    `;
    document.body.appendChild(overlay);
}

/**
 * Nasconde overlay di caricamento
 */
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Formatta data in formato italiano
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

/**
 * Formatta ora in formato italiano
 */
function formatTime(timeString) {
    return timeString.substring(0, 5); // HH:MM
}

/**
 * Copia testo negli appunti
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copiato negli appunti!', 'success');
    }).catch(err => {
        console.error('Errore nella copia:', err);
        showToast('Errore nella copia', 'danger');
    });
}

/**
 * Mostra toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Rimuovi dopo che si nasconde
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

/**
 * Crea container per toast
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// ============================================================================
// EXPORT FUNCTIONS
// ============================================================================

/**
 * Esporta tabella in CSV
 */
function exportTableToCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = Array.from(cols).map(col => {
            return '"' + col.textContent.trim().replace(/"/g, '""') + '"';
        });
        csv.push(rowData.join(','));
    });
    
    downloadCSV(csv.join('\n'), filename);
}

/**
 * Download file CSV
 */
function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (navigator.msSaveBlob) {
        navigator.msSaveBlob(blob, filename);
    } else {
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
    }
}

// ============================================================================
// PRINT FUNCTIONS
// ============================================================================

/**
 * Stampa contenuto di un elemento
 */
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const printWindow = window.open('', '', 'height=600,width=800');
    printWindow.document.write('<html><head><title>Stampa</title>');
    
    // Copia gli stili
    const styles = document.querySelectorAll('style, link[rel="stylesheet"]');
    styles.forEach(style => {
        printWindow.document.write(style.outerHTML);
    });
    
    printWindow.document.write('</head><body>');
    printWindow.document.write(element.innerHTML);
    printWindow.document.write('</body></html>');
    
    printWindow.document.close();
    printWindow.focus();
    
    setTimeout(() => {
        printWindow.print();
        printWindow.close();
    }, 250);
}

// ============================================================================
// AJAX HELPERS
// ============================================================================

/**
 * GET request generico
 */
async function ajaxGet(url) {
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        return await response.json();
    } catch (error) {
        console.error('AJAX GET Error:', error);
        showToast('Errore nella richiesta', 'danger');
        return null;
    }
}

/**
 * POST request generico
 */
async function ajaxPost(url, data) {
    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        });
        return await response.json();
    } catch (error) {
        console.error('AJAX POST Error:', error);
        showToast('Errore nell\'invio dei dati', 'danger');
        return null;
    }
}

// ============================================================================
// CONSOLE LOG (DEVELOPMENT)
// ============================================================================

console.log('UNIGEST JavaScript loaded successfully');
console.log('Bootstrap version:', bootstrap.Tooltip.VERSION);
