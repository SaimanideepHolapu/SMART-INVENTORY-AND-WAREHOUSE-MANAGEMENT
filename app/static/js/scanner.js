// QR and Barcode Scanner with Camera and Manual Fallback

let html5QrCode = null;
let isScanning = false;

// Web Audio API beep sound for scan success
function playBeep() {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(800, audioCtx.currentTime); // 800 Hz
        gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.15);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.15);
    } catch (e) {
        console.warn('Audio feedback not supported:', e);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('start-camera-btn');
    const stopBtn = document.getElementById('stop-camera-btn');
    const manualForm = document.getElementById('manual-search-form');
    const manualInput = document.getElementById('manual-sku-input');

    if (startBtn) {
        startBtn.addEventListener('click', startScanner);
    }

    if (stopBtn) {
        stopBtn.addEventListener('click', stopScanner);
    }

    if (manualForm) {
        manualForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const sku = manualInput.value.trim();
            if (sku) {
                lookupProduct(sku);
            }
        });
    }

    // Check if an initial SKU was passed via query string
    const initialSku = document.getElementById('scanner-initial-sku')?.value;
    if (initialSku) {
        lookupProduct(initialSku);
    }

    // QR / Barcode Image File Scanner
    const fileInput = document.getElementById('qr-file-input');
    const fileStatus = document.getElementById('file-scan-status');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            if (fileStatus) {
                fileStatus.innerHTML = '<span class="text-primary"><i class="fas fa-spinner fa-spin me-1"></i> Decoding QR / Barcode from image file...</span>';
            }

            if (!html5QrCode) {
                html5QrCode = new Html5Qrcode("qr-reader");
            }

            html5QrCode.scanFile(file, true)
                .then(decodedText => {
                    playBeep();
                    if (fileStatus) {
                        fileStatus.innerHTML = `<span class="text-success"><i class="fas fa-check-circle me-1"></i> Decoded code: <strong>${decodedText}</strong></span>`;
                    }
                    lookupProduct(decodedText);
                })
                .catch(err => {
                    console.warn("File QR scan failed:", err);
                    if (fileStatus) {
                        fileStatus.innerHTML = `<span class="text-danger"><i class="fas fa-exclamation-circle me-1"></i> No clear QR/Barcode found in this image. Please upload a clear photo or type the SKU manually.</span>`;
                    }
                });
        });
    }
});

function startScanner() {
    const readerDiv = document.getElementById('qr-reader');
    if (!readerDiv) return;

    if (!html5QrCode) {
        html5QrCode = new Html5Qrcode("qr-reader");
    }

    const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 }
    };

    html5QrCode.start(
        { facingMode: "environment" },
        config,
        onScanSuccess,
        onScanFailure
    ).then(() => {
        isScanning = true;
        document.getElementById('start-camera-btn').classList.add('d-none');
        document.getElementById('stop-camera-btn').classList.remove('d-none');
        document.getElementById('camera-status-text').innerHTML = '<span class="text-success"><i class="fas fa-video"></i> Camera active. Align QR or barcode within the box.</span>';
    }).catch(err => {
        console.error("Camera start error:", err);
        document.getElementById('camera-status-text').innerHTML = `<span class="text-danger"><i class="fas fa-exclamation-triangle"></i> Unable to access camera: ${err}. Please use manual search below.</span>`;
    });
}

function stopScanner() {
    if (html5QrCode && isScanning) {
        html5QrCode.stop().then(() => {
            isScanning = false;
            document.getElementById('start-camera-btn').classList.remove('d-none');
            document.getElementById('stop-camera-btn').classList.add('d-none');
            document.getElementById('camera-status-text').innerHTML = '<span class="text-muted"><i class="fas fa-camera"></i> Camera paused.</span>';
        }).catch(err => console.error("Error stopping camera:", err));
    }
}

function onScanSuccess(decodedText, decodedResult) {
    playBeep();
    // Stop scanning after a successful read to avoid repeated triggers
    stopScanner();
    lookupProduct(decodedText);
}

function onScanFailure(error) {
    // Normal frame-by-frame non-match, no need to log excessively
}

function lookupProduct(identifier) {
    const resultContainer = document.getElementById('scan-result-container');
    const statusText = document.getElementById('camera-status-text');

    resultContainer.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-muted mt-2 small">Searching database for identifier: <strong>${identifier}</strong>...</p>
        </div>
    `;

    fetch(`/api/lookup/${encodeURIComponent(identifier)}`)
        .then(res => {
            if (!res.ok) {
                return res.json().then(err => { throw new Error(err.error || 'Product not found'); });
            }
            return res.json();
        })
        .then(data => {
            if (data.success && data.product) {
                renderProductCard(data.product);
            }
        })
        .catch(err => {
            resultContainer.innerHTML = `
                <div class="alert alert-danger d-flex align-items-center mb-0">
                    <i class="fas fa-exclamation-circle fa-2x me-3"></i>
                    <div>
                        <h6 class="alert-heading mb-1">Product Not Found</h6>
                        <p class="mb-0 small">${err.message}</p>
                    </div>
                </div>
            `;
        });
}

function renderProductCard(p) {
    const container = document.getElementById('scan-result-container');
    let statusClass = 'badge-in-stock';
    if (p.status === 'LOW STOCK') statusClass = 'badge-low-stock';
    if (p.status === 'OUT OF STOCK') statusClass = 'badge-out-of-stock';

    let imageHtml = '';
    if (p.image_url) {
        imageHtml = `
            <div class="col-12 text-center">
                <img src="${p.image_url}" alt="${p.name}" class="img-fluid rounded border shadow-sm" style="max-height: 140px; object-fit: contain;">
            </div>
        `;
    }

    container.innerHTML = `
        <div class="card border-0 shadow-sm" style="border-radius: 12px; overflow: hidden;">
            <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center py-3">
                <div>
                    <span class="badge bg-primary me-2">${p.category}</span>
                    <strong class="h5 mb-0">${p.name}</strong>
                </div>
                <span class="${statusClass} px-3 py-1">${p.status}</span>
            </div>
            <div class="card-body">
                <div class="row g-3">
                    ${imageHtml}
                    <div class="col-md-6">
                        <div class="p-3 bg-light rounded">
                            <div class="text-muted small">SKU / Code</div>
                            <div class="font-monospace fw-bold fs-6 text-primary">${p.sku}</div>
                            <div class="text-muted small mt-2">Product Code: <code>${p.product_code}</code></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="p-3 bg-light rounded">
                            <div class="text-muted small">Current Available Stock</div>
                            <div class="fs-4 fw-bold ${p.stock_quantity <= p.minimum_stock ? 'text-danger' : 'text-success'}">
                                ${p.stock_quantity} <span class="small text-muted fw-normal">units</span>
                            </div>
                            <div class="text-muted small">Minimum Threshold: ${p.minimum_stock} units</div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="small text-muted"><i class="fas fa-map-marker-alt text-danger me-1"></i> Warehouse Location:</div>
                        <div class="fw-semibold">${p.location_full}</div>
                    </div>
                    <div class="col-md-6">
                        <div class="small text-muted"><i class="fas fa-truck text-secondary me-1"></i> Supplier:</div>
                        <div class="fw-semibold">${p.supplier} (${p.supplier_code})</div>
                    </div>
                </div>

                <hr class="my-3">

                <div class="d-flex flex-wrap gap-2 justify-content-end">
                    <a href="/products/${p.id}" class="btn btn-outline-secondary btn-sm">
                        <i class="fas fa-external-link-alt me-1"></i> View Full Details
                    </a>
                    <a href="/inventory/stock-in?product_id=${p.id}" class="btn btn-primary-wh btn-sm">
                        <i class="fas fa-arrow-down me-1"></i> Quick Stock In
                    </a>
                    <a href="/inventory/stock-out?product_id=${p.id}" class="btn btn-outline-danger btn-sm">
                        <i class="fas fa-arrow-up me-1"></i> Quick Stock Out
                    </a>
                </div>
            </div>
        </div>
    `;
}
