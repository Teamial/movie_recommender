import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { 
  Sparkles, 
  ChevronRight, 
  ChevronLeft, 
  Check, 
  ThumbsUp, 
  ThumbsDown,
  MapPin,
  Calendar,
  Star,
  Film
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '../context/AuthContext';
import { getMovies, createRating } from '../services/api';
import api from '../services/api';

const GENRES = [
  'Action', 'Adventure', 'Animation', 'Comedy', 'Crime',
  'Documentary', 'Drama', 'Fantasy', 'Horror', 'Mystery',
  'Romance', 'Science Fiction', 'Thriller', 'War', 'Western'
];

const Onboarding = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [demographics, setDemographics] = useState({ age: '', location: '' });
  const [selectedGenres, setSelectedGenres] = useState({});
  const [movies, setMovies] = useState([]);
  const [movieRatings, setMovieRatings] = useState({});
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();
  const navigate = useNavigate();

  const totalSteps = 5;

  // Fetch popular movies for rating step
  useEffect(() => {
    if (currentStep === 3) {
      fetchPopularMovies();
    }
  }, [currentStep]);

  const fetchPopularMovies = async () => {
    try {
      setLoading(true);
      const response = await getMovies({ 
        page: 1, 
        page_size: 10,
        sort_by: 'popularity'
      });
      setMovies(response.data.movies);
    } catch (error) {
      console.error('Error fetching movies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenreToggle = (genre) => {
    setSelectedGenres(prev => ({
      ...prev,
      [genre]: prev[genre] === 'like' ? null : 'like'
    }));
  };

  const handleGenreDislike = (genre) => {
    setSelectedGenres(prev => ({
      ...prev,
      [genre]: prev[genre] === 'dislike' ? null : 'dislike'
    }));
  };

  const handleMovieRating = (movieId, rating) => {
    setMovieRatings(prev => ({
      ...prev,
      [movieId]: rating
    }));
  };

  const handleSkipMovie = (movieId) => {
    setMovieRatings(prev => {
      const newRatings = { ...prev };
      delete newRatings[movieId];
      return newRatings;
    });
  };

  const handleNext = async () => {
    if (currentStep === totalSteps - 1) {
      await completeOnboarding();
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    setCurrentStep(prev => Math.max(0, prev - 1));
  };

  const completeOnboarding = async () => {
    try {
      setLoading(true);

      // Save demographics and genre preferences to localStorage for future use
      // (Backend endpoint doesn't exist yet, so we store locally)
      const onboardingData = {
        demographics: demographics,
        genres: {
          liked: Object.keys(selectedGenres).filter(g => selectedGenres[g] === 'like'),
          disliked: Object.keys(selectedGenres).filter(g => selectedGenres[g] === 'dislike')
        },
        completedAt: new Date().toISOString()
      };
      
      localStorage.setItem(`onboarding_data_${user.id}`, JSON.stringify(onboardingData));

      // Save movie ratings to backend
      const ratingPromises = Object.entries(movieRatings).map(([movieId, rating]) => 
        createRating({ movie_id: parseInt(movieId), rating }, user.id)
      );
      
      await Promise.all(ratingPromises);

      // Mark onboarding as complete
      localStorage.setItem(`onboarding_complete_${user.id}`, 'true');

      // Redirect to recommendations
      navigate('/recommendations');
    } catch (error) {
      console.error('Error completing onboarding:', error);
      // Even if ratings fail, mark as complete and redirect
      localStorage.setItem(`onboarding_complete_${user.id}`, 'true');
      navigate('/recommendations');
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0: return true; // Welcome screen
      case 1: return true; // Demographics (optional)
      case 2: return Object.keys(selectedGenres).some(g => selectedGenres[g]); // At least 1 genre
      case 3: return true; // Movie ratings are now optional - can skip if haven't seen any
      case 4: return true; // Completion
      default: return false;
    }
  };

  const steps = [
    {
      id: 'welcome',
      title: 'Welcome to Cinemate',
      component: <WelcomeStep />
    },
    {
      id: 'demographics',
      title: 'Tell us about yourself',
      component: (
        <DemographicsStep 
          demographics={demographics} 
          setDemographics={setDemographics} 
        />
      )
    },
    {
      id: 'genres',
      title: 'Choose your favorite genres',
      component: (
        <GenreStep 
          selectedGenres={selectedGenres}
          onLike={handleGenreToggle}
          onDislike={handleGenreDislike}
        />
      )
    },
    {
      id: 'ratings',
      title: 'Rate some popular movies',
        component: (
          <RatingStep
            movies={movies}
            movieRatings={movieRatings}
            onRate={handleMovieRating}
            onSkip={handleSkipMovie}
            loading={loading}
          />
        )
    },
    {
      id: 'completion',
      title: 'You\'re all set!',
      component: <CompletionStep />
    }
  ];

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-4xl">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between mb-2">
            {steps.map((step, index) => (
              <div 
                key={step.id}
                className={`flex-1 h-2 rounded-full mx-1 transition-all duration-300 ${
                  index <= currentStep ? 'bg-primary' : 'bg-muted'
                }`}
              />
            ))}
          </div>
          <p className="text-center text-muted-foreground text-sm">
            Step {currentStep + 1} of {totalSteps}
          </p>
        </div>

        {/* Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="bg-card rounded-2xl p-8 md:p-12 border border-border shadow-lg min-h-[500px] flex flex-col"
          >
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6 text-center">
              {steps[currentStep].title}
            </h2>

            <div className="flex-1 flex items-center justify-center">
              {steps[currentStep].component}
            </div>

            {/* Navigation */}
            <div className="flex justify-between items-center mt-8 pt-6 border-t border-border">
              <Button
                onClick={handleBack}
                variant="outline"
                className="rounded-xl"
                disabled={currentStep === 0}
              >
                <ChevronLeft className="w-4 h-4 mr-2" />
                Back
              </Button>

              <Button
                onClick={handleNext}
                className="rounded-xl bg-foreground text-background hover:bg-foreground/90"
                disabled={!canProceed() || loading}
              >
                {currentStep === totalSteps - 1 ? (
                  <>
                    {loading ? 'Setting up...' : 'Get Started'}
                    <Check className="w-4 h-4 ml-2" />
                  </>
                ) : (
                  <>
                    Next
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </>
                )}
              </Button>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

// Step Components
const WelcomeStep = () => (
  <div className="text-center max-w-2xl mx-auto space-y-6">
    <div className="p-4 bg-primary/10 rounded-full w-24 h-24 mx-auto flex items-center justify-center">
      <Sparkles className="w-12 h-12 text-primary" />
    </div>
    
    <p className="text-muted-foreground text-lg leading-relaxed">
      Get ready for a personalized movie experience! We'll help you discover films you'll love.
    </p>

    <div className="grid md:grid-cols-3 gap-4 mt-8">
      <div className="bg-muted/50 rounded-xl p-6">
        <div className="p-2 bg-primary/10 rounded-lg w-12 h-12 mx-auto mb-3 flex items-center justify-center">
          <Sparkles className="w-6 h-6 text-primary" />
        </div>
        <h3 className="font-semibold text-foreground mb-2">Smart Recommendations</h3>
        <p className="text-sm text-muted-foreground">AI-powered suggestions based on your taste</p>
      </div>
      
      <div className="bg-muted/50 rounded-xl p-6">
        <div className="p-2 bg-primary/10 rounded-lg w-12 h-12 mx-auto mb-3 flex items-center justify-center">
          <Star className="w-6 h-6 text-primary" />
        </div>
        <h3 className="font-semibold text-foreground mb-2">Track Your Favorites</h3>
        <p className="text-sm text-muted-foreground">Build your watchlist and rate movies</p>
      </div>
      
      <div className="bg-muted/50 rounded-xl p-6">
        <div className="p-2 bg-primary/10 rounded-lg w-12 h-12 mx-auto mb-3 flex items-center justify-center">
          <Film className="w-6 h-6 text-primary" />
        </div>
        <h3 className="font-semibold text-foreground mb-2">Discover Hidden Gems</h3>
        <p className="text-sm text-muted-foreground">Find movies you never knew existed</p>
      </div>
    </div>
  </div>
);

const DemographicsStep = ({ demographics, setDemographics }) => (
  <div className="w-full max-w-md mx-auto space-y-6">
    <p className="text-center text-muted-foreground mb-8">
      Help us personalize your experience (optional)
    </p>

    <div className="space-y-4">
      <div>
        <label className="flex items-center gap-2 text-foreground font-medium mb-2">
          <Calendar className="w-4 h-4 text-primary" />
          Age Range
        </label>
        <select
          value={demographics.age}
          onChange={(e) => setDemographics(prev => ({ ...prev, age: e.target.value }))}
          className="w-full px-4 py-3 bg-background text-foreground rounded-xl border border-border focus:outline-none focus:ring-2 focus:ring-primary transition"
        >
          <option value="">Prefer not to say</option>
          <option value="18-24">18-24</option>
          <option value="25-34">25-34</option>
          <option value="35-44">35-44</option>
          <option value="45-54">45-54</option>
          <option value="55+">55+</option>
        </select>
      </div>

      <div>
        <label className="flex items-center gap-2 text-foreground font-medium mb-2">
          <MapPin className="w-4 h-4 text-primary" />
          Location
        </label>
        <input
          type="text"
          value={demographics.location}
          onChange={(e) => setDemographics(prev => ({ ...prev, location: e.target.value }))}
          placeholder="e.g., New York, USA (optional)"
          className="w-full px-4 py-3 bg-background text-foreground rounded-xl border border-border focus:outline-none focus:ring-2 focus:ring-primary transition"
        />
        <p className="text-xs text-muted-foreground mt-2">
          For informational purposes - may be used for regional recommendations in the future
        </p>
      </div>
    </div>

    <p className="text-xs text-muted-foreground text-center mt-6">
      💡 This information is saved locally and helps us understand your preferences better
    </p>
  </div>
);

const GenreStep = ({ selectedGenres, onLike, onDislike }) => (
  <div className="w-full max-w-3xl mx-auto">
    <p className="text-center text-muted-foreground mb-8">
      Select at least one genre you enjoy
    </p>

    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {GENRES.map((genre) => (
        <motion.div
          key={genre}
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className={`relative rounded-xl border-2 transition-all ${
            selectedGenres[genre] === 'like'
              ? 'border-primary bg-primary/10'
              : selectedGenres[genre] === 'dislike'
              ? 'border-destructive bg-destructive/10 opacity-50'
              : 'border-border bg-card hover:border-primary/50'
          }`}
        >
          <div className="p-4">
            <p className="text-center font-medium text-foreground mb-3">{genre}</p>
            <div className="flex gap-2 justify-center">
              <button
                onClick={() => onDislike(genre)}
                className={`p-2 rounded-lg transition-all ${
                  selectedGenres[genre] === 'dislike'
                    ? 'bg-destructive text-white'
                    : 'bg-muted hover:bg-destructive/20'
                }`}
              >
                <ThumbsDown className="w-4 h-4" />
              </button>
              <button
                onClick={() => onLike(genre)}
                className={`p-2 rounded-lg transition-all ${
                  selectedGenres[genre] === 'like'
                    ? 'bg-primary text-white'
                    : 'bg-muted hover:bg-primary/20'
                }`}
              >
                <ThumbsUp className="w-4 h-4" />
              </button>
            </div>
          </div>
        </motion.div>
      ))}
    </div>

    <div className="mt-6 text-center">
      <Badge variant="secondary" className="text-sm">
        {Object.keys(selectedGenres).filter(g => selectedGenres[g] === 'like').length} genres selected
      </Badge>
    </div>
  </div>
);

const RatingStep = ({ movies, movieRatings, onRate, onSkip, loading }) => {
  if (loading) {
    return (
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4"></div>
        <p className="text-muted-foreground">Loading movies...</p>
      </div>
    );
  }

  const ratedCount = Object.keys(movieRatings).length;

  return (
    <div className="w-full max-w-4xl mx-auto">
      <p className="text-center text-muted-foreground mb-2">
        Rate movies you've seen to help us understand your taste
      </p>
      <p className="text-center text-muted-foreground text-sm mb-8">
        Haven't seen these? No problem - you can skip this step!
      </p>

      <div className="grid md:grid-cols-2 gap-6 max-h-[400px] overflow-y-auto pr-2">
        {movies.map((movie) => {
          const isRated = movieRatings.hasOwnProperty(movie.id);
          
          return (
            <motion.div
              key={movie.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`bg-muted/50 rounded-xl p-4 flex gap-4 transition-all ${
                isRated ? 'ring-2 ring-primary/20' : ''
              }`}
            >
              {movie.poster_url && (
                <img
                  src={movie.poster_url}
                  alt={movie.title}
                  className="w-20 h-28 object-cover rounded-lg"
                />
              )}
              <div className="flex-1 flex flex-col">
                <h3 className="font-semibold text-foreground mb-1 line-clamp-2">
                  {movie.title}
                </h3>
                <p className="text-xs text-muted-foreground mb-3">
                  {movie.release_date ? new Date(movie.release_date).getFullYear() : 'N/A'}
                </p>
                <div className="flex gap-1 mb-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => onRate(movie.id, star)}
                      className="transition-transform hover:scale-110"
                    >
                      <Star
                        className={`w-5 h-5 ${
                          star <= (movieRatings[movie.id] || 0)
                            ? 'text-yellow-500 fill-yellow-500'
                            : 'text-muted-foreground/30'
                        }`}
                      />
                    </button>
                  ))}
                </div>
                {isRated && (
                  <button
                    onClick={() => onSkip(movie.id)}
                    className="text-xs text-muted-foreground hover:text-foreground transition-colors mt-auto"
                  >
                    Clear rating
                  </button>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      <div className="mt-6 text-center space-y-2">
        <Badge variant="secondary" className="text-sm">
          {ratedCount} {ratedCount === 1 ? 'movie' : 'movies'} rated
        </Badge>
        {ratedCount === 0 && (
          <p className="text-xs text-muted-foreground">
            💡 You can skip this step and rate movies later
          </p>
        )}
        {ratedCount > 0 && ratedCount < 3 && (
          <p className="text-xs text-primary">
            ✨ Great start! Rate a few more for better recommendations
          </p>
        )}
        {ratedCount >= 3 && (
          <p className="text-xs text-primary">
            🎉 Excellent! We have enough data for personalized recommendations
          </p>
        )}
      </div>
    </div>
  );
};

const CompletionStep = () => (
  <div className="text-center max-w-2xl mx-auto space-y-6">
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 15 }}
      className="p-4 bg-primary/10 rounded-full w-24 h-24 mx-auto flex items-center justify-center"
    >
      <Check className="w-12 h-12 text-primary" />
    </motion.div>
    
    <h3 className="text-2xl font-bold text-foreground">
      Your profile is ready!
    </h3>
    
    <p className="text-muted-foreground text-lg leading-relaxed">
      We've analyzed your preferences and are ready to show you personalized movie recommendations tailored just for you.
    </p>

    <div className="bg-primary/5 border border-primary/20 rounded-xl p-6 mt-8">
      <p className="text-foreground font-medium mb-2">What's next?</p>
      <ul className="text-sm text-muted-foreground space-y-2 text-left">
        <li className="flex items-start gap-2">
          <Check className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
          <span>Explore your personalized movie recommendations</span>
        </li>
        <li className="flex items-start gap-2">
          <Check className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
          <span>Build your watchlist and favorites collection</span>
        </li>
        <li className="flex items-start gap-2">
          <Check className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
          <span>Rate more movies to improve recommendations</span>
        </li>
      </ul>
    </div>
  </div>
);

export default Onboarding;

