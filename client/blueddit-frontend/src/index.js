import React from 'react';
import ReactDOM from 'react-dom/client';

import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";

import './style.css';

import { AuthProvider } from './AuthContext';

import NotFound from './NotFound';
import MainPage from './MainPage';
import PostPage from './PostPage';
import LoginPage from './LoginPage';

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <MainPage />
    )
  },
  {
    path: "/login",
    element: (
      <LoginPage />
    )
  },
  {
    path: "/about",
    element: (
      <div>About</div>
    )
  },
  {
    path: "/post/:postId",
    element: (
      <PostPage />
    )
  },
  {
    path: "*",
    element: (
      <NotFound />
    )
  }
]);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<AuthProvider><RouterProvider router={router} /></AuthProvider>);
