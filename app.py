from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()
ATLAS_STRING = os.getenv('ATLAS_STRING')

app = Flask(__name__)
CORS(app, supports_credentials=True)

client = MongoClient(ATLAS_STRING)
db = client["todo_db"]
users = db["users"]  # Single collection for users & their todos

try:
    # Ping MongoDB to check if the connection is successful
    client.db.command("ping")
    print("Successfully connected to MongoDB Atlas!")
except ConnectionError as e:
    print("Failed to connect to MongoDB Atlas:", e)
    # You can also raise an exception or handle it as needed
    raise Exception("Could not connect to MongoDB Atlas. Please check your connection.")

# Sign Up (Initialize user with an empty todo list)
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    if users.find_one({"useremail": data["useremail"]}):
        return jsonify({"error": "User already exists"}), 400
    user_data = {
        "username": data["username"],
        "useremail": data["useremail"],
        "password": data["password"],
        "todos": []  # Empty todo list
    }
    users.insert_one(user_data)
    return jsonify({"message": "User registered"}), 201

# Login (Return user data)
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = users.find_one({"useremail": data["useremail"]})
    if user:
        user["_id"] = str(user["_id"])  # Convert Mongo ObjectId to string
        return jsonify(user)
    return jsonify({"error": "Invalid credentials"}), 400

# Get all todos of a user
@app.route("/todos/<username>", methods=["GET"])
def get_todos(username):
    user = users.find_one({"username": username})
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user["todos"])

@app.route("/profile/<username>", methods=["GET"])
def get_user(username):
    user = users.find_one({"username": username})
    if not user:
        return jsonify({"error": "User not found"}), 404
    user['_id'] = str(user['_id'])
    return jsonify(user)

# Add a new todo
@app.route("/todos/<username>", methods=["POST"])
def add_todo(username):
    data = request.json
    new_todo = {
        "id": str(ObjectId()),  # Convert ObjectId to string
        "task": data["task"],
        "completed": False
    }
    users.update_one({"username": username}, {"$push": {"todos": new_todo}})
    return jsonify({"message": "Todo added", "todo": new_todo})

# Toggle (strike-through) a todo
@app.route("/todos/<username>/<todo_id>", methods=["PUT"])
def toggle_todo(username, todo_id):
    user = users.find_one({"username": username})
    if not user:
        return jsonify({"error": "User not found"}), 404

    updated_todos = []
    for todo in user["todos"]:
        if todo["id"] == todo_id:  # Match string ID
            todo["completed"] = not todo["completed"]
        updated_todos.append(todo)
    
    users.update_one({"username": username}, {"$set": {"todos": updated_todos}})
    return jsonify({"message": "Todo updated"})

# Delete a todo
@app.route("/todos/<username>/<todo_id>", methods=["DELETE"])
def delete_todo(username, todo_id):
    users.update_one({"username": username}, {"$pull": {"todos": {"id": todo_id}}})
    return jsonify({"message": "Todo deleted"})

@app.route('/upload/<username>', methods=['POST'])
def upload_file(username):
    data = request.json
    file_base64 = data['file']
    users.update_one({"username": username}, {"$set": {"profile_pic": file_base64}})
    user = users.find_one({'username':username})
    return jsonify(user['profile_pic']) , 200




if __name__ == "__main__":
    app.run(debug=True)
