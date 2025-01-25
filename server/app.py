#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response,jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

 #GET all restaurants
class Restaurants(Resource):
    def get(self):
        # Query all restaurants from the database
        restaurants = Restaurant.query.all()

        # Convert each restaurant into a dictionary using the to_dict method
         # Convert each restaurant into a dictionary without restaurant_pizzas
        response_dict_list = [restaurant.to_dict(include_relationships=False) for restaurant in restaurants]

        # Return the response as JSON with a 200 OK status
        response = make_response(jsonify(response_dict_list), 200)
        return response

api.add_resource(Restaurants, '/restaurants')

# GET and DELETE one restaurant by ID
class RestaurantByID(Resource):
    def get(self, id):
        # Use SQLAlchemy 2.0 session.get() instead of query.get(id)
        restaurant = db.session.get(Restaurant, id)

        # If doesn't exist, return a 404 message
        if not restaurant:
            return make_response({"error": "Restaurant not found"}, 404)


        # Convert the restaurant to a dictionary and return as JSON
        response_dict = restaurant.to_dict()
        response = make_response(response_dict, 200)
        return response
    
    def delete(self, id):
       # Use SQLAlchemy 2.0 session.get() instead of query.get(id)
        restaurant = db.session.get(Restaurant, id)

        # If the restaurant doesn't exist, return a 404 error with the JSON message
        if not restaurant:
            return make_response({"error": "Restaurant not found"}, 404)

        # Delete the restaurant (cascades will automatically delete related RestaurantPizza entries)
        db.session.delete(restaurant)
        db.session.commit()

        # Return an empty response with a 204
        response = make_response("", 204)
        return response
    
api.add_resource(RestaurantByID, '/restaurants/<int:id>')

#GET all pizzas
class Pizzas(Resource):
    def get(self):
        # Query all pizzas 
        pizzas = Pizza.query.all()

        # Convert each pizza into a dictionary 
        response_dict_list = [pizza.to_dict() for pizza in pizzas]

        # Return the response as JSON with a 200 response
        response = make_response(response_dict_list, 200)
        return response

api.add_resource(Pizzas, '/pizzas')

#POST Restaurant-Pizza 
class RestaurantPizzas(Resource):

    def post(self):
        # Parse the JSON data from the request body
        data = request.get_json()

        # Validate the required fields
        price = data.get('price')
        pizza_id = data.get('pizza_id')
        restaurant_id = data.get('restaurant_id')

       # Ensure all required fields exist
        if price is None or pizza_id is None or restaurant_id is None:
           return make_response({"errors": ["Missing required fields"]}, 400)
        
        # Validate price range
        if not (1 <= price <= 30):
           return make_response({"errors": ["validation errors"]}, 400)
       
        try:
            # Check if the associated Pizza exists
            pizza = db.session.get(Pizza, pizza_id)
            if not pizza:
                return make_response({"errors": ["Pizza not found"]}, 404)

            # Check if the associated Restaurant exists
            restaurant = db.session.get(Restaurant, restaurant_id)
            if not restaurant:
                return make_response({"errors": ["Restaurant not found"]}, 404)

            # Create the new RestaurantPizza
            restaurant_pizza = RestaurantPizza(
                price=price,
                pizza_id=pizza_id,
                restaurant_id=restaurant_id
            )

            # Add to the session and commit
            db.session.add(restaurant_pizza)
            db.session.commit()

            # Serialize the response data
            response_dict = {
                "id": restaurant_pizza.id,
                "price": restaurant_pizza.price,
                "pizza_id": restaurant_pizza.pizza_id,
                "restaurant_id": restaurant_pizza.restaurant_id,
                "pizza": {
                    "id": pizza.id,
                    "name": pizza.name,
                    "ingredients": pizza.ingredients
                },
                "restaurant": {
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "address": restaurant.address
                }
            }

            # Return the response with status 201 (Created)
            return make_response(response_dict, 201)

        except ValueError as e:
            # Handle validation errors such as price not being within a valid range
            return make_response({"errors": ["validation errors"]}, 400)

api.add_resource(RestaurantPizzas, '/restaurant_pizzas')

if __name__ == "__main__":
    app.run(port=5555, debug=True)
