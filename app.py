from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
import subprocess
import time

app = Flask(__name__)

# MongoDB Atlas connection
client = MongoClient("YOUR_MONGO_STRING")
db = client['movies']
movies_collection = db['movies']

# Cooldown time (in seconds)
REFRESH_COOLDOWN = 3600
last_refresh_time = 0  # Timestamp of the last refresh

@app.route('/')
def index():
    refresh()  # Optional: refresh on page load
    movies = list(movies_collection.find({}, {"_id": 0}))  # Load all movies
    return render_template('index.html', movies=movies)

@app.route('/refresh', methods=['GET'])
def refresh():
    global last_refresh_time
    current_time = time.time()

    # Check if cooldown period has passed
    if current_time - last_refresh_time < REFRESH_COOLDOWN:
        time_remaining = REFRESH_COOLDOWN - (current_time - last_refresh_time)
        return jsonify(success=False, error=f"Please wait {int(time_remaining)} seconds before refreshing again.")

    try:
        # Run your Scrapy spider to fetch new movie data
        subprocess.run(["python", "main.py"], check=True)

        # Update the last refresh time to the current time
        last_refresh_time = current_time

        return jsonify(success=True)
    except subprocess.CalledProcessError:
        return jsonify(success=False, error="Failed to run Scrapy spider"), 500

@app.route('/update_notification', methods=['GET'])
def update_notification():
    """Endpoint to check for updates."""
    # Add logic to check update conditions if required.
    return jsonify(updated=True)

@app.route('/search', methods=['GET'])
def search():
    """Search for movies by name and return the results rendered on the webpage."""
    query = request.args.get('query', '').lower()
    mongo_query = {"Name": {"$regex": query, "$options": "i"}} if query else {}
    movies = list(movies_collection.find(mongo_query))
    
    return render_template('search_results.html', movies=movies, query=query)


@app.route('/movies', methods=['GET'])
def get_movies():
    """Paginated endpoint to fetch movies."""
    try:
        page = int(request.args.get('page', 1))  # Default to page 1
        size = int(request.args.get('size', 10))  # Default page size is 10

        # Fetch movies with pagination
        movies = list(movies_collection.find({}, {"_id": 0})
                      .skip((page - 1) * size)
                      .limit(size)
                      .sort([("_id", -1)]))
        
        return jsonify(movies=movies)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/about', methods=['GET'])
def about():
    
    return render_template('about.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
