// Function that runs once the window is fully loaded
window.onload = function() {
    var savedBaseUrl = localStorage.getItem('apiBaseUrl');
    if (savedBaseUrl) {
        document.getElementById('api-base-url').value = savedBaseUrl;
        loadPosts();
    }
};

function loadPosts(isSearch = false) {
    var baseUrl = document.getElementById('api-base-url').value;
    var sortField = document.getElementById('sort-field').value;
    var sortDirection = document.getElementById('sort-direction').value;
    var url = baseUrl + '/posts?sort=' + sortField + '&direction=' + sortDirection;

    // Check if it's a search request
    if (isSearch) {
        var query = document.getElementById('search-input').value.trim();
        if (query !== '') {
            url = baseUrl + '/posts/search?q=' + encodeURIComponent(query) + '&sort=' + sortField + '&direction=' +
            sortDirection;
        }
    }

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const postContainer = document.getElementById('post-container');
            postContainer.innerHTML = '';
            data.forEach(post => {
                const postDiv = createPostElement(post);
                postContainer.appendChild(postDiv);
            });
        })
        .catch(error => console.error('Error:', error));
}

function createPostElement(post) {
    const postDiv = document.createElement('div');
    postDiv.className = 'post';
    postDiv.id = `postDiv-${post.id}`;
    postDiv.dataset.post = JSON.stringify(post);
    postDiv.innerHTML = `<h2>${post.title}</h2>
         <p>${post.content}</p>
         <p><strong>Author:</strong> ${post.author}</p>
         <p><strong>Date:</strong> ${post.date}</p>
         <p><strong>Comments:</strong> ${post.comments?.length ?? 0}</p>
         <p class="likes">Likes: ${post.likes}</p>
         <button class="post-like-button" onclick="likePost(${post.id})">Like</button>`;

    const deleteButton = document.createElement('button');
    deleteButton.innerText = 'Delete';
    deleteButton.addEventListener('click', () => deletePost(post.id));
    postDiv.appendChild(deleteButton);

    const commentButton = document.createElement('button');
    commentButton.innerText = 'Comment';
    commentButton.addEventListener('click', () => addComment(post.id));
    postDiv.appendChild(commentButton);

    const updateButton = document.createElement('button');
    updateButton.innerText = 'Update';
    updateButton.addEventListener('click', () => updatePost(post.id));
    postDiv.appendChild(updateButton);

    const commentSection = document.createElement('div');
    commentSection.id = `comment-section-${post.id}`;
    commentSection.className = 'comment-section';
    post.comments?.forEach(comment => {
        const commentDiv = document.createElement('div');
        commentDiv.className = 'comment';
        commentDiv.innerHTML = `<p class="likes">Likes: ${comment.likes}</p><p>${comment.content}</p><button
        class="comment-like-button" onclick="likeComment(${post.id}, ${comment.id})">Like</button><button
        class="comment-delete-button" onclick="deleteComment(${post.id}, ${comment.id})">Delete</button>`;
        commentSection.appendChild(commentDiv);
    });
    postDiv.appendChild(commentSection);

    return postDiv;
}

// Event listener for the "Load Posts" button
document.getElementById('load-posts-button').addEventListener('click', function() {
    loadPosts();
});

// Event listener for the "Sort" button
document.getElementById('sort-button').addEventListener('click', function() {
    loadPosts();
});

// Event listener for the "Search" button
document.getElementById('search-button').addEventListener('click', function() {
    loadPosts(true);
});

function searchPosts() {
            loadPosts(true);
}

function addPost() {
    var baseUrl = document.getElementById('api-base-url').value;
    var postTitle = document.getElementById('post-title').value;
    var postContent = document.getElementById('post-content').value;
    var postAuthor = document.getElementById('post-author').value;

    fetch(baseUrl + '/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: postTitle, content: postContent, author: postAuthor })
    })
        .then(response => response.json())
        .then(post => {
            console.log('Post added:', post);
            loadPosts();
            document.getElementById('post-title').value = '';
            document.getElementById('post-content').value = '';
            document.getElementById('post-author').value = '';
        })
        .catch(error => console.error('Error:', error));
}

function deletePost(postId) {
    var baseUrl = document.getElementById('api-base-url').value;
    fetch(baseUrl + '/posts/' + postId, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            console.log('Post deleted:', data);
            loadPosts();
        })
        .catch(error => console.error('Error:', error));
}

function deleteComment(postId, commentId) {
    var baseUrl = document.getElementById('api-base-url').value;
    fetch(baseUrl + '/posts/' + postId + '/comments/' + commentId, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            console.log('Comment deleted:', data);
            loadPosts();
        })
        .catch(error => console.error('Error:', error));
}

function updatePost(postId) {
  const postDiv = document.getElementById(`postDiv-${postId}`);
  const titleElement = postDiv.querySelector('h2');
  const contentElement = postDiv.querySelector('p');
  const authorElement = postDiv.querySelector('p:nth-child(3)');

  const updatedTitle = prompt('Enter the new title:', titleElement.innerText) || titleElement.innerText;
  const updatedContent = prompt('Enter the new content:', contentElement.innerText) || contentElement.innerText;
  const updatedAuthor = prompt('Enter the new author:', authorElement.innerText.replace('Author: ', '')) || authorElement.innerText.replace('Author: ', '');

  const baseUrl = document.getElementById('api-base-url').value;
  const url = `${baseUrl}/posts/${postId}`;
  const data = {
    title: updatedTitle,
    content: updatedContent,
    author: updatedAuthor
  };

  fetch(url, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
    .then(response => response.json())
    .then(updatedPost => {
      // Handle the response and update the post on the client side
      titleElement.innerText = updatedPost.title;
      contentElement.innerText = updatedPost.content;
      authorElement.innerHTML = `<strong>Author:</strong> ${updatedPost.author}`; // Update the author field with the <strong> tag

      // Remove the update form and display the update button again
      const updateButton = createUpdateButton(postId);
      postDiv.removeChild(saveButton);
      postDiv.removeChild(cancelButton);
      postDiv.appendChild(updateButton);
    })
    .catch(error => console.error('Error:', error));
}

function addComment(postId) {
    var baseUrl = document.getElementById('api-base-url').value;
    var commentContent = prompt('Enter your comment:');
    fetch(baseUrl + '/posts/' + postId + '/comments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: commentContent })
    })
        .then(response => response.json())
        .then(comment => {
            console.log('Comment added:', comment);
            loadPosts();
        })
        .catch(error => console.error('Error:', error));
}

function likePost(postId) {
  // Send a POST request to update the likes
  var baseUrl = document.getElementById('api-base-url').value;
  fetch(baseUrl + '/posts/' + postId +'/like', {method: 'POST'})
  .then(response => response.json())
        .then(data => {
            console.log('Comment liked:', data);
            loadPosts();
        })
        .catch(error => console.error('Error:', error));
}


function likeComment(postId, commentId) {
    var baseUrl = document.getElementById('api-base-url').value;
    fetch(baseUrl + '/posts/' + postId + '/comments/' + commentId + '/like', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log('Comment liked:', data);
            loadPosts();
        })
        .catch(error => console.error('Error:', error));
}
