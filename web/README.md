# MCP Dashboard

A modern, responsive dashboard application built with React and Tailwind CSS, inspired by Cake's equity management platform.

## Features

- 🎨 **Beautiful UI** - Modern, clean interface with Tailwind CSS
- 📱 **Responsive Design** - Works seamlessly on desktop and mobile
- 🔄 **Collapsible Sidebar** - Expandable navigation with icon-only mode
- 📊 **Data Visualization** - Interactive ownership charts and statistics
- 🚀 **Fast Development** - Built with Create React App for quick iteration

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

1. Navigate to the web directory:
```bash
cd web
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

The app will open in your browser at [http://localhost:3000](http://localhost:3000)

### Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App (one-way operation)

## Project Structure

```
web/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── App.js              # Main dashboard component
│   ├── index.js            # Application entry point
│   └── index.css           # Global styles with Tailwind
├── package.json            # Dependencies and scripts
└── tailwind.config.js      # Tailwind CSS configuration
```

## Features Overview

### Navigation Routes

The dashboard includes the following navigation routes:
- Getting Started
- Dashboard (default view)
- Cap Table
- Equity Plans
- Tools
- Communication
- Data Room
- Secondaries
- Documents
- Company

### Dashboard Components

1. **Company Stats** - Key metrics including stakeholders, shares, securities, valuation, and share price
2. **Ownership Visualization** - Interactive donut chart showing equity distribution
3. **Activity Feed** - Recent actions and notifications
4. **Funding Rounds** - Fundraising progress and goals
5. **Options Pool** - Total options allocation tracking

## Customization

### Tailwind CSS

The project uses Tailwind CSS for styling. You can customize the theme in `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        // Add custom colors
      },
    },
  },
}
```

### Icons

All icons are implemented as inline SVG components using Heroicons design patterns. No external icon libraries are required.

## Technologies Used

- **React** - JavaScript library for building user interfaces
- **Tailwind CSS** - Utility-first CSS framework
- **Create React App** - React application bootstrapping tool
- **PostCSS** - CSS transformation tool
- **Autoprefixer** - CSS vendor prefixing

## Browser Support

This project supports all modern browsers:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

This project is part of the forge-mcptools workspace.

## Contributing

Feel free to submit issues and enhancement requests!

