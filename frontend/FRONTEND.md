# Angular Frontend - Pole Sport AI Training Generator

## Features

- **Responsive Design**: Mobile-first responsive interface
- **Standalone Components**: Modern Angular 17+ standalone components
- **Reactive Forms**: Form validation and state management
- **Services**: API integration with HttpClient
- **State Management**: Local storage integration

## Project Structure

```
src/
├── app/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── header.component.ts
│   │   │   └── footer.component.ts
│   │   ├── home/
│   │   ├── user-profile/
│   │   ├── exercise-list/
│   │   └── training-plan/
│   ├── services/
│   │   ├── api.service.ts
│   │   └── training-plan.service.ts
│   ├── models/
│   │   └── index.ts
│   ├── app.component.ts
│   └── app.routes.ts
├── environments/
├── styles.scss
└── main.ts
```

## Components

### Home
- Hero section with CTA
- Features showcase
- Database statistics
- Call-to-action buttons

### User Profile
- Personal information form
- Pole sport experience selector
- Availability and goals selection
- Health information input
- Form validation

### Exercise List
- Search and filtering
- Category selection
- Level filtering
- Pole sport specific filtering
- Pagination
- Detailed exercise information

### Training Plan
- Plan overview
- Exercise list with specs
- Intensity visualization
- Exercise instructions
- Save/Download functionality

## Services

### ApiService
- Exercise API endpoints
- Training plan generation
- CRUD operations

### TrainingPlanService
- State management
- Local storage integration
- Current plan management
- Saved plans management

## Styling

- SCSS with variables
- CSS Grid and Flexbox
- Mobile-responsive design
- Gradient accents
- Smooth animations

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## Configuration

### API URL
Configure in `src/environments/environment.ts`:
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1'
};
```

### Backend Integration
The frontend connects to FastAPI backend at `/api/v1` endpoints.

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Lazy loading not configured yet
- Build optimization available
- Tree-shaking enabled
- Minification in production

## Future Enhancements

- [ ] Lazy loading for components
- [ ] Service workers for offline support
- [ ] Progressive web app capabilities
- [ ] Dark mode toggle
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] User authentication UI
- [ ] Social sharing features
