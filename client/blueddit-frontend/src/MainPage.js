import React, { useState, useEffect } from 'react';

import config from './config';

import Navbar from "./Navbar";
import LoadingPage from "./LoadingPage";
import NotFound from "./NotFound";
import { useAuth } from './AuthContext';
import { Link } from 'react-router-dom';

function MainPage() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreatePost, setShowCreatePost] = useState(false);
  const [createPostTitle, setCreatePostTitle] = useState("");
  const [createPostText, setCreatePostText] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [scores, setScores] = useState({});
  const { username } = useAuth();

  useEffect(() => {
    // Re-initialize scores when posts change
    const initialScores = posts.reduce((acc, post) => {
      acc[post.id] = post.score;
      return acc;
    }, {});
    setScores(initialScores);
  }, [posts]);

  const handleVote = async (id, type) => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/post_vote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: localStorage.getItem('user_id'),
          token: localStorage.getItem('token'),
          post_id: id,
          vote_type: type
        })
      });

      if (response.ok) {
        const data = await response.json(); // Await the JSON data from response
        const newScore = data.new_score !== undefined ? data.new_score : 0;
        setScores(prevScores => ({
          ...prevScores,
          [id]: prevScores[id] + newScore
        }));
      } else {
        alert('Failed to submit vote');
        console.error('Failed to submit vote');
      }
    } catch (error) {
      alert(error);
      console.error('Error:', error);
    }
  }

  const handleCreatePost = async () => {
    setShowCreatePost(true);
  }

  const handlePostSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    // Basic validation
    if (!createPostText || !createPostTitle) {
      setErrorMessage('Please fill out all required fields.');
      return;
    }

    if (!createPostText.trim() || !createPostTitle.trim()) {
      setErrorMessage('Please fill out all required fields.');
      return;
    }

    if (createPostTitle.length > 100) {
      setErrorMessage('The title must be 100 characters or fewer.');
      return;
    }

    if (createPostText.length > 5000) {
      setErrorMessage('The post body must be 5000 characters or fewer.');
      return;
    }

    const userId = localStorage.getItem('user_id');

    try {
      const response = await fetch(`${config.API_BASE_URL}/create_post`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          title: createPostTitle,
          content: createPostText,
          token: localStorage.getItem('token'),
        })
      });
      window.location.reload();
    } catch (e) {
      alert(e);
    }
  }

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const response = await fetch(`${config.API_BASE_URL}/posts`);
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        setPosts(data[0][0]);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, []);

  if (loading) {
    return <LoadingPage />;
  };

  if (error) {
    return <NotFound />;
  };

  return <>
    <Navbar />
    {showCreatePost && (
      <div className="reply-box">
        <form onSubmit={handlePostSubmit}>
          <input type="text" value={createPostTitle} onChange={(e) => setCreatePostTitle(e.target.value)} placeholder='Title...'></input>
          <textarea
            value={createPostText}
            onChange={(e) => setCreatePostText(e.target.value)}
            placeholder="Write a post..."
            className="reply-input"
          /><br />
          <button type="submit" className="create-post">
            Submit
          </button>
          <p>{errorMessage}</p>
        </form>
      </div>
    )}
    <table className="main-page-table">
      {username ? <tr><td /><td>{<button className="create-post" onClick={handleCreatePost}>Create Post</button>}</td></tr> : <></>}
      {posts.map(post => (
        <tr key={post.id} className="main-page-post">
          <td className="comment-vote">
            <div className="upvote" onClick={() => handleVote(post.id, 'upvote')}>&#x25B2;</div>
            <div>{scores[post.id]}</div>
            <div className="downvote" onClick={() => handleVote(post.id, 'downvote')}>&#x25BC;</div>
          </td>
          <td className="post-description">
            <div className="post-title-main-page">
              <Link to={`/post/${post.id}`}>{post.title}</Link>
            </div>
            <div className="post-submitted-main-page">
              Submitted by u/{post.author} at: {new Date(post.created_at).toLocaleString()}
            </div>
          </td>
        </tr>
      ))}
    </table>
  </>;
}

export default MainPage;
