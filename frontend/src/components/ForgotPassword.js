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
                    <div className="success-icon">
                        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="12" cy="12" r="10" stroke="#10b981" strokeWidth="2" />
                            <path d="m9 12 2 2 4-4" stroke="#10b981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
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