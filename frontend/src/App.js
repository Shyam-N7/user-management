import "./App.css";
import { ToastContainer } from 'react-toastify';
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from "./Home";
import LoginPage from "./components/login";
import RegisterPage from "./components/register";
import ProtectedRoute from "./components/protectRoute";
import PageNotFound from "./components/PageFourOFour";

const App = () => {
  return (
    <>
      <div className="App">
        <ToastContainer></ToastContainer>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LoginPage />} />
            <Route
              path="/home"
              element={
                <ProtectedRoute>
                  <Home />
                </ProtectedRoute>
              }
            />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="*" element={<PageNotFound />} />
          </Routes>
        </BrowserRouter>
      </div>
    </>
  )
}

export default App