import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from "react-router-dom";
import Navbar from "./Navbar";
import config from './config';

function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const [validationError, setValidationError] = useState('');
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setValidationError('');
        setErrorMessage('');

        // Basic validation
        if (!username || !password) {
            setValidationError('Please enter both username and password.');
            return;
        }

        try {
            const response = await fetch(`${config.API_BASE_URL}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            // Check if the response is successful
            if (response.ok) {
                const data = await response.json();
                // Successful login: store user info in local storage if needed
                localStorage.setItem('username', data.username);
                localStorage.setItem('user_id', data.user_id);
                localStorage.setItem('token', data.token);

                navigate("/");
                window.location.reload();
            } else {
                const errorData = await response.json();
                setErrorMessage(errorData.error || 'Login failed. Please try again.');
            }
        } catch (error) {
            setErrorMessage('An error occurred. Please try again later.');
            console.error('Error during login:', error);
        } finally {
            // Reset the form
            setUsername('');
            setPassword('');
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setValidationError('');
        setErrorMessage('');

        // Basic validation
        if (!username || !password) {
            setValidationError('Please enter both username and password.');
            return;
        }

        try {
            const response = await fetch(`${config.API_BASE_URL}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            // Check if the response is successful
            if (response.ok) {
                const data = await response.json();
                // Successful login: store user info in local storage if needed
                localStorage.setItem('username', data.username);
                localStorage.setItem('user_id', data.user_id);
                localStorage.setItem('token', data.token);

                navigate("/");
                window.location.reload();
            } else {
                const errorData = await response.json();
                setErrorMessage(errorData.error || 'Login failed. Please try again.');
            }
        } catch (error) {
            setErrorMessage('An error occurred. Please try again later.');
            console.error('Error during login:', error);
        } finally {
            // Reset the form
            setUsername('');
            setPassword('');
        }
    };

    return (
        <>
            <Navbar />
            <div className="login-page">
                <form>
                    <div className='entry-form-row'>
                        <label>Username:</label>
                        <input
                            type=""
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                        />
                    </div>
                    <div className='entry-form-row'>
                        <label>Password:</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>
                    <div className='entry-form-row'>
                        <button type="submit" onClick={handleLogin}>Login</button>
                        <button type="submit" onClick={handleRegister}>Register</button>
                    </div>
                    {errorMessage ? <div>{errorMessage}</div> : <></>}
                </form>
            </div>
        </>
    );
}

export default LoginPage;
