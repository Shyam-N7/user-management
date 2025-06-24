import React, { useState } from 'react';
import './login.css';
import { IoEye, IoEyeOffOutline } from 'react-icons/io5';
import { toast } from 'react-toastify';

const LoginPage = () => {
    const [showPassword, setShowPassword] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const response = await fetch('https://user-management-wucu.onrender.com/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error('Invalid email or password.');
            }

            //save token to localStorage
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));

            toast.success(data.message);
            window.location.href = '/home'

        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="login-container">
            <form className="form" onSubmit={handleLogin}>
                <p className="title">Login</p>
                <p className="message">Login now and get full access to our app.</p>

                <label>
                    <input
                        required
                        placeholder=" "
                        type="email"
                        className="input"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                    />
                    <span>Email</span>
                </label>

                <label>
                    <input
                        required
                        placeholder=" "
                        type={showPassword ? "text" : "password"}
                        className="input"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                    <span>Password</span>
                    <button
                        type='button'
                        className="icon"
                        onClick={() => setShowPassword((prev) => !prev)}
                    >
                        {showPassword ? <IoEyeOffOutline /> : <IoEye />}
                    </button>
                </label>

                <button type='submit' className="submit-button" disabled={loading}>{loading ?
                    <div class="loader">
                        <div class="loading-text">
                            Authenticating<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
                        </div>
                    </div>
                    : 'Login'}</button>

                {error && <p className='error'>{error}</p>}

                <p className="signin">
                    Don't have an account? <a href="/register">Create One</a>
                </p>

            </form>
        </div>
    );
};

export default LoginPage;