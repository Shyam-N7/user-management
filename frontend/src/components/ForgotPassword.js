import React, { useState } from 'react';
import './login.css';
import { toast } from 'react-toastify';

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [isSubmitted, setIsSubmitted] = useState(false);

    const validateEmail = (email) => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    const handleEmailChange = (e) => {
        const newEmail = e.target.value;
        setEmail(newEmail);
        if (error) setError('');
    };

    const handleForgotPassword = async (e) => {
        e.preventDefault();
        setError('');

        if (!email.trim()) {
            setError('Email is required');
            return;
        }

        if (!validateEmail(email)) {
            setError('Please enter a valid email address');
            return;
        }

        setLoading(true);

        try {
            const response = await fetch('https://user-management-wucu.onrender.com/forgot-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email: email.trim() }),
            });

            const data = await response.json();

            if (!response.ok) {
                const errorMessage = data.detail || 'Invalid email or email not found.';
                throw new Error(errorMessage);
            }

            toast.success(data.message);
            setIsSubmitted(true);

        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleBackToLogin = () => {
        window.location.href = '/';
    };

    const handleResendEmail = () => {
        setIsSubmitted(false);
        setError('');
    };

    if (isSubmitted) {
        return (
            <div className="login-container">
                <div className="form">
                    <p className="title">Check Your Email</p>
                    <div className="animation-ctn">
                        <div className="icon icon--order-success svg">
                            <svg xmlns="http://www.w3.org/2000/svg" width="60px" height="60px" viewBox="0 0 154 154">
                                <g fill="none" stroke="#22AE73" strokeWidth="2">
                                    <circle
                                        cx="77"
                                        cy="77"
                                        r="72"
                                        style={{
                                            strokeDasharray: '480px, 480px',
                                            strokeDashoffset: '960px'
                                        }}
                                    />
                                    <circle
                                        id="colored"
                                        fill="#22AE73"
                                        cx="77"
                                        cy="77"
                                        r="72"
                                        style={{
                                            strokeDasharray: '480px, 480px',
                                            strokeDashoffset: '960px'
                                        }}
                                    />
                                    <polyline
                                        className="st0"
                                        stroke="#fff"
                                        strokeWidth="8"
                                        points="43.5,77.8 63.7,97.9 112.2,49.4"
                                        style={{
                                            strokeDasharray: '100px, 100px',
                                            strokeDashoffset: '200px'
                                        }}
                                    />
                                </g>
                            </svg>
                        </div>
                    </div>
                    <p className="message">
                        We've sent password reset instructions to <strong>{email}</strong>
                    </p>
                    <p className="message" style={{ fontSize: '0.9em', color: '#666', marginTop: '10px' }}>
                        Didn't receive the email? Check your spam folder or try again.
                    </p>

                    <div className="button-group">
                        <button
                            type="button"
                            className="submit-button"
                            onClick={handleBackToLogin}
                            style={{ marginBottom: '10px' }}
                        >
                            Back to Login
                        </button>
                        <button
                            type="button"
                            className="submit-button secondary"
                            onClick={handleResendEmail}
                        >
                            Resend Email
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="login-container">
            <form className="form" onSubmit={handleForgotPassword}>
                <p className="title">Reset Password</p>
                <p className="message">Enter your email to reset password.</p>

                <label>
                    <input
                        required
                        placeholder=" "
                        type="email"
                        className="input"
                        value={email}
                        onChange={handleEmailChange}
                        disabled={loading}
                    />
                    <span>Email</span>
                </label>

                <button
                    type="submit"
                    className="submit-button"
                    disabled={loading || !email.trim()}
                >
                    {loading ? (
                        <div className="loader">
                            <div className="loading-text">
                                Sending<span className="dot">.</span><span className="dot">.</span><span className="dot">.</span>
                            </div>
                        </div>
                    ) : (
                        'Send password reset link'
                    )}
                </button>

                {error && <p className="error">{error}</p>}

                <div className="signin">
                    <p>
                        Remember your password?{' '}
                        <a href="/" className="link">
                            Back to Login
                        </a>
                    </p>
                </div>
            </form>
        </div>
    );
};

export default ForgotPassword;