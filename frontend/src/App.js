import React, { Suspense, lazy } from 'react';
import "./App.css";
import { ToastContainer } from 'react-toastify';
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import ProtectedRoute from "./components/protectRoute";
import PageNotFound from "./components/PageFourOFour";

const Login = lazy(() => import('./components/login'));
const Register = lazy(() => import('./components/register'));
const Home = lazy(() => import('./Home'));

const App = () => {
  return (
    <>
      <div className="App">
        <ToastContainer></ToastContainer>
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
            <Route path="*" element={<PageNotFound />} />
          </Routes>
        </BrowserRouter>
      </div>
    </>
  )
}

export default App