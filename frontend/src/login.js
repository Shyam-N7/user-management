import React, { useState } from 'react';
import './login.css';
import { IoEye, IoEyeOffOutline } from 'react-icons/io5';

const LoginPage = () => {
    const [showPassword, setShowPassword] = useState(false);
    return (
        <div className="login-container">
            <form className="form">
                <p className="title">Login</p>
                <p className="message">Login now and get full access to our app.</p>

                <label>
                    <input required placeholder=" " type="email" className="input" />
                    <span>Email</span>
                </label>

                <label>
                    <input
                        required
                        placeholder=" "
                        type={showPassword ? "text" : "password"}
                        className="input" />
                    <span>Password</span>
                    <button
                        type='button'
                        className="icon"
                        onClick={() => setShowPassword((prev) => !prev)}
                    >
                        {showPassword ? <IoEyeOffOutline /> : <IoEye />}
                    </button>
                </label>

                <button className="submit">Login</button>
                <p className="signin">
                    Don't have an account? <a href="/register">Create One</a>
                </p>

            </form>
        </div>
    );
};

export default LoginPage;