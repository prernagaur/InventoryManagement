from flask import Blueprint, jsonify, request, render_template, Flask
import heapq
from geopy.distance import geodesic

# Initialize Flask app
app = Flask(__name__)

# Blueprint for pathfinder
pathfinder_bp = Blueprint('pathfinder', __name__, template_folder='templates')

# Remove pre-setted warehouse locations
warehouses = []

# Heuristic function for A* (straight-line distance)
def heuristic(a, b):
    return geodesic(a, b).kilometers

# A* Algorithm to find the shortest path between two points (customer to warehouse)
def a_star(start, goal, graph):
    open_list = []
    heapq.heappush(open_list, (0, tuple(start)))  # Start is a tuple to use in sets/maps
    g_score = {tuple(start): 0}
    came_from = {tuple(start): None}

    while open_list:
        current_f_score, current_node_tuple = heapq.heappop(open_list)
        current_node = list(current_node_tuple)

        if current_node == goal:
            # Reconstruct path
            path = []
            curr_tuple = tuple(current_node)
            while curr_tuple in came_from:
                path.append(list(curr_tuple))
                curr_tuple = came_from[curr_tuple]
            path.append(start)
            return path[::-1]  # Return the path in the correct order

        # Check neighbors (other warehouse locations)
        for neighbor in graph[current_node]:
            neighbor_location = neighbor["location"]
            dist = geodesic(current_node, neighbor_location).kilometers
            tentative_g_score = g_score.get(tuple(current_node), float('inf')) + dist

            if tuple(neighbor_location) not in g_score or tentative_g_score < g_score.get(tuple(neighbor_location), float('inf')):
                came_from[tuple(neighbor_location)] = tuple(current_node)
                g_score[tuple(neighbor_location)] = tentative_g_score
                f_score = tentative_g_score + heuristic(neighbor_location, goal)
                heapq.heappush(open_list, (f_score, tuple(neighbor_location)))

    return None  # If no path is found

# Route to serve the map page
@pathfinder_bp.route('/map')
def map_page():
    return render_template('delivery_route_map.html')  # This will load your map page

# Route to handle path calculation
@pathfinder_bp.route('/calculate_path', methods=['POST'])
def calculate_path():
    data = request.get_json()
    warehouse_location = data.get('warehouse_location')
    delivery_location = data.get('delivery_location')

    if not warehouse_location or not delivery_location:
        return jsonify([])  # Invalid input

    # Define the graph with only two nodes: warehouse and delivery location
    graph = {
        tuple(warehouse_location): [{"name": "Delivery", "location": delivery_location}],
        tuple(delivery_location): []
    }

    # Calculate the A* path
    path = a_star(warehouse_location, delivery_location, graph)

    if path:
        return jsonify(path)
    else:
        return jsonify([])

# Register blueprint
app.register_blueprint(pathfinder_bp)

# --- Delivery logic merged from tim.py ---

def make_delivery(data):
    """Helper function to create a delivery."""
    # delivery creation logic
    # delivery = DeliveryModel(**data)
    # db.session.add(delivery)
    # db.session.commit()
    # return delivery
    pass  # Replace with actual logic

@app.route('/api/deliveries', methods=['POST'])
def create_delivery():
    """API endpoint to create a new delivery."""
    data = request.json
    delivery = make_delivery(data)
    # existing code to return response
    return jsonify({'status': 'success'})  # Adjust as needed

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/delivery_confirmation')
def delivery_confirmation():
    return render_template('delivery_confirmation.html')

# Example usage elsewhere in your code:
# delivery = make_delivery(delivery_data)
# return jsonify({'order': new_order, 'delivery': delivery}), 201
