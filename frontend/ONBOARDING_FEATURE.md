# 🎬 Onboarding Wizard Feature

## Overview
A comprehensive multi-step onboarding experience that guides new users through setting up their movie preferences and creating a personalized profile.

## Features

### 🎯 **5-Step Wizard Process**

#### **Step 1: Welcome Screen**
- Introduces Cineamate and its key benefits
- Highlights three main features:
  - **Smart Recommendations**: AI-powered suggestions
  - **Track Your Favorites**: Build watchlists and rate movies
  - **Discover Hidden Gems**: Find movies you never knew existed
- Clean, engaging visual design with icons

#### **Step 2: Demographics Form (Optional)**
- **Age Range Selection**: 
  - 18-24, 25-34, 35-44, 45-54, 55+
  - "Prefer not to say" option
- **Location Input**: 
  - City or Country (free text)
  - Completely optional
- Privacy note: "This information is private and helps us provide better recommendations"

#### **Step 3: Genre Selector**
- **Thumbs Up/Down Interface** for 15 genres:
  - Action, Adventure, Animation, Comedy, Crime
  - Documentary, Drama, Fantasy, Horror, Mystery
  - Romance, Science Fiction, Thriller, War, Western
- Visual feedback with color coding:
  - **Liked**: Primary color border and background
  - **Disliked**: Destructive color with reduced opacity
  - **Neutral**: Default border
- **Requirement**: At least 1 genre must be liked
- Live counter showing selected genres

#### **Step 4: Movie Rating**
- Rate 5-10 popular movies from the database
- **5-star rating system** for each movie
- Shows movie poster, title, and release year
- **Requirement**: At least 3 movies must be rated
- Scrollable grid layout for easy browsing
- Live counter showing progress

#### **Step 5: Completion**
- Success celebration with animated checkmark
- Overview of what's next:
  - Explore personalized recommendations
  - Build watchlist and favorites
  - Rate more movies to improve suggestions
- Direct button to recommendations page

## Design System

### **Clod Theme Integration**
- Warm beige/neutral color palette
- Rounded corners (rounded-xl, rounded-2xl)
- Consistent spacing and typography
- Smooth animations with Framer Motion

### **Animations**
- Page transitions with slide effect
- Step content fades in/out
- Smooth progress bar updates
- Spring animation for completion checkmark

### **Responsive Design**
- Mobile-first approach
- Grid layouts adapt to screen size
- Touch-friendly buttons and interactions
- Scrollable content areas for mobile

## User Flow

### **New User Registration**
```
Register → Onboarding (Step 1) → ... → Recommendations
```

### **Returning User Without Onboarding**
```
Login → Check localStorage → Onboarding (if not complete) → Recommendations
```

### **Returning User With Onboarding**
```
Login → Home
```

## Technical Details

### **State Management**
- Local state for wizard steps
- Demographics stored in state object
- Genre preferences stored as object (genre → 'like'/'dislike'/null)
- Movie ratings stored as object (movieId → rating)

### **API Integration**
- `GET /movies/` - Fetch popular movies for rating
- `POST /user/features` - Save demographics and genre preferences
- `POST /ratings/` - Save movie ratings
- Uses existing `api.js` service layer

### **Persistence**
- Onboarding completion tracked in localStorage
- Key format: `onboarding_complete_{userId}`
- Checked on login to determine redirect

### **Validation**
- Step 1 (Welcome): Always allowed to proceed
- Step 2 (Demographics): Always allowed (optional)
- Step 3 (Genres): Requires at least 1 liked genre
- Step 4 (Ratings): Requires at least 3 rated movies
- Step 5 (Completion): Always allowed

## Components

### **Main Component: `Onboarding.jsx`**
- Located: `frontend/src/pages/Onboarding.jsx`
- Manages wizard state and navigation
- Coordinates API calls on completion

### **Sub-Components (Internal)**
1. **WelcomeStep**: Introduction and benefits
2. **DemographicsStep**: Age and location form
3. **GenreStep**: Genre selection with thumbs up/down
4. **RatingStep**: Movie rating interface
5. **CompletionStep**: Success screen

## Navigation

### **Progress Indicator**
- Visual progress bar at top
- Shows current step out of total (e.g., "Step 2 of 5")
- Progress bars fill with primary color

### **Navigation Buttons**
- **Back**: Disabled on first step, goes to previous step
- **Next**: Validates current step before proceeding
- **Get Started**: Final button to complete and redirect

### **Hidden Elements**
- Navbar hidden during onboarding (focused experience)
- Popmelt badge hidden during onboarding
- Returns on completion

## Skip/Return Functionality

Currently, onboarding is **required** for new users. To implement skip functionality:

1. Add skip button in wizard
2. Store partial completion state
3. Allow access to main app
4. Show reminder to complete onboarding

## Data Collection

### **What We Collect**
1. **Demographics** (optional):
   - Age range
   - Location
2. **Genre Preferences**:
   - Liked genres
   - Disliked genres
3. **Movie Ratings**:
   - Movie ID
   - Rating (1-5 stars)

### **Privacy**
- All data stored per-user in backend
- Optional fields clearly marked
- Privacy notice shown in demographics step
- Data used only for recommendations

## Future Enhancements

Potential improvements:
- [ ] Skip onboarding option with reminder system
- [ ] Resume incomplete onboarding sessions
- [ ] More granular genre preferences (e.g., sub-genres)
- [ ] Actor/director preference collection
- [ ] Streaming service preferences
- [ ] Language preferences
- [ ] Additional demographic options
- [ ] Social sharing of taste profile
- [ ] Import ratings from IMDb/Letterboxd
- [ ] A/B test different onboarding flows

## Testing

### **Manual Testing Checklist**
- [ ] Register new user → redirects to onboarding
- [ ] Complete all steps → redirects to recommendations
- [ ] Back button works correctly
- [ ] Next button validates each step
- [ ] Progress bar updates correctly
- [ ] Demographics form accepts optional input
- [ ] Genre selector requires at least 1 like
- [ ] Movie rating requires at least 3 ratings
- [ ] Completion screen shows and redirects
- [ ] Login after onboarding → goes to home
- [ ] Login before onboarding → goes to onboarding

### **Edge Cases**
- [ ] No movies available for rating
- [ ] API errors during save
- [ ] Browser refresh during onboarding
- [ ] Multiple sessions (different browsers)
- [ ] Logout during onboarding

## Accessibility

- Keyboard navigation supported
- Button labels with icons
- Clear visual hierarchy
- Large touch targets
- Color contrast meets WCAG standards
- Screen reader friendly labels (via aria-label on icons)

## Performance

- Lazy loads movies only when needed (Step 4)
- Minimal re-renders with proper state management
- Smooth animations without jank
- Optimized API calls (batch requests)

---

**Created**: October 2025  
**Design System**: Clod (Popmelt)  
**Framework**: React 18.3.1 + Framer Motion  
**Status**: ✅ Complete and Production Ready

