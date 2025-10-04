import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  User, 
  Mail, 
  MapPin, 
  Calendar,
  ThumbsUp, 
  ThumbsDown,
  Save,
  Check,
  X,
  Settings as SettingsIcon
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { useAuth } from '../context/AuthContext';
import { updateUserProfile, getCurrentUser } from '../services/api';

const GENRES = [
  'Action', 'Adventure', 'Animation', 'Comedy', 'Crime',
  'Documentary', 'Drama', 'Fantasy', 'Horror', 'Mystery',
  'Romance', 'Science Fiction', 'Thriller', 'War', 'Western'
];

const Settings = () => {
  const { user, setUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState(null);

  // Profile fields
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [age, setAge] = useState('');
  const [location, setLocation] = useState('');

  // Genre preferences
  const [genrePreferences, setGenrePreferences] = useState({});

  useEffect(() => {
    if (user) {
      setUsername(user.username || '');
      setEmail(user.email || '');
      setAge(user.age || '');
      setLocation(user.location || '');

      // Load genre preferences
      if (user.genre_preferences) {
        const prefs = {};
        Object.entries(user.genre_preferences).forEach(([genre, score]) => {
          if (score > 0) {
            prefs[genre] = 'like';
          } else if (score < 0) {
            prefs[genre] = 'dislike';
          }
        });
        setGenrePreferences(prefs);
      }
    }
  }, [user]);

  const handleGenreToggle = (genre, action) => {
    setGenrePreferences(prev => {
      const current = prev[genre];
      if (current === action) {
        // Clicking the same button removes the preference
        const newPrefs = { ...prev };
        delete newPrefs[genre];
        return newPrefs;
      } else {
        // Set new preference
        return { ...prev, [genre]: action };
      }
    });
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      setError(null);
      setSaveSuccess(false);

      // Prepare genre preferences in backend format
      const genrePrefsFormatted = {};
      Object.entries(genrePreferences).forEach(([genre, preference]) => {
        if (preference === 'like') {
          genrePrefsFormatted[genre] = 1;
        } else if (preference === 'dislike') {
          genrePrefsFormatted[genre] = -1;
        }
      });

      const updateData = {
        username: username !== user.username ? username : undefined,
        email: email !== user.email ? email : undefined,
        age: age ? parseInt(age) : null,
        location: location || null,
        genre_preferences: Object.keys(genrePrefsFormatted).length > 0 ? genrePrefsFormatted : {}
      };

      // Remove undefined values
      Object.keys(updateData).forEach(key => 
        updateData[key] === undefined && delete updateData[key]
      );

      const response = await updateUserProfile(updateData);
      
      // Update user context
      const updatedUser = await getCurrentUser();
      setUser(updatedUser.data);

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error('Error updating profile:', err);
      setError(err.response?.data?.detail || 'Failed to update profile');
      setTimeout(() => setError(null), 5000);
    } finally {
      setLoading(false);
    }
  };

  const hasChanges = () => {
    if (username !== user.username) return true;
    if (email !== user.email) return true;
    if (age !== (user.age || '')) return true;
    if (location !== (user.location || '')) return true;

    // Check genre preferences
    const currentPrefs = {};
    if (user.genre_preferences) {
      Object.entries(user.genre_preferences).forEach(([genre, score]) => {
        if (score > 0) currentPrefs[genre] = 'like';
        else if (score < 0) currentPrefs[genre] = 'dislike';
      });
    }
    if (JSON.stringify(currentPrefs) !== JSON.stringify(genrePreferences)) return true;

    return false;
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-3 bg-primary/10 rounded-xl">
              <SettingsIcon className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-foreground">Settings</h1>
              <p className="text-muted-foreground">Manage your account and preferences</p>
            </div>
          </div>
        </div>

        {/* Success/Error Messages */}
        {saveSuccess && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-green-500/10 border border-green-500/20 rounded-xl flex items-center gap-2 text-green-600"
          >
            <Check className="w-5 h-5" />
            <span>Profile updated successfully!</span>
          </motion.div>
        )}

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-xl flex items-center gap-2 text-destructive"
          >
            <X className="w-5 h-5" />
            <span>{error}</span>
          </motion.div>
        )}

        {/* Profile Information Section */}
        <Card className="p-6 mb-6 border-border">
          <h2 className="text-xl font-semibold text-foreground mb-6 flex items-center gap-2">
            <User className="w-5 h-5 text-primary" />
            Profile Information
          </h2>

          <div className="space-y-4">
            {/* Username */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-foreground mb-2">
                <User className="w-4 h-4 text-primary" />
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                className="w-full px-4 py-3 bg-background text-foreground rounded-xl border border-border focus:outline-none focus:ring-2 focus:ring-primary transition"
                minLength={3}
                maxLength={50}
              />
            </div>

            {/* Email */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-foreground mb-2">
                <Mail className="w-4 h-4 text-primary" />
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="w-full px-4 py-3 bg-background text-foreground rounded-xl border border-border focus:outline-none focus:ring-2 focus:ring-primary transition"
              />
            </div>

            {/* Age */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-foreground mb-2">
                <Calendar className="w-4 h-4 text-primary" />
                Age
              </label>
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                placeholder="Enter your age (optional)"
                className="w-full px-4 py-3 bg-background text-foreground rounded-xl border border-border focus:outline-none focus:ring-2 focus:ring-primary transition"
                min={13}
                max={120}
              />
            </div>

            {/* Location */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-foreground mb-2">
                <MapPin className="w-4 h-4 text-primary" />
                Location
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g., New York, USA (optional)"
                className="w-full px-4 py-3 bg-background text-foreground rounded-xl border border-border focus:outline-none focus:ring-2 focus:ring-primary transition"
                maxLength={100}
              />
            </div>
          </div>
        </Card>

        {/* Genre Preferences Section */}
        <Card className="p-6 mb-6 border-border">
          <h2 className="text-xl font-semibold text-foreground mb-2 flex items-center gap-2">
            <ThumbsUp className="w-5 h-5 text-primary" />
            Genre Preferences
          </h2>
          <p className="text-sm text-muted-foreground mb-6">
            Tell us which genres you love and which ones you'd rather skip. This helps us personalize your recommendations.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {GENRES.map((genre) => (
              <motion.div
                key={genre}
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className={`relative rounded-xl border-2 transition-all ${
                  genrePreferences[genre] === 'like'
                    ? 'border-primary bg-primary/10'
                    : genrePreferences[genre] === 'dislike'
                    ? 'border-destructive bg-destructive/10 opacity-50'
                    : 'border-border bg-card hover:border-primary/50'
                }`}
              >
                <div className="p-4">
                  <p className="text-center font-medium text-foreground mb-3">{genre}</p>
                  <div className="flex gap-2 justify-center">
                    <button
                      onClick={() => handleGenreToggle(genre, 'dislike')}
                      className={`p-2 rounded-lg transition-all ${
                        genrePreferences[genre] === 'dislike'
                          ? 'bg-destructive text-white'
                          : 'bg-muted hover:bg-destructive/20'
                      }`}
                      title="Dislike"
                    >
                      <ThumbsDown className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleGenreToggle(genre, 'like')}
                      className={`p-2 rounded-lg transition-all ${
                        genrePreferences[genre] === 'like'
                          ? 'bg-primary text-white'
                          : 'bg-muted hover:bg-primary/20'
                      }`}
                      title="Like"
                    >
                      <ThumbsUp className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="mt-6 flex gap-4 justify-center">
            <Badge variant="secondary" className="text-sm">
              {Object.values(genrePreferences).filter(p => p === 'like').length} genres liked
            </Badge>
            <Badge variant="secondary" className="text-sm">
              {Object.values(genrePreferences).filter(p => p === 'dislike').length} genres disliked
            </Badge>
          </div>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end gap-4">
          <Button
            onClick={handleSave}
            disabled={!hasChanges() || loading}
            className="px-8 py-6 rounded-xl bg-foreground text-background hover:bg-foreground/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-background mr-2"></div>
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
