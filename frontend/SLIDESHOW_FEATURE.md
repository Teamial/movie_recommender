# Hero Movie Slideshow Feature

## Overview
Added a beautiful auto-playing movie slideshow to the hero section that displays top-rated movies with smooth fade transitions.

## Features

### 🎬 **Auto-Playing Slideshow**
- **4-second interval** between slides (customizable)
- **Smooth fade transitions** using Framer Motion
- **Pause on hover** - users can pause to read details
- **Auto-resume** when mouse leaves

### 🎨 **Design (Clod Theme)**
- **Rounded-xl corners** matching the design system
- **Gradient overlay** from foreground color for readability
- **Primary color progress bar** at the top
- **Backdrop blur effects** for modern aesthetic

### 🎯 **Navigation**
- **Dot indicators** at the bottom
  - Active: Wide pill shape (w-6)
  - Inactive: Small dots (w-2)
  - Hover effects for interactivity
- **Click to jump** to any slide
- **Progress bar** showing time until next slide

### 📊 **Content Display**
Each slide shows:
- Movie poster as background
- Star rating (if available)
- Movie title (large, bold)
- Release year
- "Featured" label for movies without ratings

### 🔄 **Data Source**
- **Fetches top 5 rated movies** from your API via `getTopRated(5)`
- **Fallback movies** with beautiful cinematic images if API unavailable
- **Graceful error handling** - always shows content

## Technical Details

### Components
```jsx
<MovieSlideshow autoPlayInterval={4000} />
```

### Props
- `autoPlayInterval` (optional): Time in ms between slides (default: 4000)

### Dependencies
- `framer-motion` - Smooth animations
- `@/lib/utils` - cn() utility for class merging

### Responsive Behavior
- **Mobile**: Smaller text, compact padding
- **Tablet**: Medium sizing
- **Desktop**: Full large text and spacing

## Animations

### Slide Transitions
```javascript
initial={{ opacity: 0 }}
animate={{ opacity: 1 }}
exit={{ opacity: 0 }}
duration: 0.8s with custom easing
```

### Content Entrance
```javascript
initial={{ y: 20, opacity: 0 }}
animate={{ y: 0, opacity: 1 }}
delay: 0.3s for stagger effect
```

### Progress Bar
```javascript
Linear animation from 0% to 100%
Resets on each slide
Pauses when hovering
```

## Color Scheme (Clod)

### Light Mode
- **Overlay**: Dark foreground gradient
- **Text**: Light background color
- **Progress**: Primary terracotta
- **Dots**: Background color (white)

### Gradient
```css
from-foreground/90 via-foreground/40 to-transparent
```

## User Experience

### Interactions
1. **Automatic advance** - No user action needed
2. **Pause on hover** - Read movie details
3. **Manual navigation** - Click dots to jump
4. **Visual feedback** - Progress bar shows timing

### Accessibility
- `aria-label` on navigation buttons
- Alt text on images
- Keyboard accessible (dot buttons)
- Reduced motion support through Framer Motion

## Integration

The slideshow is integrated into `HeroSection.jsx`:
```jsx
<div className="aspect-[4/3] md:aspect-auto h-[320px] md:h-[420px]">
  <MovieSlideshow />
</div>
```

## Customization

### Change interval
```jsx
<MovieSlideshow autoPlayInterval={5000} />
```

### Modify movies
Edit `FALLBACK_MOVIES` array or adjust API call in `fetchMovies()`

### Adjust styling
All classes use Tailwind with clod design tokens:
- `rounded-xl`
- `shadow-lg`
- `bg-primary`
- `text-foreground`

## Future Enhancements

Possible additions:
- [ ] Arrow navigation buttons
- [ ] Touch swipe gestures
- [ ] Lazy load images
- [ ] Video backgrounds
- [ ] Click to view movie details modal
- [ ] Filter by genre/category

---

**Fully Responsive** • **Accessible** • **Performance Optimized** • **Clod Design System**

