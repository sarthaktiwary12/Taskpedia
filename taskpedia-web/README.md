# TASKPEDIA Web App

A SEO-optimized, high-performance web application for exploring the TASKPEDIA hierarchical task decomposition dataset for embodied AI.

## Features

✨ **Visually Rich UI**
- Modern, responsive design with Tailwind CSS
- Interactive data visualizations with D3.js and Recharts
- Hierarchical tree visualization
- Gradient backgrounds and smooth animations

🚀 **High Performance**
- Next.js 15 with App Router and Turbopack
- Static Site Generation (SSG) with Incremental Static Regeneration (ISR)
- Optimized images and code splitting
- Client-side caching and memoization

🔍 **SEO Optimized**
- Comprehensive meta tags and Open Graph tags
- Structured data (JSON-LD) for search engines
- Auto-generated sitemap.xml and robots.txt
- Semantic HTML and accessibility features

📊 **Data-Rich**
- Real-time search with fuzzy matching
- Advanced filtering (node type, domain)
- Interactive statistics dashboard
- Tree visualization with zoom controls

## Tech Stack

- **Framework**: Next.js 15 with TypeScript
- **Styling**: Tailwind CSS
- **Visualizations**: D3.js, Recharts
- **Icons**: Lucide React
- **Animations**: Framer Motion
- **Search**: Fuse.js (fuzzy search)

## Getting Started

### Prerequisites

- Node.js 18+ or higher
- TASKPEDIA CLI (for data export)

### Installation

1. **Install dependencies**:

```bash
cd visualize
npm install
```

2. **Export data from TASKPEDIA**:

```bash
# Make sure you're in the main project directory with taskpedia installed
npm run export-data
```

This will copy the TASKPEDIA dataset to `public/data/`.

3. **Set environment variables**:

Create a `.env.local` file:

```bash
NEXT_PUBLIC_BASE_URL=https://taskpedia.ai
GOOGLE_SITE_VERIFICATION=your_verification_code
```

4. **Run development server**:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
visualize/
├── app/                      # Next.js app router
│   ├── layout.tsx           # Root layout with SEO
│   ├── page.tsx             # Homepage
│   ├── explore/             # Search interface
│   ├── stats/               # Statistics dashboard
│   ├── api/                 # API routes
│   │   ├── search/          # Search endpoint
│   │   ├── nodes/           # Node data endpoint
│   │   ├── stats/           # Stats endpoint
│   │   └── domains/         # Domains endpoint
│   ├── sitemap.ts           # Auto-generated sitemap
│   └── robots.ts            # Robots.txt
├── components/              # React components
│   ├── Navigation.tsx       # Header navigation
│   ├── Footer.tsx           # Footer
│   ├── HeroSection.tsx      # Landing hero
│   ├── QuickSearch.tsx      # Search widget
│   ├── SearchInterface.tsx  # Advanced search
│   ├── TreeVisualization.tsx # D3 tree viz
│   ├── StatsDashboard.tsx   # Charts & metrics
│   ├── StatsOverview.tsx    # Stats cards
│   ├── FeaturedDomains.tsx  # Domain cards
│   ├── TaskCard.tsx         # Task display card
│   └── CTASection.tsx       # Call-to-action
├── lib/                     # Utilities
│   ├── data.ts              # Data access layer
│   └── utils.ts             # Helper functions
├── public/                  # Static assets
│   └── data/                # Exported TASKPEDIA data
│       ├── manifest.json    # Task node index
│       └── stats.json       # Dataset statistics
├── scripts/                 # Build scripts
│   └── export-data.js       # Data export script
└── package.json
```

## Data Integration

The web app reads data from `public/data/`:

1. **manifest.json**: Complete task hierarchy
2. **stats.json**: Pre-computed statistics

To update the data:

```bash
# From main project directory
cd ..
taskpedia export -f json

# Back to visualize
cd visualize
npm run export-data
```

## API Routes

### GET /api/search
Search tasks by query.

```
GET /api/search?q=grasp&limit=50
```

### GET /api/nodes/[id]
Get node details and children.

```
GET /api/nodes/work_healthcare%2Fnursing
```

### GET /api/stats
Get dataset statistics.

```
GET /api/stats
```

### GET /api/domains
List all domains.

```
GET /api/domains
```

## Building for Production

```bash
npm run build
npm start
```

The app will be optimized for production with:
- Minified JavaScript and CSS
- Optimized images
- Static page generation
- ISR for dynamic content

## Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Import to Vercel
3. Set environment variables
4. Deploy

### Docker

```bash
docker build -t taskpedia-web .
docker run -p 3000:3000 taskpedia-web
```

### Static Export

For fully static hosting:

```bash
npm run build
# Deploy the 'out' directory to any static host
```

## Performance Optimizations

- **Route-based code splitting**: Automatic in Next.js
- **Image optimization**: Next.js Image component
- **Font optimization**: Next.js Font
- **API caching**: ISR with 1-hour revalidation
- **Component lazy loading**: React.lazy and Suspense
- **Memoization**: React.memo for expensive components

## SEO Features

✅ Meta tags (title, description, keywords)
✅ Open Graph tags (Facebook, LinkedIn)
✅ Twitter Card tags
✅ Structured data (Schema.org Dataset)
✅ Sitemap.xml generation
✅ Robots.txt
✅ Canonical URLs
✅ Alt text for images
✅ Semantic HTML

## Browser Support

- Chrome (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Edge (last 2 versions)

## Development

### Running tests

```bash
npm test
```

### Linting

```bash
npm run lint
```

### Type checking

```bash
npx tsc --noEmit
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_BASE_URL` | Base URL for SEO | Yes |
| `GOOGLE_SITE_VERIFICATION` | Google Search Console | No |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under CC BY 4.0 - see the main TASKPEDIA license.

## Support

- Documentation: `/docs`
- GitHub Issues: https://github.com/anthropics/taskpedia/issues
- Email: contact@taskpedia.ai

## Acknowledgments

Built with the TASKPEDIA dataset for the embodied AI research community.
