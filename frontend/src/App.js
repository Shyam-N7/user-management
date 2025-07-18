import React, { Suspense, lazy } from 'react';
import "./App.css";
import { Slide, ToastContainer } from 'react-toastify';
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ProtectedRoute from "./components/protectRoute";
import PageNotFound from "./components/PageFourOFour";
import ForgotPassword from './components/ForgotPassword';
import ResetPasswordPage from './components/reset-password';

const Login = lazy(() => import('./components/login'));
const Register = lazy(() => import('./components/register'));
const Home = lazy(() => import('./Home'));

const App = () => {
  return (
    <>
      <div className="App">
        <ToastContainer position="top-center" transition={Slide}></ToastContainer>
        <BrowserRouter>
          <Suspense fallback={<div className="spinner"></div>}></Suspense>
          <Routes>
            <Route path="/" element={<Login />} />
            <Route
              path="/home"
              element={
                <ProtectedRoute>
                  <Home />
                </ProtectedRoute>
              }
            />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="*" element={<PageNotFound />} />
          </Routes>
        </BrowserRouter>
      </div>
    </>
  )
}

export default App