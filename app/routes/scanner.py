from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from app.models import Product

scanner_bp = Blueprint('scanner', __name__)

@scanner_bp.route('/scanner')
@login_required
def index():
    initial_sku = request.args.get('sku', '').strip()
    return render_template('scanner/index.html', initial_sku=initial_sku)


@scanner_bp.route('/api/lookup/<path:identifier>')
@login_required
def lookup(identifier):
    """
    Looks up a product by SKU, product_code, or exact string match.
    Used by the camera scanner and the manual barcode search.
    """
    clean_id = identifier.strip().upper()
    product = Product.query.filter(
        (Product.sku.ilike(clean_id)) |
        (Product.product_code.ilike(clean_id)) |
        (Product.qr_code.ilike(clean_id))
    ).first()

    if not product:
        return jsonify({'success': False, 'error': f"No product found matching identifier '{identifier}'."}), 404

    return jsonify({
        'success': True,
        'product': product.to_dict()
    })
