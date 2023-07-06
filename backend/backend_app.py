import datetime
import json
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes
# Initialize the limiter
# limiter = Limiter(app, key_func=get_remote_address)


POSTS = "posts.json"


def read_posts_from_file():
    """Read posts from the JSON file.
        If the file doesn't exist, create an empty file and return an empty list."""
    posts = []
    if os.path.exists(POSTS):
        try:
            with open(POSTS, "r") as file:
                posts = json.load(file)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading posts from file: {e}")
    else:
        # Create an empty file if it doesn't exist
        write_posts_to_file(posts)
    return posts


def write_posts_to_file(posts):
    """Write posts to the JSON file."""
    try:
        with open(POSTS, 'w') as file:
            json.dump(posts, file, indent=4)
    except IOError as e:
        print(f"Error writing posts to file: {e}")


def validate_posts(post):
    """Validate the fields of a post."""
    if "title" not in post or len(post['title']) == 0:
        return "title is missing"
    elif "content" not in post or len(post['content']) == 0:
        return "content is missing"
    elif "author" not in post or len(post['author']) == 0:
        return "author is missing"
    else:
        return True


def sorting_posts(posts, field, direction):
    """Sort the posts based on the given field and direction."""
    if field not in ["title", "content", "author", "date"] or direction not in ["asc", "desc"]:
        return None
    elif field == "date":
        sorted_posts = sorted(posts, key=lambda x: datetime.datetime.strptime(x['date'], '%Y-%m-%d'),
                              reverse=(direction == 'desc'))
    else:
        sorted_posts = sorted(posts, key=lambda post: post[field], reverse=(direction == 'desc'))
    return sorted_posts


@app.route('/api/posts', methods=['POST', 'GET'])
# @limiter.limit("12/minute")  # Limit to 10 requests per minute
def handle_post():
    """Handle POST and GET requests for the '/api/posts' endpoint."""
    posts = read_posts_from_file()
    if request.method == 'POST':
        post = request.get_json()
        valid_post = validate_posts(post)
        if valid_post != True:
            return jsonify({"Error": valid_post}), 400
        if len(posts) == 0:
            post_id = 1
        else:
            post_id = int(max(post['id'] for post in posts) + 1)
        formatted_date = str(datetime.date.today().strftime("%Y-%m-%d"))
        post = {'id': post_id,
                'title': post['title'],
                'content': post['content'],
                'author': post['author'],
                'comments': [],
                'date': formatted_date,
                'likes': 0
                }
        posts.append(post)
        write_posts_to_file(posts)
        return jsonify(post), 201
    elif request.method == 'GET':
        page = request.args.get('page', default=1, type=int)
        limit = request.args.get('limit', default=10, type=int)
        # Calculate the starting and ending indices based on the page and limit
        start_index = (page - 1) * limit
        end_index = start_index + limit
        # Apply sorting if provided
        sort = request.args.get('sort')
        direction = request.args.get('direction')
        if sort and direction:
            sorted_post = sorting_posts(posts, sort, direction)
            if sorted_post is None:
                return jsonify({"Error": "Invalid sort field"}), 400
        else:
            sorted_post = posts
        paginated_posts = list(sorted_post)[start_index:end_index]
        return jsonify(paginated_posts)


def find_post_by_id(post_id):
    """Find a post in the posts list by its ID."""
    posts = read_posts_from_file()
    return next((post for post in posts if post['id'] == post_id), None)


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Delete a post by its ID."""
    posts = read_posts_from_file()
    post = find_post_by_id(post_id)
    if post is None:
        return jsonify({"Error": "No such post"}), 404
    post_index = posts.index(post)
    del posts[post_index]
    write_posts_to_file(posts)
    return jsonify({"message": f"Post with id {post_id} has been deleted successfully."}), 200


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    """Update a post by its ID."""
    new_post = request.get_json()
    post = find_post_by_id(post_id)
    posts = read_posts_from_file()
    post_index = posts.index(post)
    if post is None:
        return jsonify({"Error": "No such post"}), 404
    post['title'] = new_post.get('title', post['title'])
    post['content'] = new_post.get('content', post['content'])
    post['author'] = new_post.get('author', post['author'])
    if "date" in new_post:
        # Convert input date to datetime object
        date_obj = datetime.datetime.strptime(new_post["date"], "%d-%m-%Y")
        # Format date as a string in the desired format
        output_date = date_obj.strftime("%Y-%m-%d")
        post['date'] = output_date
    posts[post_index] = post
    write_posts_to_file(posts)
    return jsonify({
        "id": f"{post['id']}",
        "title": f"{post['title']}",
        "content": f"{post['content']}",
        "author": f"{post['author']}",
        "date": f"{post['date']}",
        "likes": f"{int(post['likes'])}"
    }), 200


def filter_posts(posts, search_query):
    """Filter posts based on a search query."""
    if not search_query:
        return posts
    filtered_posts = []
    for post in posts:
        title = post['title'].lower()
        content = post['content'].lower()
        author = post['author'].lower()
        date = datetime.datetime.strptime(post['date'], '%Y-%m-%d').date().strftime('%B %d, %Y')
        if search_query.lower() in title or search_query.lower() in content or search_query.lower() in author or search_query in date:
            filtered_posts.append(post)
    return filtered_posts


@app.route('/api/posts/search', methods=['GET'])
def search_post():
    """Search posts based on query parameters."""
    posts = read_posts_from_file()
    title = request.args.get('title')
    content = request.args.get('content')
    author = request.args.get('author')
    date = request.args.get('date')
    search_query = request.args.get('q')
    field = request.args.get('sort')
    direction = request.args.get('direction')
    found_posts = []
    if search_query:
        filtered_posts = filter_posts(posts, search_query)
        sorted_posts = sorting_posts(filtered_posts, field, direction)
        return jsonify(sorted_posts)
    if title:
        found_posts = list(post for post in posts if title in post['title'])
    if content:
        found_posts = list(post for post in posts if content in post['content'])
    if author:
        found_posts = list(post for post in posts if author in post['author'])
    if date:
        found_posts = list(post for post in posts if date in post['date'])

    return jsonify(found_posts)


@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    """Add a comment to a post by its ID."""
    post = find_post_by_id(post_id)
    posts = read_posts_from_file()
    post_index = posts.index(post)
    if post is None:
        return jsonify({"Error": "No such post"}), 404
    comment = request.get_json()
    comment_id = max(comment['id'] for comment in post['comments']) + 1 if post['comments'] else 1
    comment['id'] = comment_id
    comment['likes'] = 0
    post['comments'].append(comment)
    posts[post_index] = post
    write_posts_to_file(posts)
    return jsonify(comment), 201


@app.route('/api/posts/<int:post_id>/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(post_id, comment_id):
    """Delete a comment from a post by their IDs."""
    posts = read_posts_from_file()
    post = find_post_by_id(post_id)
    post_index = posts.index(post)
    if post is None:
        return jsonify({"Error": "No such post"}), 404
    comment = next((comment for comment in post['comments'] if comment['id'] == comment_id), None)
    if comment is None:
        return jsonify({"Error": "No such comment"}), 404
    post['comments'].remove(comment)
    posts[post_index] = post
    write_posts_to_file(posts)
    return jsonify({"message": f"Comment with id {comment_id} has been deleted successfully."}), 200


@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
def update_likes(post_id):
    posts = read_posts_from_file()
    post = find_post_by_id(post_id)
    post_index = posts.index(post)
    post['likes'] = int(post['likes'] + 1)
    posts[post_index] = post
    write_posts_to_file(posts)
    return jsonify({"message": f"Post liked +1"}), 200


@app.route('/api/posts/<int:post_id>/comments/<int:comment_id>/like', methods=['POST'])
def update_comments_likes(post_id, comment_id):
    posts = read_posts_from_file()
    post = find_post_by_id(post_id)
    post_index = posts.index(post)
    comment = next((comment for comment in post['comments'] if comment['id'] == comment_id), None)
    comment['likes'] = int(comment['likes'] + 1)
    posts[post_index] = post
    write_posts_to_file(posts)
    return jsonify({"message": f"Post liked +1"}), 200



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
