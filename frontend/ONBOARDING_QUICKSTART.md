# 🚀 Onboarding Quick Start Guide

## Testing the Onboarding Flow

### 1. **Start the Development Server**
```bash
cd frontend
npm run dev
```

### 2. **Register a New User**
1. Navigate to `/register`
2. Fill in username, email, and password
3. Click "Sign Up"
4. **You'll be automatically redirected to the onboarding wizard**

### 3. **Complete the Onboarding Steps**

#### **Step 1: Welcome** ✨
- Read about the benefits
- Click "Next" to continue

#### **Step 2: Demographics** 👤
- **Optional**: Select your age range
- **Optional**: Enter your location
- Click "Next" (can skip both fields)

#### **Step 3: Genre Selection** 🎭
- Click thumbs up (👍) on genres you like
- Click thumbs down (👎) on genres you dislike
- **Requirement**: Select at least 1 liked genre
- Click "Next"

#### **Step 4: Rate Movies** ⭐
- Rate movies by clicking stars (1-5)
- **Requirement**: Rate at least 3 movies
- Movies are fetched from your database
- Click "Next"

#### **Step 5: Completion** ✅
- Review what's next
- Click "Get Started"
- **You'll be redirected to recommendations**

## What Happens Behind the Scenes

### Data Saved to Backend
```javascript
// 1. Demographics (if provided)
POST /user/features
{
  age: "25-34",
  location: "New York"
}

// 2. Genre Preferences
POST /user/features
{
  preferred_genres: "Action,Comedy,Thriller",
  disliked_genres: "Horror,Documentary"
}

// 3. Movie Ratings (for each rated movie)
POST /ratings/?user_id={userId}
{
  movie_id: 550,
  rating: 5
}
```

### Local Storage
```javascript
// Onboarding completion flag
localStorage.setItem(`onboarding_complete_{userId}`, 'true');
```

## Testing Returning Users

### User Who Completed Onboarding
1. Login with existing credentials
2. **Redirects to Home** (/)

### User Who Skipped/Never Completed Onboarding
1. Login with credentials
2. Checks: `localStorage.getItem('onboarding_complete_{userId}')`
3. **Redirects to Onboarding** (/onboarding) if not found

### Reset Onboarding for Testing
```javascript
// In browser console
localStorage.removeItem('onboarding_complete_1'); // Replace 1 with user ID
// Logout and login again
```

## Customization Options

### Change Number of Movies to Rate
```javascript
// In Onboarding.jsx, line 28
const response = await getMovies({ 
  page: 1, 
  page_size: 15,  // Change from 10 to 15
  sort_by: 'popularity'
});
```

### Change Minimum Required Ratings
```javascript
// In Onboarding.jsx, line 82
case 3: return Object.keys(movieRatings).length >= 5; // Change from 3 to 5
```

### Add/Remove Genres
```javascript
// In Onboarding.jsx, lines 19-23
const GENRES = [
  'Action', 'Adventure', 'Animation', 'Comedy', 'Crime',
  'Documentary', 'Drama', 'Fantasy', 'Horror', 'Mystery',
  'Romance', 'Science Fiction', 'Thriller', 'War', 'Western',
  'Family', 'Musical' // Add more genres
];
```

### Change Step Titles
```javascript
// In Onboarding.jsx, steps array
const steps = [
  { id: 'welcome', title: 'Your Custom Title', ... },
  // ...
];
```

## Troubleshooting

### Issue: "No movies available for rating"
**Solution**: Ensure your database has movies with `sort_by='popularity'`
```bash
# Run the movie pipeline to fetch movies
python movie_pipeline.py
```

### Issue: "Onboarding keeps showing on login"
**Cause**: localStorage flag not set correctly
**Solution**: 
1. Check browser console for errors during completion
2. Verify API endpoints are working
3. Clear localStorage and try again

### Issue: "Backend API errors"
**Cause**: `/user/features` endpoint might not exist
**Solution**: 
1. Check if backend has this endpoint
2. If not, remove demographics saving in `completeOnboarding()`
3. Or create the endpoint in backend

### Issue: "Ratings not saving"
**Cause**: `/ratings/` endpoint error
**Solution**:
1. Check backend logs
2. Verify user authentication token
3. Ensure movie IDs are valid

## Development Tips

### Skip Onboarding During Development
Add this to `Onboarding.jsx` for testing:
```javascript
// Add a dev-only skip button
{process.env.NODE_ENV === 'development' && (
  <Button onClick={() => navigate('/recommendations')}>
    Skip (Dev Only)
  </Button>
)}
```

### Debug State
Add console logs:
```javascript
useEffect(() => {
  console.log('Current Step:', currentStep);
  console.log('Selected Genres:', selectedGenres);
  console.log('Movie Ratings:', movieRatings);
}, [currentStep, selectedGenres, movieRatings]);
```

### Test with Mock Data
```javascript
// Skip API calls during development
const fetchPopularMovies = async () => {
  setMovies([
    { id: 1, title: 'Test Movie', poster_url: '...', release_date: '2024-01-01' },
    // Add more mock movies
  ]);
};
```

## UI Customization

### Change Colors
Uses Clod design system variables:
- Primary: `--primary` (terracotta)
- Background: `--background` (white)
- Foreground: `--foreground` (charcoal)

### Adjust Animations
```javascript
// In motion.div
transition={{ duration: 0.5 }} // Change from 0.3
```

### Modify Layout
```javascript
// Make wizard wider
className="w-full max-w-6xl" // Change from max-w-4xl
```

## Production Checklist

Before deploying:
- [ ] Test all 5 steps thoroughly
- [ ] Verify API endpoints work
- [ ] Test on mobile devices
- [ ] Check accessibility (keyboard nav)
- [ ] Test with slow network
- [ ] Verify error handling
- [ ] Test with empty database
- [ ] Check localStorage persistence
- [ ] Test logout during onboarding
- [ ] Verify analytics tracking (if added)

## Need Help?

Common files to check:
- **Main Component**: `frontend/src/pages/Onboarding.jsx`
- **Routing**: `frontend/src/App.jsx`
- **Auth Context**: `frontend/src/context/AuthContext.jsx`
- **API Service**: `frontend/src/services/api.js`
- **Login Flow**: `frontend/src/pages/Login.jsx`
- **Register Flow**: `frontend/src/pages/Register.jsx`

---

Happy onboarding! 🎉

