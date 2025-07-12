import React, { useState } from 'react';
import './login.css';
import { IoEye, IoEyeOffOutline } from 'react-icons/io5';

const RegisterPage = () => {
    const [showPassword, setShowPassword] = useState(false);
    const [confirmPassword, setConfirmPassword] = useState(false);
    const [formData, setFormData] = useState({
        firstname: '',
        lastname: '',
        email: '',
        password: '',
        passwordConfirm: '',
    });
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setErrors({ ...errors, [e.target.name]: '' });
    };

    const validate = () => {
        const newErrors = {};
        if (!formData.firstname.trim()) newErrors.firstname = 'First name is required';
        if (!formData.lastname.trim()) newErrors.lastname = 'Last name is required';
        if (!formData.email.includes('@')) newErrors.email = 'Enter a valid email';
        if (formData.password.length < 8) newErrors.password = 'Password must be atleast 8 characters';
        if (formData.password !== formData.passwordConfirm)
            newErrors.passwordConfirm = 'Passwords do not match';
        return newErrors;
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        const validationErrors = validate();
        if (Object.keys(validationErrors).length > 0) {
            setErrors(validationErrors);
            return;
        }

        setLoading(true);

        try {
            // const response = await fetch('https://user-management-wucu.onrender.com/register', {
            const response = await fetch('https://user-management-wucu.onrender.com/register', {
                method: 'POST',
                headers: { 'Content-type': 'application/json' },
                body: JSON.stringify({
                    firstname: formData.firstname,
                    lastname: formData.lastname,
                    email: formData.email,
                    password: formData.password,
                }),
            });

            const data = await response.json();
            if (!response.ok) {
                setMessage(data.detail || 'Registration failed');
            }
            else {
                setMessage('Regsitered successfully! Redirecting to login...')
                setTimeout(() => [
                    window.location.href = '/'
                ], 1500);
            }
        } catch (err) {
            console.log(err);
            setMessage(err.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="login-container">
            <form className="form" onSubmit={handleSubmit}>
                <p className="title">Register</p>
                <p className="message">Register now and get full access to our app.</p>

                <div className="flex">
                    <label>
                        <input
                            name='firstname'
                            required
                            placeholder=" "
                            type="text"
                            className="input"
                            value={formData.firstname}
                            onChange={handleChange}
                        />
                        <span>Firstname</span>
                        {errors.firstname && <small className='error'>{errors.firstname}</small>}
                    </label>

                    <label>
                        <input
                            name='lastname'
                            required
                            placeholder=" "
                            type="text"
                            className="input"
                            value={formData.lastname}
                            onChange={handleChange}
                        />
                        <span>Lastname</span>
                        {errors.lastname && <small className='error'>{errors.lastname}</small>}
                    </label>
                </div>

                <label>
                    <input
                        name='email'
                        required
                        placeholder=" "
                        type="email"
                        className="input"
                        value={formData.email}
                        onChange={handleChange}
                    />
                    <span>Email</span>
                    {errors.email && <small className='error'>{errors.email}</small>}
                </label>

                <label>
                    <input
                        name='password'
                        required
                        placeholder=" "
                        type={showPassword ? "text" : "password"}
                        className="input"
                        value={formData.password}
                        onChange={handleChange}
                    />
                    <span>Password</span>
                    <button className='icon' type='button' onClick={() => setShowPassword((prev) => !prev)}>
                        {showPassword ? <IoEyeOffOutline /> : <IoEye />}
                    </button>
                    {errors.password && <small className="error">{errors.password}</small>}
                </label>

                <label>
                    <input
                        name='passwordConfirm'
                        required
                        placeholder=" "
                        type={confirmPassword ? "text" : "password"}
                        className="input"
                        value={formData.passwordConfirm}
                        onChange={handleChange}
                    />
                    <span>Confirm password</span>
                    <button type='button' className='icon' onClick={() => setConfirmPassword((prev) => !prev)}>
                        {confirmPassword ? <IoEyeOffOutline /> : <IoEye />}
                    </button>
                    {errors.passwordConfirm && <small className="error">{errors.passwordConfirm}</small>}
                </label>

                <button type='submit' className="submit-button" disabled={loading}>{loading ?
                    <div class="loader">
                        <div class="loading-text">
                            Registering<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
                        </div>
                    </div>
                    : 'Register'}</button>
                {message && <p className='message-status'>{message}</p>}
                <p className="signin">
                    Already have an account? <a href="/">Login</a>
                </p>

            </form>
        </div>
    );
};

export default RegisterPage;