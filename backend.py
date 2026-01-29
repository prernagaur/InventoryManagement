from flask import request, jsonify, Blueprint
import json
import os
import qrcode
import io
import base64
import secrets

try:
    from PIL import Image
except ImportError:
    raise ImportError("Pillow is required. Install it using: pip install pillow")

backend_bp = Blueprint('backend', __name__, url_prefix='/api')

ORDERS_FILE = 'orders.json'
PRODUCTS_FILE = 'products.json'
WAREHOUSES_FILE = 'warehouses.json'
DELIVERIES_FILE = 'deliveries.json'

def load_data(filename):
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump([], f)
    with open(filename, 'r') as f:
        return json.load(f)

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)

def load_warehouses():
    return load_data(WAREHOUSES_FILE)

def save_warehouses(data):
    save_data(WAREHOUSES_FILE, data)

def load_deliveries():
    return load_data(DELIVERIES_FILE)

def save_deliveries(data):
    save_data(DELIVERIES_FILE, data)

@backend_bp.route('/orders', methods=['GET', 'POST'])
def orders():
    if request.method == 'GET':
        return jsonify(load_data(ORDERS_FILE))
    elif request.method == 'POST':
        orders = load_data(ORDERS_FILE)
        products = load_data(PRODUCTS_FILE)
        new_order = request.json
        product_name = new_order.get('product')
        order_qty = int(new_order.get('quantity', 1))

        product = next((p for p in products if p.get('name') == product_name), None)
        if not product:
            return jsonify({'error': 'Product not found'}), 400
        if int(product.get('quantity', 0)) < order_qty:
            return jsonify({'error': 'Insufficient product quantity'}), 400

        # Update product quantity
        product['quantity'] = int(product['quantity']) - order_qty
        save_data(PRODUCTS_FILE, products)

        # Create order
        new_order['id'] = (max([o['id'] for o in orders], default=0) + 1) if orders else 1
        orders.append(new_order)
        save_data(ORDERS_FILE, orders)

        # Create delivery with QR
        deliveries = load_deliveries()
        verification_code = secrets.token_hex(4).upper()
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(verification_code)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        if not hasattr(img, 'save'):
            img = img.get_image()
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        new_delivery = {
            "id": len(deliveries) + 1,
            "order_id": new_order["id"],
            "verification_code": verification_code,
            "qr_code": qr_code_base64,
            "status": "pending",
            "items": [{
                "name": new_order["product"],
                "quantity": new_order["quantity"]
            }]
        }
        deliveries.append(new_delivery)
        save_deliveries(deliveries)

        return jsonify({
            "order": new_order,
            "delivery": new_delivery
        }), 201

@backend_bp.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    orders = load_data(ORDERS_FILE)
    orders = [o for o in orders if o['id'] != order_id]
    save_data(ORDERS_FILE, orders)
    return '', 204

@backend_bp.route('/products', methods=['GET', 'POST'])
def products():
    if request.method == 'GET':
        return jsonify(load_data(PRODUCTS_FILE))
    elif request.method == 'POST':
        products = load_data(PRODUCTS_FILE)
        new_product = request.json
        new_product['id'] = (max([p['id'] for p in products], default=0) + 1) if products else 1
        products.append(new_product)
        save_data(PRODUCTS_FILE, products)
        return jsonify(new_product), 201

@backend_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    products = load_data(PRODUCTS_FILE)
    products = [p for p in products if p['id'] != product_id]
    save_data(PRODUCTS_FILE, products)
    return '', 204

@backend_bp.route('/statistics', methods=['GET'])
def statistics():
    orders = load_data(ORDERS_FILE)
    products = load_data(PRODUCTS_FILE)
    stats = {}
    for order in orders:
        name = order.get('product')
        stats[name] = stats.get(name, 0) + int(order.get('quantity', 1))
    return jsonify({
        'orders_per_product': stats,
        'products': products,
        'orders': orders
    })

@backend_bp.route('/warehouses', methods=['GET', 'POST', 'DELETE'])
def warehouses():
    if request.method == 'GET':
        return jsonify(load_warehouses())
    elif request.method == 'POST':
        warehouses = load_warehouses()
        new_warehouse = request.json
        new_warehouse['id'] = (max([w['id'] for w in warehouses], default=0) + 1) if warehouses else 1
        warehouses.append(new_warehouse)
        save_warehouses(warehouses)
        return jsonify(new_warehouse), 201
    elif request.method == 'DELETE':
        warehouses = load_warehouses()
        warehouse_id = request.json.get('id')
        warehouses = [w for w in warehouses if w['id'] != warehouse_id]
        save_warehouses(warehouses)
        return '', 204

@backend_bp.route('/deliveries/<verification_code>', methods=['GET'])
def get_delivery(verification_code):
    deliveries = load_deliveries()
    delivery = next((d for d in deliveries if d['verification_code'] == verification_code), None)
    if not delivery:
        return jsonify({'error': 'Delivery not found'}), 404
    return jsonify(delivery)

@backend_bp.route('/deliveries/<verification_code>/confirm', methods=['POST'])
def confirm_delivery(verification_code):
    deliveries = load_deliveries()
    delivery = next((d for d in deliveries if d['verification_code'] == verification_code), None)
    if not delivery:
        return jsonify({'error': 'Delivery not found'}), 404
    delivery['status'] = 'delivered'
    save_deliveries(deliveries)
    return jsonify({'message': 'Delivery confirmed successfully'}), 200
