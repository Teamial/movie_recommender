import { Link } from 'react-router-dom';
import { Film, Heart, Bookmark, Sparkles, Menu, Settings, Sun, Moon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { useTheme } from '../context/ThemeContext';
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";

const Navbar = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <nav className="w-full border-b bg-background shadow-xs">
      <div className="mx-auto max-w-6xl h-16 px-4 flex items-center justify-between gap-4">
        <Link to="/" className="flex items-center gap-2 font-semibold text-foreground hover:text-primary transition-colors">
          <Film className="w-6 h-6 text-primary" />
          <span className="text-lg tracking-tight">Cineamate</span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-6">
          <Link 
            to="/" 
            className="text-sm font-medium text-foreground/80 hover:text-foreground transition-colors"
          >
            Browse
          </Link>

          {user && (
            <>
              <Link 
                to="/recommendations" 
                className="flex items-center gap-2 text-sm font-medium text-foreground/80 hover:text-foreground transition-colors"
              >
                <Sparkles className="w-4 h-4" />
                <span>For You</span>
              </Link>
              <Link 
                to="/favorites" 
                className="flex items-center gap-2 text-sm font-medium text-foreground/80 hover:text-foreground transition-colors"
              >
                <Heart className="w-4 h-4" />
                <span>Favorites</span>
              </Link>
              <Link 
                to="/watchlist" 
                className="flex items-center gap-2 text-sm font-medium text-foreground/80 hover:text-foreground transition-colors"
              >
                <Bookmark className="w-4 h-4" />
                <span>Watchlist</span>
              </Link>
            </>
          )}
        </div>

        {/* Desktop Auth */}
        <div className="hidden md:flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            className="rounded-xl"
            onClick={toggleTheme}
            aria-label="Toggle theme"
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
          {user ? (
            <>
              <Link 
                to="/settings"
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors px-3 py-1.5 rounded-lg hover:bg-muted"
              >
                <Settings className="w-4 h-4" />
                <span>{user.username}</span>
              </Link>
              <Button
                onClick={logout}
                variant="outline"
                size="sm"
                className="rounded-xl"
              >
                Logout
              </Button>
            </>
          ) : (
            <>
              <Button
                asChild
                variant="ghost"
                size="sm"
                className="rounded-xl"
              >
                <Link to="/login">Login</Link>
              </Button>
              <Button
                asChild
                size="sm"
                className="rounded-xl bg-foreground text-background hover:bg-foreground/90"
              >
                <Link to="/register">Sign up</Link>
              </Button>
            </>
          )}
        </div>

        {/* Mobile Menu */}
        <Sheet>
          <SheetTrigger asChild className="md:hidden">
            <Button variant="ghost" size="icon" className="md:hidden">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Menu</span>
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-[85vw] sm:max-w-sm p-6">
            <div className="flex flex-col gap-4">
              <h3 className="font-semibold text-lg mb-2">Cineamate</h3>

              <Button
                variant="outline"
                onClick={toggleTheme}
                className="rounded-xl w-full justify-start"
                aria-label="Toggle theme"
              >
                {theme === 'dark' ? (
                  <>
                    <Sun className="h-4 w-4 mr-2" /> Light mode
                  </>
                ) : (
                  <>
                    <Moon className="h-4 w-4 mr-2" /> Dark mode
                  </>
                )}
              </Button>
              
              <Link 
                to="/" 
                className="text-base font-medium hover:text-primary transition-colors"
              >
                Browse
              </Link>

              {user && (
                <>
                  <Link 
                    to="/recommendations" 
                    className="text-base font-medium hover:text-primary transition-colors"
                  >
                    For You
                  </Link>
                  <Link 
                    to="/favorites" 
                    className="text-base font-medium hover:text-primary transition-colors"
                  >
                    Favorites
                  </Link>
                  <Link 
                    to="/watchlist" 
                    className="text-base font-medium hover:text-primary transition-colors"
                  >
                    Watchlist
                  </Link>
                </>
              )}

              <Separator className="my-2" />

              {user ? (
                <>
                  <Link 
                    to="/settings"
                    className="text-base font-medium hover:text-primary transition-colors flex items-center gap-2"
                  >
                    <Settings className="w-4 h-4" />
                    <span>Settings</span>
                  </Link>
                  <span className="text-sm text-muted-foreground">
                    Logged in as {user.username}
                  </span>
                  <Button
                    onClick={logout}
                    variant="outline"
                    className="w-full rounded-xl"
                  >
                    Logout
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    asChild
                    variant="outline"
                    className="w-full rounded-xl"
                  >
                    <Link to="/login">Login</Link>
                  </Button>
                  <Button
                    asChild
                    className="w-full rounded-xl bg-foreground text-background hover:bg-foreground/90"
                  >
                    <Link to="/register">Sign up</Link>
                  </Button>
                </>
              )}
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </nav>
  );
};

export default Navbar;