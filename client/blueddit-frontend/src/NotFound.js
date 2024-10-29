import { Link } from "react-router-dom";

function NotFound() {
    return (
        <div className="not-found">
            <h1>Whoops! You broke Blueddit!</h1>
            <Link to={"/"}>Go back to main page</Link>
        </div>
    );
}

export default NotFound;
