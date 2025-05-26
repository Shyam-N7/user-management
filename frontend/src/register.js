import React, { useState } from 'react';
import './login.css';
import { IoEye, IoEyeOffOutline } from 'react-icons/io5';

const RegisterPage = () => {
    const [showPassword, setShowPassword] = useState(false);
    const [confirmPassword, setConfirmPassword] = useState(false);
    return (
        <div className="login-container">
            <form className="form">
                <p className="title">Register</p>
                <p className="message">Register now and get full access to our app.</p>

                <div className="flex">
                    <label>
                        <input required placeholder=" " type="text" className="input" />
                        <span>Firstname</span>
                    </label>

                    <label>
                        <input required placeholder=" " type="text" className="input" />
                        <span>Lastname</span>
                    </label>
                </div>

                <label>
                    <input required placeholder=" " type="email" className="input" />
                    <span>Email</span>
                </label>

                <label>
                    <input required placeholder=" " type={showPassword ? "text" : "password"} className="input" />
                    <span>Password</span>
                    <button className='icon' type='button' onClick={() => setShowPassword((prev) => !prev)}>
                        {showPassword ? <IoEyeOffOutline /> : <IoEye />}
                    </button>
                </label>

                <label>
                    <input required placeholder=" " type={confirmPassword ? "text" : "password"} className="input" />
                    <span>Confirm password</span>
                    <button type='button' className='icon' onClick={() => setConfirmPassword((prev) => !prev)}>
                        {confirmPassword ? <IoEyeOffOutline/> : <IoEye/>}
                    </button>
                </label>

                <button className="submit">Register</button>
                <p className="signin">
                    Already have an account? <a href="/login">Login</a>
                </p>

            </form>
        </div>
    );
};

export default RegisterPage;