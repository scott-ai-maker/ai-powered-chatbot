# AI Career Mentor Design System & Styling Guide

## 🎨 Design Philosophy

The AI Career Mentor follows a **modern, professional, and accessible** design system that emphasizes:
- **Trust & Reliability** through consistent visual elements
- **Clarity & Focus** with clean typography and spacing
- **Professional Aesthetics** suitable for career guidance
- **Accessibility** with proper contrast and keyboard navigation

## 🌈 Color Palette

### Primary Gradient
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```
- **Primary Blue**: `#667eea` - Main brand color, used for CTAs and highlights
- **Primary Purple**: `#764ba2` - Accent color, creates depth and sophistication

### Semantic Colors
```css
/* Success States */
--success-light: #f0fff4;
--success-main: #38a169;
--success-dark: #2f855a;

/* Error States */
--error-light: #fed7d7;
--error-main: #e53e3e;
--error-dark: #c53030;

/* Warning States */
--warning-light: #fefcbf;
--warning-main: #d69e2e;
--warning-dark: #b7791f;

/* Neutral Palette */
--gray-50: #f7f9fc;
--gray-100: #f1f3f4;
--gray-200: #e2e8f0;
--gray-300: #cbd5e0;
--gray-400: #a0aec0;
--gray-500: #718096;
--gray-600: #4a5568;
--gray-700: #2d3748;
--gray-800: #1a202c;
--gray-900: #171923;
```

## 📝 Typography

### Font Stack
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
  'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
```

### Font Sizes & Weights
```css
/* Headings */
h1: 2.5rem (40px) - font-weight: 700
h2: 2rem (32px) - font-weight: 600
h3: 1.5rem (24px) - font-weight: 600
h4: 1.25rem (20px) - font-weight: 600

/* Body Text */
body: 1rem (16px) - font-weight: 400
small: 0.875rem (14px) - font-weight: 400
tiny: 0.75rem (12px) - font-weight: 400
```

## 🧩 Component Library

### Buttons

#### Primary Button
```css
.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
}
```

#### Secondary Button
```css
.btn-secondary {
  background: white;
  color: #2d3748;
  border: 1px solid #e2e8f0;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: #f7f9fc;
  border-color: #667eea;
}
```

### Cards
```css
.card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  padding: 2rem;
}

.card-hover {
  transition: all 0.3s ease;
}

.card-hover:hover {
  transform: translateY(-5px);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
}
```

### Form Elements
```css
.input-field {
  width: 100%;
  padding: 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.2s ease;
}

.input-field:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.textarea {
  min-height: 50px;
  max-height: 120px;
  resize: vertical;
}
```

### Message Bubbles
```css
.message-bubble {
  max-width: 70%;
  padding: 1rem 1.5rem;
  border-radius: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-bubble.user {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message-bubble.assistant {
  background: #f7f9fc;
  color: #2d3748;
  border: 1px solid #e2e8f0;
}
```

## 📐 Layout & Spacing

### Grid System
```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
}

.grid {
  display: grid;
  gap: 2rem;
}

.grid-2 { grid-template-columns: repeat(2, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }
.grid-4 { grid-template-columns: repeat(4, 1fr); }
```

### Spacing Scale
```css
/* Spacing variables */
--space-xs: 0.25rem;   /* 4px */
--space-sm: 0.5rem;    /* 8px */
--space-md: 1rem;      /* 16px */
--space-lg: 1.5rem;    /* 24px */
--space-xl: 2rem;      /* 32px */
--space-2xl: 3rem;     /* 48px */
--space-3xl: 4rem;     /* 64px */
```

## 🎭 Animation & Transitions

### Standard Transitions
```css
/* Default transition for interactive elements */
transition: all 0.2s ease;

/* Hover elevations */
.hover-lift:hover {
  transform: translateY(-2px);
}

.hover-lift-strong:hover {
  transform: translateY(-5px);
}
```

### Loading Animations
```css
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.spinner {
  animation: spin 1s linear infinite;
}

.slide-in {
  animation: slideIn 0.3s ease-out;
}
```

## 📱 Responsive Design

### Breakpoints
```css
/* Mobile First Approach */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
```

### Mobile Optimizations
```css
@media (max-width: 768px) {
  .header h1 { font-size: 2rem; }
  .main-content { grid-template-columns: 1fr; }
  .message-bubble { max-width: 85%; }
  .btn { width: 100%; }
}
```

## ♿ Accessibility Guidelines

### Color Contrast
- **Normal text**: Minimum 4.5:1 contrast ratio
- **Large text**: Minimum 3:1 contrast ratio
- **Interactive elements**: Clearly distinguishable focus states

### Focus Management
```css
.focus-visible {
  outline: 2px solid #667eea;
  outline-offset: 2px;
}

.skip-link {
  position: absolute;
  top: -40px;
  left: 6px;
  background: #667eea;
  color: white;
  padding: 8px;
  text-decoration: none;
  transition: top 0.3s;
}

.skip-link:focus {
  top: 6px;
}
```

### Semantic HTML
- Use proper heading hierarchy (h1 → h2 → h3)
- Include `alt` attributes for images
- Use `aria-label` for icon-only buttons
- Implement proper form labels

## 🧪 Component Usage Examples

### Chat Interface
```jsx
<div className="chat-container">
  <div className="header">
    <h1>🤖 AI Career Mentor</h1>
    <p>Your intelligent guide to AI engineering careers</p>
  </div>
  
  <div className="main-content">
    <div className="sidebar">
      <h3>💡 Try These Questions</h3>
      {/* Sample questions */}
    </div>
    
    <div className="chat-area">
      <div className="messages-container">
        {/* Messages */}
      </div>
      
      <div className="input-area">
        {/* Input form */}
      </div>
    </div>
  </div>
</div>
```

### File Upload
```jsx
<div className="file-upload-area drag-over">
  <FileText size={24} />
  <div className="file-upload-text">
    Drag & drop documents or click to upload
  </div>
</div>
```

## 🎯 Best Practices

### Do's ✅
- Use the gradient for primary actions and headers
- Maintain consistent spacing using the spacing scale
- Apply hover effects to interactive elements
- Use semantic colors for status indicators
- Test with screen readers and keyboard navigation

### Don'ts ❌
- Don't use colors alone to convey information
- Don't create custom colors outside the palette
- Don't use gradients for body text or small elements
- Don't skip focus states on interactive elements
- Don't use animation for critical information

## 🔧 Implementation Notes

### CSS Custom Properties
```css
:root {
  --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --border-radius-sm: 8px;
  --border-radius-md: 12px;
  --border-radius-lg: 20px;
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 8px 16px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 20px 40px rgba(0, 0, 0, 0.1);
}
```

### Dark Mode Considerations
Future implementation should consider:
- Inverting the gradient for dark backgrounds
- Adjusting gray scale for dark mode
- Maintaining accessibility contrast ratios

---

This design system ensures consistent, professional, and accessible user experiences across the AI Career Mentor application while maintaining the sophisticated gradient aesthetic that matches the broader portfolio brand.