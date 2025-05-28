import React, { useEffect } from 'react'
import './PageFourOFour.css'
import { useNavigate } from 'react-router-dom';

const PageNotFound = () => {

    useEffect(() => {
        const obj = document.querySelector('h1.text-center');
        if (!obj) return;

        const textArray = obj.textContent.split('');
        const min = 1, max = 9;

        // Generate dynamic CSS for animation delays
        let style = document.createElement('style');
        let css = '';
        for (let i = min; i <= max; i++) {
            css += `.ld${i} { animation-delay: 1.${i}s; }\n`;
        }
        style.innerHTML = css;
        document.head.appendChild(style);

        // Apply animation spans
        obj.innerHTML = '';
        textArray.forEach(char => {
            const delay = Math.floor(Math.random() * (max - min + 1)) + min;
            const span = document.createElement('span');
            span.className = `letterDrop ld${delay}`;
            span.innerHTML = char === ' ' ? '&nbsp;' : char;
            obj.appendChild(span);
        });

        // Cleanup on unmount
        return () => {
            document.head.removeChild(style);
        };
    }, []);

    const navigate = useNavigate();

    const handleNavivate = (e) => {
        e.preventDefault();
        navigate("/");
    }

    return (
        <div className="page-not-found-container">
            <section className="page_404">
                <div className="container">
                    <div className="col-sm-12">
                        <div className="col-sm-10 col-sm-offset-1 text-center">
                            <div className="four_zero_four_bg">
                                <h1 className="text-center">404</h1>
                            </div>
                            <div className="contant_box_404">
                                <p className="para">Looks like you're lost</p>
                                <p className="para">The page you are looking for is not available!</p>
                                <div className="Btn-Container" onClick={handleNavivate}>
                                    <span className="text">Take me home!</span>
                                    <span className="icon-Container">
                                        <svg
                                            width="16"
                                            height="19"
                                            viewBox="0 0 16 19"
                                            fill="nones"
                                            xmlns="http://www.w3.org/2000/svg"
                                        >
                                            <circle cx="1.61321" cy="1.61321" r="1.5" fill="blue"></circle>
                                            <circle cx="5.73583" cy="1.61321" r="1.5" fill="blue"></circle>
                                            <circle cx="5.73583" cy="5.5566" r="1.5" fill="blue"></circle>
                                            <circle cx="9.85851" cy="5.5566" r="1.5" fill="blue"></circle>
                                            <circle cx="9.85851" cy="9.5" r="1.5" fill="blue"></circle>
                                            <circle cx="13.9811" cy="9.5" r="1.5" fill="blue"></circle>
                                            <circle cx="5.73583" cy="13.4434" r="1.5" fill="blue"></circle>
                                            <circle cx="9.85851" cy="13.4434" r="1.5" fill="blue"></circle>
                                            <circle cx="1.61321" cy="17.3868" r="1.5" fill="blue"></circle>
                                            <circle cx="5.73583" cy="17.3868" r="1.5" fill="blue"></circle>
                                        </svg>
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    )
}

export default PageNotFound;
