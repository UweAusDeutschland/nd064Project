import sqlite3
import logging
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

db_connection_cont = 0
# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global db_connection_cont
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    db_connection_cont += 1
    return connection

# Close a db connection
def close_db_connection(connection):
    connection.close()

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    close_db_connection(connection)
    return post

# count number of elements
def count_rows(table_name):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        return count
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        close_db_connection(conn)

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    close_db_connection(connection)
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.error("404: Tried to fetch an unknown post: " + str(post_id))
      return render_template('404.html'), 404
    else:
      app.logger.info("Received post with id: " + str(post_id) + 
                   " with headline " + str(post['title']))
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info("About us is called.")
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            close_db_connection(connection)
            app.logger.info("New article posted with headline: " + str(title))
            return redirect(url_for('index'))

    return render_template('create.html')

#Entpoint for health check
@app.route('/healtz') 
def healthz():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
        )
    return response

#metrics endpoint returning the db connections and the number of posts in the database.
@app.route('/metrics')
def metrics():
    post_count = count_rows("posts")
    response = app.response_class(
            response=json.dumps({"db_connection_count":db_connection_cont, "post_count": post_count}),
            status=200,
            mimetype='application/json'
        )
    return response

# Custom filter to allow only INFO level messages
class InfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.INFO
    

# start the application on port 3111
if __name__ == "__main__":
#   logging.basicConfig(
#       stream=sys.stdout,
#       format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
#       datefmt='%Y-%m-%d %H:%M:%S',
#       level=logging.DEBUG)
       # Get root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create formatters and handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    # STDOUT handler for INFO messages
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)
    stdout_handler.addFilter(InfoFilter())

    # STDERR handler for ERROR messages
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)
    app.run(host='0.0.0.0', port='3111')
