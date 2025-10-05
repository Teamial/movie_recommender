import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getTopRated } from '../services/api';
import { cn } from '@/lib/utils';
import { getPosterUrl } from '../utils/imageUtils';

// Fallback movies with cinematic imagery
const FALLBACK_MOVIES = [
  {
    id: 1,
    title: 'Dune: Part Three',
    poster_url: 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=1925&auto=format&fit=crop',
    release_date: '2024-12-15'
  },
  {
    id: 2,
    title: 'Blade Runner 2099',
    poster_url: 'https://images.unsplash.com/photo-1478720568477-152d9b164e26?q=80&w=2070&auto=format&fit=crop',
    release_date: '2024-11-20'
  },
  {
    id: 3,
    title: 'The Matrix: Resurrections',
    poster_url: 'https://images.unsplash.com/photo-1485846234645-a62644f84728?q=80&w=2059&auto=format&fit=crop',
    release_date: '2024-10-30'
  },
  {
    id: 4,
    title: 'Interstellar Odyssey',
    poster_url: 'https://images.unsplash.com/photo-1440404653325-ab127d49abc1?q=80&w=2070&auto=format&fit=crop',
    release_date: '2024-12-01'
  },
  {
    id: 5,
    title: 'Neon Nights',
    poster_url: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=2070&auto=format&fit=crop',
    release_date: '2024-11-15'
  }
];

const MovieSlideshow = ({ autoPlayInterval = 4000 }) => {
  const [movies, setMovies] = useState(FALLBACK_MOVIES);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const timeoutRef = useRef(null);

  // Fetch top-rated movies to display
  useEffect(() => {
    const fetchMovies = async () => {
      try {
        const response = await getTopRated(5);
        if (response.data && response.data.length > 0) {
          setMovies(response.data);
        }
      } catch (error) {
        console.log('Using fallback movies:', error);
        // Keep fallback movies on error
      } finally {
        setLoading(false);
      }
    };
    
    fetchMovies();
  }, []);

  const goToSlide = (index) => {
    setCurrentIndex(index);
  };

  const nextSlide = () => {
    setCurrentIndex((prevIndex) => (prevIndex + 1) % movies.length);
  };

  useEffect(() => {
    if (!isPaused && !loading) {
      timeoutRef.current = setTimeout(() => {
        nextSlide();
      }, autoPlayInterval);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [currentIndex, isPaused, autoPlayInterval, loading, movies.length]);

  return (
    <div
      className="relative w-full h-full overflow-hidden rounded-xl bg-background shadow-lg"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      {/* Slideshow Container */}
      <div className="relative w-full h-full">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentIndex}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{
              duration: 0.8,
              ease: [0.25, 0.46, 0.45, 0.94]
            }}
            className="absolute inset-0"
          >
            {/* Image */}
            <div className="relative w-full h-full">
              <img
                src={getPosterUrl(movies[currentIndex])}
                alt={movies[currentIndex].title}
                className="w-full h-full object-cover"
              />
              
              {/* Gradient Overlay - matches theme background for dark mode support */}
              <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-background/40 to-transparent" />
              
              {/* Content */}
              <div className="absolute bottom-0 left-0 right-0 p-6 md:p-8">
                <motion.div
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: 0.3, duration: 0.6 }}
                >
                  <p className="text-xs md:text-sm text-foreground/80 mb-2 font-medium tracking-wide">
                    {movies[currentIndex].vote_average ? `★ ${movies[currentIndex].vote_average.toFixed(1)}` : 'Featured'}
                  </p>
                  <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold text-foreground mb-2 tracking-tight">
                    {movies[currentIndex].title}
                  </h2>
                  <p className="text-sm md:text-base text-foreground/90 font-medium">
                    {movies[currentIndex].release_date ? new Date(movies[currentIndex].release_date).getFullYear() : '2024'}
                  </p>
                </motion.div>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation Dots */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2 z-10">
        {movies.map((_, index) => (
          <button
            key={index}
            onClick={() => goToSlide(index)}
            className={cn(
              'transition-all duration-300 rounded-full',
              currentIndex === index
                ? 'w-6 h-2 bg-background'
                : 'w-2 h-2 bg-background/50 hover:bg-background/75'
            )}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>

      {/* Progress Bar */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-background/20 z-10">
        <motion.div
          key={currentIndex}
          className="h-full bg-primary"
          initial={{ width: '0%' }}
          animate={{ width: isPaused ? '0%' : '100%' }}
          transition={{
            duration: autoPlayInterval / 1000,
            ease: 'linear'
          }}
        />
      </div>
    </div>
  );
};

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

        {/* Movie Slideshow */}
        <div className="aspect-[4/3] md:aspect-auto h-[320px] md:h-[420px]">
          <MovieSlideshow />
        </div>
      </div>
    </div>
  );
};

export default HeroSection;

