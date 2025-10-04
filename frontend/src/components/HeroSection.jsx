import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Film, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const HeroSection = () => {
  const { user } = useAuth();

  return (
    <div className="w-full bg-background">
      <div className="mx-auto max-w-6xl px-4 py-16 grid gap-8 md:grid-cols-2 items-center">
        <div className="grid gap-6">
          <Badge className="w-fit bg-secondary text-secondary-foreground hover:bg-secondary/80 border-0">
            ✨ Your Personal Movie Curator
          </Badge>
          
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-foreground leading-tight">
            Discover Movies You'll Love
          </h1>
          
          <p className="text-muted-foreground text-lg md:text-xl leading-relaxed">
            Get personalized movie recommendations powered by AI. Build your watchlist, rate movies, and find your next favorite film.
          </p>
          
          <div className="grid grid-cols-1 sm:flex gap-3">
            {user ? (
              <>
                <Button
                  asChild
                  size="lg"
                  className="w-full sm:w-auto rounded-xl bg-foreground text-background hover:bg-foreground/90 shadow-md"
                >
                  <Link to="/recommendations" className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5" />
                    Get Recommendations
                  </Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="w-full sm:w-auto rounded-xl border-foreground"
                >
                  <Link to="/">Browse Movies</Link>
                </Button>
              </>
            ) : (
              <>
                <Button
                  asChild
                  size="lg"
                  className="w-full sm:w-auto rounded-xl bg-foreground text-background hover:bg-foreground/90 shadow-md"
                >
                  <Link to="/register">Get Started</Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="w-full sm:w-auto rounded-xl border-foreground"
                >
                  <Link to="/login">Login</Link>
                </Button>
              </>
            )}
          </div>
        </div>

        <Card className="bg-muted/50 backdrop-blur-sm rounded-xl aspect-[4/3] md:aspect-auto h-[320px] md:h-[420px] flex items-center justify-center border-border/50 shadow-lg overflow-hidden">
          <div className="flex flex-col items-center justify-center gap-4 p-8">
            <Film className="w-24 h-24 text-primary/60" strokeWidth={1.5} />
            <div className="text-center">
              <p className="text-xl font-semibold text-foreground/80 mb-2">
                Cinema at Your Fingertips
              </p>
              <p className="text-sm text-muted-foreground max-w-xs">
                Explore thousands of movies with intelligent recommendations tailored just for you
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default HeroSection;

