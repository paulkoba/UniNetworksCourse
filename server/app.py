from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import psycopg2
from psycopg2 import pool, sql
import os
from datetime import datetime

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})  # Allow cross-origin requests from React

# Database connection parameters
db_config = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': os.environ.get("DB_PASSWORD"),
    'host': 'localhost'
}

connection_pool = pool.SimpleConnectionPool(1, 10, **db_config)

def get_db_connection():
    try:
        conn = connection_pool.getconn()
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error: Could not get connection from the pool. Details: {e}")
        return None
    
def release_db_connection(conn):
    connection_pool.putconn(conn)

@app.route('/api/hello', methods=['GET'])
def hello_world():
    return jsonify(message="Hello from Flask!")

def get_posts_int(conn):
    cur = conn.cursor()
    query = sql.SQL(
        """
SELECT json_agg(json_build_object(
    'id', p.id,
    'user_id', p.user_id,
    'author', u.username,
    'title', p.title,
    'content', p.content,
    'created_at', p.created_at,
    'updated_at', p.updated_at,
    'score', p.score
) ORDER BY p.score DESC ) 
FROM posts p
JOIN users u ON p.user_id = u.id;
"""
    )
    
    try:
        cur.execute(query)
        result = cur.fetchall()

        if result:
            return result
        else:
            return None
    except:
        return None
    finally:
        cur.close()

import json

def get_comments_json(conn, post_id):
    try:
        cursor = conn.cursor()
        # Fetch post details
        cursor.execute("SELECT p.id, p.user_id, p.title, p.content, p.created_at, p.updated_at, p.score, u.username FROM posts p INNER JOIN users u ON p.user_id = u.id WHERE p.id = %s", (post_id,))
        post = cursor.fetchone()
        
        # Fetch comments
        cursor.execute("""
            SELECT p.id, p.parent_comment_id, p.content, p.created_at, p.score, u.username 
            FROM comments p 
            JOIN users u ON p.user_id = u.id 
            WHERE p.post_id = %s
        """, (post_id,))

        response = cursor.fetchall()
        # Organize comments into a structured format
        comments_dict = {}
        for comment in response:
            comment_id, parent_comment_id, content, created_at, score, username = comment
            comments_dict[comment_id] = {
                "id": comment_id,
                "parent_id": parent_comment_id,
                "content": content,
                "username": username,
                "created_at": created_at.isoformat(),  # Assuming created_at is a datetime object
                "score": score,
                "replies": []
            }

        # Build the hierarchical structure for replies
        for comment in response:
            comment_id, parent_id, _, _, _, _ = comment
            if parent_id is not None:
                # Check if the parent_id exists in the comments_dict before accessing it
                if parent_id in comments_dict:
                    comments_dict[parent_id]["replies"].append(comments_dict[comment_id])
                else:
                    print(f"Warning: Parent ID {parent_id} not found in comments_dict.")

        result = {
            post_id: {
                "post": {
                    "id": post[0],
                    "title": post[2],
                    "body": post[3],
                    "author": post[7],
                    "created_at": post[4].isoformat(),  # Assuming created_at is a datetime object
                    "updated_at": post[5].isoformat(),  # Assuming created_at is a datetime object
                    "score": post[6],
                },
                "comments": [comment for comment in comments_dict.values() if comment["parent_id"] is None]
            }
        }

        return json.dumps(result, indent=4, sort_keys=True, default=str)  # Convert to JSON string

    except Exception as e:
        print(f"Error: {e}")
        return json.dumps({})  # Return an empty JSON object in case of error

def create_post(conn, user_id, title, content):
    cur = conn.cursor()
    query = sql.SQL(
        """
INSERT INTO posts (user_id, title, content, created_at, updated_at, score)
VALUES (%s, %s, %s, %s, %s, 0)
RETURNING id;
"""
    )
    
    try:
        # Using `datetime.now()` to capture the current timestamp for created_at and updated_at
        now = datetime.now()
        cur.execute(query, (user_id, title, content, now, now))
        
        # Fetch the ID of the newly created post
        post_id = cur.fetchone()[0]
        
        # Commit the transaction
        conn.commit()
        
        return post_id
    except Exception as e:
        print("Failed to create post:", e)
        # Roll back the transaction if there's an error
        conn.rollback()
        return None
    finally:
        cur.close()

def create_comment(conn, user_id, token, post_id, content, parent_comment_id=None):
    # Validate user token
    if not validate_user_token(conn, user_id, token):
        return json.dumps({"error": "Invalid token or user ID."}), 403
    
    try:
        cursor = conn.cursor()

        # Insert the new comment into the `comments` table
        cursor.execute("""
            INSERT INTO comments (post_id, user_id, content, parent_comment_id, created_at, score) 
            VALUES (%s, %s, %s, %s, NOW(), 0)
            RETURNING id;
        """, (post_id, user_id, content, parent_comment_id))
        
        # Retrieve the ID of the newly created comment
        comment_id = cursor.fetchone()[0]
        
        # Commit the transaction
        conn.commit()
        
        return json.dumps({
            "message": "Comment created successfully.",
            "comment_id": comment_id,
            "post_id": post_id,
            "user_id": user_id,
            "content": content,
            "parent_comment_id": parent_comment_id
        }), 201
    
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return json.dumps({"error": "Failed to create comment due to server error."}), 500



@app.route('/api/posts', methods=['GET'])
def get_posts():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Failed to connect to the database"}), 500

    try:
        posts = get_posts_int(conn)
        return posts
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        release_db_connection(conn)

def get_user_id(conn, username):
    cur = conn.cursor()
    query = sql.SQL("SELECT id FROM users WHERE username = %s")
    
    try:
        cur.execute(query, (username,))
        result = cur.fetchone()

        if result:
            return result[0]  # Return the user ID
        else:
            return None
    except:
        return None
    finally:
        cur.close()

def get_username(conn, user_id):
    cur = conn.cursor()
    query = sql.SQL("SELECT username FROM users WHERE id = %s")
    
    try:
        cur.execute(query, (user_id,))
        result = cur.fetchone()

        if result:
            return result[0]  # Return the user ID
        else:
            return None
    except:
        return None
    finally:
        cur.close()


def create_user(conn, username, password):
    cur = conn.cursor()
    # Use RETURNING clause to get the id of the newly inserted user
    query = sql.SQL("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id")

    try:
        # Execute the insert query and fetch the returned id
        cur.execute(query, (username, password))
        user_id = cur.fetchone()[0]  # Fetch the first row and get the id
        conn.commit()
        return user_id  # Return the user id
    except Exception as e:
        print(f"Error occurred: {e}")
        return None
    finally:
        cur.close()


def save_user_token(conn, user_id, token):
    cur = conn.cursor()
    query = sql.SQL("INSERT INTO sessions (user_id, token) VALUES (%s, %s)")
    
    try:
        cur.execute(query, (user_id, token,))
        result = cur.fetchone()

        if result:
            return result[0]  # Return the user ID
        else:
            return None
    except:
        return None
    finally:
        cur.close()

def validate_user_token(conn, user_id, token):
    cur = conn.cursor()
    query = sql.SQL("SELECT token FROM sessions WHERE user_id = %s AND token = %s")

    try:
        cur.execute(query, (user_id, token,))
        result = cur.fetchone()

        if result is not None:
            return True  # Token is valid
        else:
            return False  # Token is invalid
    except:
        return None
    finally:
        cur.close()

def delete_user_token(conn, token):
    cur = conn.cursor()
    query = sql.SQL("DELETE FROM sessions WHERE token = %s")

    try:
        cur.execute(query, (token,))
        # Optionally return the number of deleted rows to confirm deletion
        deleted_count = cur.rowcount
        return deleted_count > 0  # Returns True if a row was deleted
    except Exception as e:
        print(f"Error deleting token: {e}")
        return False  # Return False in case of error
    finally:
        cur.close()

def verify_password(conn, username, password):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        
        if result is None:
            return False

        stored_password_hash = result[0]
        print(stored_password_hash)
        return check_password_hash(stored_password_hash, password)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False
    finally:
        cursor.close()

def vote_comment(conn, user_id, token, comment_id, vote_type):
    if not validate_user_token(conn, user_id, token):
        return json.dumps({"error": "Invalid token or user ID."}), 403

    if vote_type not in ["upvote", "downvote"]:
        return json.dumps({"error": "Invalid vote type."}), 400
    
    try:
        cursor = conn.cursor()

        # Retrieve existing vote, if any
        cursor.execute("""
            SELECT vote_type FROM comment_votes
            WHERE user_id = %s AND comment_id = %s;
        """, (user_id, comment_id))
        existing_vote = cursor.fetchone()

        # Determine score adjustment based on current and new vote
        score_change = 0
        if existing_vote:
            # Delete the existing vote
            cursor.execute("""
                DELETE FROM comment_votes
                WHERE user_id = %s AND comment_id = %s;
            """, (user_id, comment_id))
            
            # Adjust score change based on existing vote
            if existing_vote[0] == "upvote":
                score_change = -1  # Removing an upvote
            else:
                score_change = 1   # Removing a downvote

            conn.commit()

            if existing_vote[0] == vote_type:
                cursor.execute("""
                    UPDATE comments SET score = score + %s
                    WHERE id = %s;
                """, (score_change, comment_id))

                return json.dumps({
                    "message": f"Comment {vote_type}d successfully.",
                    "comment_id": comment_id,
                    "new_score": score_change
                }), 200

        # Insert new vote
        score_change += 1 if vote_type == "upvote" else -1
        cursor.execute("""
            INSERT INTO comment_votes (user_id, comment_id, vote_type)
            VALUES (%s, %s, %s);
        """, (user_id, comment_id, vote_type))

        # Update comment score
        cursor.execute("""
            UPDATE comments SET score = score + %s
            WHERE id = %s;
        """, (score_change, comment_id))

        # Commit the transaction
        conn.commit()

        return json.dumps({
            "message": f"Comment {vote_type}d successfully.",
            "comment_id": comment_id,
            "new_score": score_change
        }), 200
    
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return json.dumps({"error": "Failed to process vote due to server error."}), 500

@app.route('/api/username/<int:user_id>', methods=['GET'])
def get_username_route(user_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Failed to connect to the database"}), 500

    try:
        username = get_username(conn, user_id)
        if username:
            return jsonify({"username": username}), 200
        else:
            return jsonify({"error": "User ID not found"}), 404
    except Exception as e:
        return jsonify({"error": e}), 404
    finally:
        release_db_connection(conn)

@app.route('/api/post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Failed to connect to the database"}), 500

    try:
        json = get_comments_json(conn, post_id)
        if json:
            return json, 200
        else:
            return jsonify({"error": "Something went wrong"}), 404
    except Exception as e:
        return jsonify({"error": e}), 404
    finally:
        release_db_connection(conn)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user_id = 0
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Check if the user already exists
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Failed to connect to the database"}), 500

    try:
        id = get_user_id(conn, username)
        if id is not None:
            return jsonify({"error": "Username already exists"}), 400
        
        user_id = create_user(conn, username, generate_password_hash(password))
        token = uuid.uuid4().hex
        save_user_token(conn, user_id, token)

        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        release_db_connection(conn)

    # Return the session token in the response

    response = make_response(jsonify({"username": username, "user_id": user_id, "token": token}), 200)
    response.set_cookie("token", token, domain="127.0.0.1")
    return response


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Check if the user exists and verify the password
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Failed to connect to the database"}), 500

    try:
        user_id = get_user_id(conn, username)
        if user_id is None:
            return jsonify({"error": "Invalid username"}), 401
        
        # Assuming you have a function to verify the password
        if not verify_password(conn, username, password):
            return jsonify({"error": "Invalid password"}), 401
        
        token = uuid.uuid4().hex
        save_user_token(conn, user_id, token)

        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        release_db_connection(conn)

    # Return the session token in the response
    response = make_response(jsonify({"username": username, "user_id": user_id, "token": token}), 200)
    response.set_cookie("token", token, domain="127.0.0.1")
    return response

@app.route('/api/logout', methods=['POST'])
def logout():
    token = request.cookies.get('token')

    if not token:
        return jsonify({"error": "No token provided"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Failed to connect to the database"}), 500

    try:
        delete_user_token(conn, token)
        conn.commit()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        release_db_connection(conn)

    # Clear the token cookie from the client
    response = make_response(jsonify({"message": "Logged out successfully"}), 200)
    response.set_cookie("token", "", expires=0)  # Set cookie to expire
    return response

@app.route('/api/comments', methods=['POST'])
def create_comment_route():
    # Extract data from the request
    token = request.json.get('token')
    post_id = request.json.get('post_id')
    user_id = request.json.get('user_id')
    content = request.json.get('content')
    parent_comment_id = request.json.get('parent_comment_id', None)  # Optional field
    print("Token:" + str(token) + ", post_id: " + str(post_id) +", user_id: " + str(user_id) + ", content: " + str(content) + ", parent_comment_id: " + str(parent_comment_id))
    # Ensure all required data is present
    if not token or not post_id or not user_id or not content:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Failed to connect to the database"}), 500

    try:
        result, status_code = create_comment(conn, user_id, token, post_id, content, parent_comment_id)
        # Commit the transaction
        conn.commit()
        
        # Return the result as a JSON response
        return jsonify(json.loads(result)), status_code
    
    except Exception as e:
        print(str(e))
        conn.rollback()  # Rollback in case of error
        return jsonify({"error": str(e)}), 500
    finally:
        release_db_connection(conn)

@app.route('/api/comment_vote', methods=['POST'])
def vote_comment_route():
    # Extract data from the request
    token = request.json.get('token')
    comment_id = request.json.get('comment_id')
    user_id = request.json.get('user_id')
    vote_type = request.json.get('vote_type')
    
    print("Token:" + str(token) + ", comment_id: " + str(comment_id) +", user_id: " + str(user_id) + ", vote_type: " + str(vote_type))
    
    if not token or not comment_id or not user_id or not vote_type:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Failed to connect to the database"}), 500

    try:
        print(1)
        # Call the `create_comment` function to insert the comment
        result, status_code = vote_comment(conn, user_id, token, comment_id, vote_type)
        # Commit the transaction
        conn.commit()
        
        # Return the result as a JSON response
        return jsonify(json.loads(result)), status_code
    
    except Exception as e:
        print(str(e))
        conn.rollback()  # Rollback in case of error
        return jsonify({"error": str(e)}), 500
    finally:
        release_db_connection(conn)


@app.route('/api/create_post', methods=['POST'])
def create_post_endpoint():
    data = request.json
    
    # Extract required fields from request data
    user_id = data.get("user_id")
    token = data.get("token")
    title = data.get("title")
    content = data.get("content")
    
    print("Token:" + str(token) + ", user_id: " + str(user_id) +", content: " + str(content) + ", title: " + str(title))
    
    if not token or not title or not user_id:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Failed to connect to the database"}), 500

    try:
        print(1)
        if not validate_user_token(conn, user_id, token):
            return json.dumps({"error": "Invalid token or user ID."}), 403
    
        # Call the `create_comment` function to insert the comment
        result, status_code = create_post(conn, user_id, title, content)
        # Commit the transaction
        conn.commit()
        
        # Return the result as a JSON response
        return jsonify(json.loads(result)), status_code
    
    except Exception as e:
        print(str(e))
        conn.rollback()  # Rollback in case of error
        return jsonify({"error": str(e)}), 500
    finally:
        release_db_connection(conn)

def vote_post(conn, user_id, token, post_id, vote_type):
    if not validate_user_token(conn, user_id, token):
        return json.dumps({"error": "Invalid token or user ID."}), 403

    if vote_type not in ["upvote", "downvote"]:
        return json.dumps({"error": "Invalid vote type."}), 400
    
    try:
        cursor = conn.cursor()

        # Retrieve existing vote, if any
        cursor.execute("""
            SELECT vote_type FROM post_votes
            WHERE user_id = %s AND post_id = %s;
        """, (user_id, post_id))
        existing_vote = cursor.fetchone()

        # Determine score adjustment based on current and new vote
        score_change = 0
        if existing_vote:
            # Delete the existing vote
            cursor.execute("""
                DELETE FROM post_votes
                WHERE user_id = %s AND post_id = %s;
            """, (user_id, post_id))
            
            # Adjust score change based on existing vote
            if existing_vote[0] == "upvote":
                score_change = -1  # Removing an upvote
            else:
                score_change = 1   # Removing a downvote

            conn.commit()

            if existing_vote[0] == vote_type:
                cursor.execute("""
                    UPDATE posts SET score = score + %s
                    WHERE id = %s;
                """, (score_change, post_id))

                return json.dumps({
                    "message": f"Post {vote_type}d successfully.",
                    "post_id": post_id,
                    "new_score": score_change
                }), 200

        # Insert new vote
        score_change += 1 if vote_type == "upvote" else -1
        cursor.execute("""
            INSERT INTO post_votes (user_id, post_id, vote_type)
            VALUES (%s, %s, %s);
        """, (user_id, post_id, vote_type))

        # Update post score
        cursor.execute("""
            UPDATE posts SET score = score + %s
            WHERE id = %s;
        """, (score_change, post_id))

        # Commit the transaction
        conn.commit()

        return json.dumps({
            "message": f"Post {vote_type}d successfully.",
            "post_id": post_id,
            "new_score": score_change
        }), 200
    
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        return json.dumps({"error": "Failed to process vote due to server error."}), 500

@app.route('/api/post_vote', methods=['POST'])
def vote_post_route():
    token = request.json.get('token')
    post_id = request.json.get('post_id')
    user_id = request.json.get('user_id')
    vote_type = request.json.get('vote_type')
    
    print("Token:" + str(token) + ", post_id: " + str(post_id) +", user_id: " + str(user_id) + ", vote_type: " + str(vote_type))
    
    if not token or not post_id or not user_id or not vote_type:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Failed to connect to the database"}), 500

    try:
        print(1)
        result, status_code = vote_post(conn, user_id, token, post_id, vote_type)
        conn.commit()

        return jsonify(json.loads(result)), status_code
    
    except Exception as e:
        print(str(e))
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        release_db_connection(conn)


if __name__ == '__main__':
    app.run(debug=True)

