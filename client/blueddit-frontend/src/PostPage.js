import React, { useState, useEffect } from 'react';
import { Link, useParams } from "react-router-dom";
import Navbar from "./Navbar";
import config from './config';
import LoadingPage from './LoadingPage';
import NotFound from './NotFound';
import Helmet from 'react-helmet';
import { getCookie } from './AuthContext';
import { useAuth } from './AuthContext';

const Comment = ({ comment, post }) => {
  const [score, setScore] = useState(comment.score);
  const [showReplyBox, setShowReplyBox] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const { username } = useAuth();

  const handleReplyClick = () => {
    setShowReplyBox(!showReplyBox);
  };

  const handleReplySubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    // Basic validation
    if (!replyText) {
      setErrorMessage('Please enter a reply.');
      return;
    }

    if (!replyText.trim()) {
      setErrorMessage('Please enter a reply.');
      return;
    }

    if (replyText.length >= 5000) {
      setErrorMessage('The reply must be < 5000 characters in size.');
      return;
    }

    const postId = comment.post_id;
    const userId = localStorage.getItem('user_id');

    try {
      const response = await fetch(`${config.API_BASE_URL}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          post_id: post.post.id,
          user_id: userId,
          content: replyText,
          token: localStorage.getItem('token'),
          parent_comment_id: comment.id
        })
      });
      window.location.reload();
    } catch (e) {
      alert(e);
    }
  };

  const handleVote = async (voteType) => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/comment_vote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: localStorage.getItem('user_id'),
          token: localStorage.getItem('token'),
          comment_id: comment.id,
          vote_type: voteType
        })
      });

      if (response.ok) {
        const data = await response.json(); // Await the JSON data from response
        const newScore = data.new_score !== undefined ? data.new_score : 0;
        setScore((prevScore) => prevScore + newScore);
      } else {
        alert('Failed to submit vote');
        console.error('Failed to submit vote');
      }
    } catch (error) {
      alert(error);
      console.error('Error:', error);
    }
  };

  return (
    <>
      <div className="comment-container">
        <div className="comment-vote">
          <div className="upvote" onClick={() => handleVote('upvote')}>&#x25B2;</div>
          <div className="vote-count">{score}</div>
          <div className="downvote" onClick={() => handleVote('downvote')}>&#x25BC;</div>
        </div>
        <div className="comment-content">
          <p className="comment-username">{"u/" + comment.username}</p>
          <p className="comment-text">{comment.content}</p>
          {username ? <button className="comment-reply" onClick={handleReplyClick}>Reply</button> : <></>}
        </div>
      </div>
      {showReplyBox && (
        <div className="reply-box">
          <form onSubmit={handleReplySubmit}>
            <textarea
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder="Write a reply..."
              className="reply-input"
            /><br />
            <button type="submit" className="submit-reply">
              Submit
            </button>
            <p>{errorMessage}</p>
          </form>
        </div>
      )}
      <div className="comment-replies">
        {comment.replies && comment.replies.length > 0 && (
          <div className="comment-replies">
            {comment.replies.map((reply) => (
              <Comment key={reply.id} comment={reply} post={post} />
            ))}
          </div>
        )}
      </div>
    </>
  );
};

function PostPage() {
  window.addEventListener("beforeunload", function () {
    localStorage.setItem("scrollPosition", window.scrollY);
  });

  // Restore scroll position after the page loads
  window.addEventListener("load", function () {
    const scrollPosition = localStorage.getItem("scrollPosition");
    if (scrollPosition) {
      window.scrollTo(0, parseInt(scrollPosition));
      localStorage.removeItem("scrollPosition"); // Clean up
    }
  });

  const { postId } = useParams();
  const [post, setPost] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [showReplyBox, setShowReplyBox] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const { username } = useAuth();

  const [postScore, setPostScore] = useState(0);

  useEffect(() => {
    setPostScore(post.post ? post.post.score : 0);
  }, [post]);

  const handlePostVote = async (type) => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/post_vote`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: localStorage.getItem('user_id'),
          token: localStorage.getItem('token'),
          post_id: postId,
          vote_type: type
        })
      });

      if (response.ok) {
        const data = await response.json();
        const newScore = data.new_score !== undefined ? data.new_score : 0;
        setPostScore(postScore + newScore);
      } else {
        alert('Failed to submit vote');
        console.error('Failed to submit vote');
      }
    } catch (error) {
      alert(error);
      console.error('Error:', error);
    }
  }

  const handleReplyClick = () => {
    setShowReplyBox(!showReplyBox);
  };

  const handleReplySubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    // Basic validation
    if (!replyText) {
      setErrorMessage('Please enter a reply.');
      return;
    }

    if (!replyText.trim()) {
      setErrorMessage('Please enter a reply.');
      return;
    }

    if (replyText.length >= 5000) {
      setErrorMessage('The reply must be < 5000 characters in size.');
      return;
    }
    const userId = localStorage.getItem('user_id');

    try {
      const response = await fetch(`${config.API_BASE_URL}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          post_id: post.post.id,
          user_id: userId,
          content: replyText,
          token: localStorage.getItem('token')
        })
      });
      window.location.reload();
    } catch (e) {
      alert(e);
    }
  };

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const response = await fetch(`${config.API_BASE_URL}/post/${postId}`);
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        const data = await response.json();
        setPost(data[postId]);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, []);

  const renderComments = (comments) => {
    return comments ? comments.map((comment) => <Comment key={comment.id} comment={comment} post={post} />) : <></>;
  };

  if (loading) {
    return <LoadingPage />;
  };

  if (error) {
    return <NotFound />;
  };

  return (
    <>
      <Navbar />
      <Helmet>
        <title>{post.post.title}</title>
      </Helmet>
      <div className="post-page">
        <div className="post-body-block">
          <div className="post-fl-cont">
            <div className="comment-vote">
              <div className="upvote" onClick={() => handlePostVote('upvote')}>&#x25B2;</div>
              <div className="vote-count">{postScore}</div>
              <div className="downvote" onClick={() => handlePostVote('downvote')}>&#x25BC;</div>
            </div>
            <div>
              <div className="post-title comment-text">{post.post.title}</div>
              <div className="comment-text">
                {post.post.body}
              </div>
              <div className="post-footer comment-text">
                Posted at {post.post.created_at} by {post.post.author ? "u/" + post.post.author : "[deleted]"}
              </div>
              {username ? <button className="comment-reply" onClick={handleReplyClick}>Reply</button> : <></>}
              {showReplyBox && (
                <div className="reply-box">
                  <form onSubmit={handleReplySubmit}>
                    <textarea
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                      placeholder="Write a reply..."
                      className="reply-input"
                    /><br />
                    <button type="submit" className="submit-reply">
                      Submit
                    </button>
                    <p>{errorMessage}</p>
                  </form>
                </div>)}
            </div>
          </div>
        </div>
        <hr />
        <div className="comments-block">{renderComments(post.comments)}</div>
      </div>
    </>
  );
}

export default PostPage;
