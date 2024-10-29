import { Link } from "react-router-dom";
import { useAuth } from "./AuthContext";

function Navbar() {
    const { username, logout } = useAuth();

    return (
        !!username ?
            <nav className="navbar">
                <Link to="/">Blueddit</Link>
                <div>
                    <Link>u/{username}</Link>
                    <a onClick={logout}>Logout</a>
                </div>
            </nav> :
            <nav className="navbar">
                <Link to="/">Blueddit</Link>
                <Link to="/login">Login</Link>
            </nav>
    );
}

export default Navbar;
