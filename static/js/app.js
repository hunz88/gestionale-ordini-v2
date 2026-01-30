/* ============================================================================
   ALKEMY PRINT HUB - Main JavaScript
   Voice Recording, File Upload, and Interactive Features
   ============================================================================ */

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Alkemy Print Hub initialized');

    // Initialize tooltips
    initializeTooltips();

    // Initialize auto-dismiss alerts
    initializeAlerts();

    // Check for low stock materials
    checkLowStockMaterials();
});

// ============================================================================
// TOOLTIP INITIALIZATION
// ============================================================================
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ============================================================================
// ALERT AUTO-DISMISS
// ============================================================================
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

// ============================================================================
// LOW STOCK MATERIALS CHECK
// ============================================================================
function checkLowStockMaterials() {
    // This would typically make an API call
    // For now, we'll check if there's a badge in the navbar
    const materialsLink = document.querySelector('a[href*="materials"]');
    if (materialsLink) {
        const badge = materialsLink.querySelector('.badge');
        if (badge && parseInt(badge.textContent) > 0) {
            showToast('Attenzione', `Ci sono ${badge.textContent} materiali in esaurimento!`, 'warning');
        }
    }
}

// ============================================================================
// TOAST NOTIFICATIONS
// ============================================================================
function showToast(title, message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');

    if (!toastContainer) {
        // Create toast container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }

    const toastHTML = `
        <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type}">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;

    const container = document.getElementById('toastContainer');
    container.insertAdjacentHTML('beforeend', toastHTML);

    const toastElement = container.lastElementChild;
    const toast = new bootstrap.Toast(toastElement);
    toast.show();

    // Remove toast after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// ============================================================================
// FILE UPLOAD HELPERS
// ============================================================================
function previewImage(input, previewContainer) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function(e) {
            const preview = document.createElement('div');
            preview.className = 'col-md-4 mb-2';
            preview.innerHTML = `
                <img src="${e.target.result}" class="img-fluid rounded" alt="Preview">
            `;
            previewContainer.appendChild(preview);
        };

        reader.readAsDataURL(input.files[0]);
    }
}

// ============================================================================
// VOICE RECORDING UTILITIES
// ============================================================================
class VoiceRecorder {
    constructor() {
        this.recorder = null;
        this.stream = null;
        this.audioBlob = null;
        this.startTime = null;
        this.timerInterval = null;
    }

    async start() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.recorder = RecordRTC(this.stream, {
                type: 'audio',
                mimeType: 'audio/webm',
                recorderType: RecordRTC.StereoAudioRecorder
            });

            this.recorder.startRecording();
            this.startTime = Date.now();

            return true;
        } catch (error) {
            console.error('Error starting recording:', error);
            showToast('Errore', 'Impossibile accedere al microfono', 'danger');
            return false;
        }
    }

    async stop() {
        return new Promise((resolve) => {
            if (!this.recorder) {
                resolve(null);
                return;
            }

            this.recorder.stopRecording(() => {
                this.audioBlob = this.recorder.getBlob();
                this.cleanup();
                resolve(this.audioBlob);
            });
        });
    }

    cleanup() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        this.recorder = null;
    }

    getElapsedTime() {
        if (!this.startTime) return 0;
        return Math.floor((Date.now() - this.startTime) / 1000);
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}

// ============================================================================
// API HELPERS
// ============================================================================
async function transcribeAudio(audioBlob, context = 'project') {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('context', context);

    try {
        const response = await fetch('/api/transcribe', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Transcription failed');
        }

        return await response.json();
    } catch (error) {
        console.error('Transcription error:', error);
        throw error;
    }
}

async function getCompatibleMaterials(printerType) {
    try {
        const response = await fetch(`/api/materials/compatible/${printerType}`);
        if (!response.ok) {
            throw new Error('Failed to fetch materials');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching materials:', error);
        return [];
    }
}

// ============================================================================
// FORM VALIDATION
// ============================================================================
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;

    // Bootstrap form validation
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return false;
    }

    return true;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================
function formatCurrency(amount) {
    return new Intl.NumberFormat('it-IT', {
        style: 'currency',
        currency: 'EUR'
    }).format(amount);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('it-IT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// ============================================================================
// PRICE CALCULATOR
// ============================================================================
class PriceCalculator {
    constructor(hourlyRate = 15, marginPercentage = 30) {
        this.hourlyRate = hourlyRate;
        this.marginPercentage = marginPercentage;
    }

    calculateMaterialCost(material, quantity) {
        if (!material) return 0;

        if (material.cost_per_kg) {
            // 3D printing - estimate 50g per piece
            return material.cost_per_kg * 0.05 * quantity;
        } else if (material.cost_per_sheet) {
            // Laser cutting
            return material.cost_per_sheet * quantity;
        }

        return 0;
    }

    calculateLaborCost(hours) {
        return hours * this.hourlyRate;
    }

    calculateFinalPrice(materialCost, laborCost) {
        const subtotal = materialCost + laborCost;
        return subtotal * (1 + this.marginPercentage / 100);
    }

    getBreakdown(materialCost, laborCost) {
        const subtotal = materialCost + laborCost;
        const margin = subtotal * (this.marginPercentage / 100);
        const final = subtotal + margin;

        return {
            material: materialCost,
            labor: laborCost,
            subtotal: subtotal,
            margin: margin,
            marginPercentage: this.marginPercentage,
            final: final
        };
    }
}

// ============================================================================
// LOCAL STORAGE HELPERS
// ============================================================================
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('Error saving to localStorage:', error);
        return false;
    }
}

function getFromLocalStorage(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (error) {
        console.error('Error reading from localStorage:', error);
        return null;
    }
}

function removeFromLocalStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.error('Error removing from localStorage:', error);
        return false;
    }
}

// ============================================================================
// EXPORT FUNCTIONS
// ============================================================================
window.AlkemyPrintHub = {
    VoiceRecorder,
    PriceCalculator,
    transcribeAudio,
    getCompatibleMaterials,
    showToast,
    validateForm,
    formatCurrency,
    formatDate,
    saveToLocalStorage,
    getFromLocalStorage,
    removeFromLocalStorage
};

// Log initialization
console.log('Alkemy Print Hub utilities loaded successfully');
