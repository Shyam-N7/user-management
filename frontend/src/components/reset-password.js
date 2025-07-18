import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';

const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    token: '',
    new_password: '',
    confirm_password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      setFormData(prev => ({ ...prev, token }));
    } else {
      setError('Invalid reset link. Please request a new password reset.');
    }
  }, [searchParams]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.new_password !== formData.confirm_password) {
      setError('Passwords do not match');
      return;
    }

    if (formData.new_password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('https://user-management-wucu.onrender.com/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: formData.token,
          new_password: formData.new_password
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(true);
        setTimeout(() => navigate('/'), 3000);
      } else {
        setError(data.detail || 'Password reset failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="login-container">
        <div className="form">
          <p className="title" style={{"fontSize": "27px"}}>Password Reset Successful!</p>
          <p className="message">Your password has been reset successfully. You will be redirected to login in 3 seconds.</p>
          <div className="loader">
            <div className="loading-text">
              Redirecting<span className="dot">.</span><span className="dot">.</span><span className="dot">.</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-container">
      <form className="form" onSubmit={handleSubmit}>
        <p className="title">Reset Password</p>
        <p className="message">Enter your new password below.</p>
        
        <label>
          <input
            required
            placeholder=" "
            type="password"
            className="input"
            value={formData.new_password}
            onChange={(e) => setFormData(prev => ({ ...prev, new_password: e.target.value }))}
            minLength={8}
          />
          <span>New Password</span>
        </label>

        <label>
          <input
            required
            placeholder=" "
            type="password"
            className="input"
            value={formData.confirm_password}
            onChange={(e) => setFormData(prev => ({ ...prev, confirm_password: e.target.value }))}
            minLength={8}
          />
          <span>Confirm Password</span>
        </label>

        <button type='submit' className="submit-button" disabled={loading || !formData.token}>
          {loading ? (
            <div className="loader">
              <div className="loading-text">
                Resetting<span className="dot">.</span><span className="dot">.</span><span className="dot">.</span>
              </div>
            </div>
          ) : 'Reset Password'}
        </button>

        {error && <p className='error'>{error}</p>}
      </form>
    </div>
  );
};

export default ResetPasswordPage;