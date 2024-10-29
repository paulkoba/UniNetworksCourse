import { Link } from "react-router-dom";
import Navbar from "./Navbar";

function LoadingPage() {
    return (
        <>
            <Navbar />
            <div className="loading-page">
                <h1>Loading...</h1>
            </div>
        </>
    );
}

export default LoadingPage;
