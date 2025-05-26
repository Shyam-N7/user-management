import "./App.css";
import { ToastContainer } from 'react-toastify';
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home from "./Home";
import LoginPage from "./login";
import RegisterPage from "./register";

const App = () => {
  return (
    <>
      <div className="App">
        <ToastContainer></ToastContainer>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Routes>
        </BrowserRouter>
      </div>
    </>
  )
}

export default App