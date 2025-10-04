import { Link } from 'react-router-dom';
import { Film, Heart, Bookmark, User, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-gray-900 border-b border-gray-800">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 text-white font-bold text-xl">
            <Film className="w-8 h-8" />
            <span>MovieRec</span>
          </Link>

          <div className="flex items-center gap-6">
            <Link to="/" className="text-gray-300 hover:text-white transition">
              Browse
            </Link>

            {user ? (
              <>
                <Link to="/favorites" className="flex items-center gap-2 text-gray-300 hover:text-white transition">
                  <Heart className="w-5 h-5" />
                  <span>Favorites</span>
                </Link>
                <Link to="/watchlist" className="flex items-center gap-2 text-gray-300 hover:text-white transition">
                  <Bookmark className="w-5 h-5" />
                  <span>Watchlist</span>
                </Link>
                <div className="flex items-center gap-4 ml-4 pl-4 border-l border-gray-700">
                  <Link to="/profile" className="flex items-center gap-2 text-gray-300 hover:text-white transition">
                    <User className="w-5 h-5" />
                    <span>{user.username}</span>
                  </Link>
                  <button
                    onClick={logout}
                    className="flex items-center gap-2 text-gray-300 hover:text-white transition"
                  >
                    <LogOut className="w-5 h-5" />
                  </button>
                </div>
              </>
            ) : (
              <>
                <Link to="/login" className="text-gray-300 hover:text-white transition">
                  Login
                </Link>
                <Link to="/register" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition">
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;