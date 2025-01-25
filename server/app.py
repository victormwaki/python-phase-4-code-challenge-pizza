#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, jsonify,make_response
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


# --- RESTful Resources ---

class Restaurants(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        #serialize to json format 
        response = [restaurant.to_dict(only=("id", "name", "address")) for restaurant in restaurants]
        return make_response(jsonify(response), 200)

    def post(self):
        data = request.get_json()
        try:
            new_restaurant = Restaurant(name=data["name"], address=data["address"])
            db.session.add(new_restaurant)
            db.session.commit()
            return jsonify(new_restaurant.to_dict()), 201
        except KeyError:
            return {"error": "Invalid data"}, 400


class RestaurantDetail(Resource):
    def get(self, restaurant_id):
        restaurant = Restaurant.query.get(restaurant_id)
        if restaurant:
            return jsonify(restaurant.to_dict())
        return {"error": "Restaurant not found"}, 404

    def delete(self, restaurant_id):
        # Find the restaurant by ID
        restaurant = Restaurant.query.get(restaurant_id)
        
        if restaurant:
            try:
                # Delete associated RestaurantPizzas
                RestaurantPizza.query.filter_by(restaurant_id=restaurant_id).delete()
                
                # Delete the restaurant itself
                db.session.delete(restaurant)
                db.session.commit()
                
                # Return success message
                return {"message": "Restaurant deleted"}, 204
            except Exception as e:
                # Handle errors and rollback session
                db.session.rollback()
                return {"error": str(e)}, 500

        # Return error response if restaurant is not found
        return {"error": "Restaurant not found"}, 404


class Pizzas(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        response = [pizza.to_dict(only=("id", "ingredients", "name")) for pizza in pizzas]
        return make_response(jsonify(response), 200)
    
        #return jsonify([pizza.to_dict() for pizza in pizzas])

    def post(self):
        data = request.get_json()
        try:
            new_pizza = Pizza(name=data["name"], ingredients=data["ingredients"])
            db.session.add(new_pizza)
            db.session.commit()
            return jsonify(new_pizza.to_dict()), 201
        except KeyError:
            return {"error": "Invalid data"}, 400


class RestaurantPizzas(Resource):
    def post(self):
        data = request.get_json()

        try:
            # Validate input data
            price = data.get("price")
            pizza_id = data.get("pizza_id")
            restaurant_id = data.get("restaurant_id")

            if not all([price, pizza_id, restaurant_id]):
                raise ValueError("Missing required fields: 'price', 'pizza_id', or 'restaurant_id'")

            # Validate price range
            if price < 1 or price > 30:
                raise ValueError("Price must be between 1 and 30")

            # Check if pizza and restaurant exist
            pizza = Pizza.query.get(pizza_id)
            restaurant = Restaurant.query.get(restaurant_id)

            if not pizza:
                raise ValueError("Pizza not found")
            if not restaurant:
                raise ValueError("Restaurant not found")

            # Create new RestaurantPizza
            new_restaurant_pizza = RestaurantPizza(
                price=price,
                pizza_id=pizza_id,
                restaurant_id=restaurant_id,
            )

            db.session.add(new_restaurant_pizza)
            db.session.commit()

            # Return created RestaurantPizza with related data
            response_data = {
                "id": new_restaurant_pizza.id,
                "price": new_restaurant_pizza.price,
                "pizza_id": pizza.id,
                "restaurant_id": restaurant.id,
                "pizza": pizza.to_dict(),
                "restaurant": restaurant.to_dict(),
            }
            return response_data, 201

        except ValueError as ve:
            # Handle validation errors
            return {"errors": ["validation errors"]}, 400

        except Exception as e:
            # Handle other exceptions
            db.session.rollback()
            return {"error": str(e)}, 500


class RestaurantPizzaList(Resource):
    def get(self, restaurant_id):
        restaurant = Restaurant.query.get(restaurant_id)
        if restaurant:
            return jsonify([pizza.to_dict() for pizza in restaurant.pizzas])
        return {"error": "Restaurant not found"}, 404


# --- Registering Routes ---

api.add_resource(Restaurants, "/restaurants")
api.add_resource(RestaurantDetail, "/restaurants/<int:restaurant_id>")
api.add_resource(Pizzas, "/pizzas")
api.add_resource(RestaurantPizzas, "/restaurant_pizzas")
api.add_resource(RestaurantPizzaList, "/restaurants/<int:restaurant_id>/pizzas")


if __name__ == "__main__":
    app.run(port=5555, debug=True)
