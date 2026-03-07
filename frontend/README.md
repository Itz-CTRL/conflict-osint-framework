# Frontend - OSINT Investigation Platform

React-based frontend for military-grade OSINT (Open Source Intelligence) investigations with interactive network visualization, advanced filtering, and real-time progress tracking.

## 📋 Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Components](#components)
- [Utilities](#utilities)
- [Custom Hooks](#custom-hooks)
- [API Integration](#api-integration)
- [Styling & Themes](#styling--themes)
- [Getting Started](#getting-started)
- [Usage Examples](#usage-examples)

## 🎯 Features

### Core Investigation Features
- **Username-based Search**: Primary input with optional email/phone auto-discovery
- **Flexible Filtering**: Platform, location, account type, verification status
- **Progress Tracking**: 
  - Light Scan: 6 phases (~15 seconds)
  - Deep Scan: 9 phases (~60-120 seconds)
- **Dual Scan Modes**:
  - **Light Scan**: Quick overview across major platforms
  - **Deep Scan**: Comprehensive analysis with network mapping and behavior analysis

### Graph Visualization
- **Interactive Vis.js Network**:
  - Central target node with connected entities
  - 8 node types (profile, platform, email, phone, keyword, mention, location, org)
  - 7 edge types with confidence scores and labels
  - Zoom, pan, fit, and reset controls
  - Hover metadata and tooltips
  
- **Advanced Filtering**:
  - Filter by node type
  - Filter by edge type
  - Confidence/weight threshold slider
  - Dynamic legend

- **Export Options**:
  - PNG (canvas screenshot)
  - SVG (vector graphic)
  - JSON (graph data)
  - CSV (node/edge table)
  - GraphML (network analysis format)

### Tab Structure
- **Overview**: Case summary and quick stats
- **Username**: Individual username findings
- **Emails**: Associated email addresses
- **Phones**: Phone numbers and intelligence
- **Mentions**: References in social content
- **Graph**: Interactive network visualization
- **Risk**: Risk assessment and scoring
- **Report**: Downloadable executive reports

### Design & UX
- **Responsive Design**: Mobile-first approach (768px/1024px breakpoints)
- **Dark/Light Modes**: System preference detection with toggle
- **Accessibility**: Semantic HTML, focus states, keyboard navigation
- **Performance Optimized**: CSS animations, lazy loading, debouncing

## 📁 Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/           # React components
│   │   ├── AutocompleteInput.jsx
│   │   ├── CasePage.jsx
│   │   ├── CountryCodePicker.jsx
│   │   ├── Dashboard.jsx
│   │   ├── GraphView.jsx
│   │   ├── GraphView.css
│   │   ├── Header.jsx
│   │   ├── NetworkGraph.jsx
│   │   ├── NewInvestigation.jsx
│   │   ├── NewInvestigation.css
│   │   ├── PhoneLookup.jsx
│   │   ├── ReportViewer.jsx
│   │   ├── RiskScore.jsx
│   │   ├── Sidebar.jsx
│   │   ├── ThemeButton.jsx
│   │   ├── Ticker.jsx
│   │   └── UI.jsx
│   │
│   ├── contexts/             # React Context
│   │   └── CaseContext.jsx
│   │
│   ├── hooks/               # Custom hooks
│   │   └── useCustomHooks.js
│   │
│   ├── utils/               # Utility functions
│   │   ├── apiClient.js      # API communication layer
│   │   ├── constants.js      # Configuration and constants
│   │   ├── formValidation.js # Form validation
│   │   ├── graphUtils.js     # Graph filtering and analysis
│   │   └── themeUtils.js     # Theme management
│   │
│   ├── App.jsx              # Root component
│   ├── index.js             # Entry point
│   ├── index.css            # Global styles
│   └── themes.js            # Theme definitions
│
├── package.json
└── README.md (this file)
```

## 🧩 Components

### NewInvestigation (`NewInvestigation.jsx`)
Create new OSINT investigations with advanced filtering.

**Props**: None (uses CaseContext)

**State Management**:
```javascript
{
  username: string,        // Required
  email: string,          // Optional
  phone: string,          // Optional with dialCode
  scanType: 'light'|'deep',
  filters: {
    platforms: string[],
    location: string,
    accountType: string,
    verified: string
  },
  loading: boolean,
  progress: 0-100,
  phase: string,
  error: string
}
```

**Key Features**:
- AutocompleteInput for username suggestions
- CountryCodePicker for international phone format
- Platform multi-select grid (15 platforms)
- Location dropdown (12 countries)
- Account type and verification toggles
- Real-time progress tracking with phase updates
- Form validation with error display

**Styling**: `NewInvestigation.css` (500+ lines)
- Responsive form sections with animations
- Platform grid (repeat auto-fill minmax 140px)
- Progress bar with gradient fill
- Dark mode support

### GraphView (`GraphView.jsx`)
Interactive network visualization of investigation results.

**Props**: None (uses CaseContext)

**Features**:
- Vis.js network canvas
- 7 control buttons (zoom, pan, fit, reset)
- Node type filtering (8 types)
- Edge type filtering (7 types)
- Confidence threshold slider
- Hover metadata tooltips
- Node selection details panel
- Export options (PNG/SVG/JSON/CSV/GraphML)
- Legend with color coding

**Styling**: `GraphView.css` (600+ lines)
- Full-height responsive canvas
- Control toolbar with active states
- Filter tags with toggle styling
- Hover tooltips and legends
- Dark mode color scheme

### CasePage (`CasePage.jsx`)
Main investigation view with tab navigation.

**Features**:
- Tab navigation between 8 views
- Case information header
- Dynamic content loading
- Error boundaries

### Dashboard (`Dashboard.jsx`)
Overview of recent investigations and statistics.

**Features**:
- Recent investigations list
- Quick stats (total cases, success rate, etc.)
- Quick actions (new investigation, view reports)

### Header (`Header.jsx`)
Top navigation bar.

**Features**:
- Logo and title
- Theme toggle (light/dark)
- User profile menu
- Search bar

## 🛠️ Utilities

### `apiClient.js` - API Communication Layer
Centralized HTTP client for backend communication.

```javascript
import { api } from '../utils/apiClient';

// Investigate
const inv = await api.createInvestigation(username, email, phone);
const investigation = await api.getInvestigation(caseId);
const result = await api.getInvestigationResult(caseId);
await api.startLightScan(caseId);
await api.startDeepScan(caseId);

// Phone Intel
const phone = await api.phoneUniqueLookup(phoneNumber);
const phones = await api.phoneBatchLookup([...]);
const valid = await api.validatePhone(phoneNumber);

// Graph
const graph = await api.getGraph(caseId);
const stats = await api.getGraphStatistics(caseId);
const nodes = await api.getGraphConnectedNodes(caseId, nodeId, depth);
const nodeDetail = await api.getNodeDetails(caseId, nodeId);
const exported = await api.exportGraph(caseId, format);

// Reports
await api.generateReport(caseId, format);
const report = await api.getReport(caseId, format);
```

**Error Handling**:
```javascript
try {
  const data = await api.getInvestigation(caseId);
} catch (error) {
  console.log(error.status);    // HTTP status
  console.log(error.message);   // Error message
  console.log(error.details);   // Additional details
}
```

### `constants.js` - Configuration
Platform list, countries, scan phases, risk scores, and more.

```javascript
import {
  PLATFORMS,
  COUNTRIES,
  SCAN_TYPES,
  RISK_SCORES,
  CASE_TABS,
  API_CONFIG,
} from '../utils/constants';
```

**Available Constants**:
- `PLATFORMS`: 15 social/messaging platforms
- `COUNTRIES`: 12 countries with dial codes
- `ACCOUNT_TYPES`: Personal, business, bot
- `VERIFICATION_STATUS`: All, verified, not-verified
- `SCAN_TYPES`: Light/deep with phase definitions
- `RISK_SCORES`: Critical/high/medium/low/minimal
- `INVESTIGATION_STATUS`: Pending/running/completed/failed
- `ENTITY_TYPES`: Graph visualization node types
- `CASE_TABS`: Navigation tabs
- `EXPORT_FORMATS`: JSON/CSV/PNG/SVG/GraphML
- `API_CONFIG`: Base URL, timeouts, poll intervals

### `formValidation.js` - Form Validation
Comprehensive validation for investigation forms.

```javascript
import {
  validateEmail,
  validatePhone,
  validateUsername,
  validateInvestigationForm,
  sanitizeInput,
  normalizePhone,
  estimateSearchDifficulty,
  getSearchTips,
} from '../utils/formValidation';

// Validate individual fields
const emailValidation = validateEmail('user@example.com');
const phoneValidation = validatePhone('5551234567', '+1');
const usernameValidation = validateUsername('john_doe');

// Validate entire form
const result = validateInvestigationForm(formData);
if (result.isValid) {
  // Submit form
} else {
  console.log(result.errors); // {username: "...", email: "..."}
}

// Utilities
const normalized = normalizePhone('555-1234567', '+1'); // +15551234567
const difficulty = estimateSearchDifficulty(formData); // 1-10
const tips = getSearchTips(formData); // Array of helpful tips
```

### `graphUtils.js` - Graph Analysis
Filtering, analysis, and export utilities for network graphs.

```javascript
import {
  filterNodesByType,
  filterEdgesByConfidence,
  getConnectedNodes,
  calculateGraphStats,
  findHubNodes,
  findShortestPath,
  exportGraph,
} from '../utils/graphUtils';

// Filtering
const nodes = filterNodesByType(allNodes, ['profile', 'email']);
const edges = filterEdgesByConfidence(allEdges, minConfidence=0.5);

// Analysis
const stats = calculateGraphStats(nodes, edges);
// Returns: {nodeCount, edgeCount, density, avgDegree, isolatedCount, riskDistribution}

const hubs = findHubNodes(nodes, edges, topN=5);
const path = findShortestPath(nodeId1, nodeId2, nodes, edges);

// Export
const json = exportGraph(nodes, edges, 'json');
const csv = exportGraph(nodes, edges, 'csv');
const graphml = exportGraph(nodes, edges, 'graphml');
```

### `themeUtils.js` - Theme Management
Light/dark mode switching and color utilities.

```javascript
import {
  getCurrentTheme,
  saveTheme,
  toggleTheme,
  getThemeColor,
  initializeTheme,
  getRiskColor,
  getVisualizationPalette,
} from '../utils/themeUtils';

// Initialize on app load
initializeTheme();

// Get/set themes
const current = getCurrentTheme(); // 'light' or 'dark'
saveTheme('dark');
toggleTheme();

// Get colors
const primaryColor = getThemeColor('primary');
const riskColor = getRiskColor(45); // Based on score
const palette = getVisualizationPalette(); // Array of 10 colors

// CSS variables available:
// --color-primary, --color-accent, --color-success, --color-danger
// --color-background, --color-surface, --color-border
// --color-text, --color-textMuted, etc.
```

## 🎣 Custom Hooks

### `useForm` - Form State Management
Handles form values, errors, validation, and submission.

```javascript
const {
  values,
  errors,
  touched,
  isSubmitting,
  handleChange,
  handleBlur,
  handleSubmit,
  setFieldValue,
  setFieldError,
  resetForm,
} = useForm(initialValues, onSubmit);

// In JSX
<input
  name="username"
  value={values.username}
  onChange={handleChange}
  onBlur={handleBlur}
/>
{touched.username && errors.username && (
  <span className="error">{errors.username}</span>
)}
<button onClick={handleSubmit}>Submit</button>
```

### `useApi` - API Call Management
Handles loading, error, and retry logic for API calls.

```javascript
const { data, loading, error, execute, refetch } = useApi(
  api.getInvestigation,
  {
    immediate: false,
    retryCount: 3,
    onSuccess: (data) => console.log('Success:', data),
    onError: (error) => console.log('Error:', error),
  }
);

// Trigger manually
await execute(caseId);

// Refetch with same parameters
refetch();

// In component
{loading && <Spinner />}
{error && <ErrorMessage error={error} />}
{data && <Data data={data} />}
```

### `useDebounce` - Debounce Values
Optimize search inputs and real-time filters.

```javascript
const [username, setUsername] = useState('');
const debouncedUsername = useDebounce(username, 500);

// Use debouncedUsername for autocomplete search
useEffect(() => {
  if (debouncedUsername) {
    api.searchUsernames(debouncedUsername);
  }
}, [debouncedUsername]);
```

### Other Hooks
- **`useLocalStorage`**: Persist state to localStorage
- **`useAsync`**: Generic async state management
- **`usePagination`**: Pagination state and navigation
- **`useToggle`**: Boolean state toggle
- **`useFilter`**: Filter items with multiple criteria
- **`useUndoRedo`**: History undo/redo support

## 🔌 API Integration

### Backend Endpoints
All endpoints documented in `apiClient.js`:

```
POST   /api/investigation/create                 - Create investigation
GET    /api/investigation/{id}                   - Get investigation status
GET    /api/investigation/{id}/result            - Get scan results
POST   /api/investigation/scan/{id}/light        - Start light scan
POST   /api/investigation/scan/{id}/deep         - Start deep scan
GET    /api/investigation/list                   - List investigations

POST   /api/phone/lookup                         - Lookup single phone
POST   /api/phone/batch-lookup                   - Lookup multiple phones
GET    /api/phone/validate/{phone}               - Validate phone format

GET    /api/graph/{id}                           - Get graph data
GET    /api/graph/{id}/statistics                - Get graph stats
GET    /api/graph/{id}/connected/{nodeId}        - Get connected nodes
GET    /api/graph/{id}/node/{nodeId}             - Get node details
GET    /api/graph/{id}/export/{format}           - Export graph

POST   /api/report/{id}/generate                 - Generate report
GET    /api/report/{id}/{format}                 - Download report
```

### Request/Response Examples

**Create Investigation**:
```javascript
// Request
api.createInvestigation('john_doe', 'john@example.com', '5551234567');

// Response
{
  "status": "success",
  "data": {
    "case_id": "uuid-...",
    "created_at": "2024-03-04T10:30:00Z"
  }
}
```

**Get Investigation**:
```javascript
// Response while running
{
  "status": "running",
  "progress": 45,
  "phase": "Network Mapping",
  "scan_type": "deep"
}

// Response when complete
{
  "status": "completed",
  "progress": 100,
  "phase": "Complete",
  "data": { /* findings */ }
}
```

**Get Graph**:
```javascript
{
  "status": "success",
  "data": {
    "nodes": [
      {
        "id": "john_doe",
        "label": "john_doe",
        "type": "profile",
        "risk_score": 45,
        "platforms": ["twitter", "github"]
      }
    ],
    "edges": [
      {
        "from": "john_doe",
        "to": "john@example.com",
        "type": "USES_EMAIL",
        "confidence": 0.95
      }
    ],
    "metadata": { /* graph info */ }
  }
}
```

## 🎨 Styling & Themes

### CSS Architecture
- **Global**: `index.css` - global styles, resets, utility classes
- **Component**: Component.css - scoped component styles
- **Responsive**: Mobile-first with breakpoints at 768px and 1024px
- **Dark Mode**: `@media (prefers-color-scheme: dark)` for auto switching
- **Animations**: slideDown, spin, fadeIn, pulse

### CSS Variables (Theme Colors)
```css
:root {
  --color-primary: #3b82f6;
  --color-accent: #f59e0b;
  --color-success: #10b981;
  --color-danger: #ef4444;
  --color-warning: #f97316;
  --color-background: #ffffff;
  --color-surface: #ffffff;
  --color-border: #e5e7eb;
  --color-text: #111827;
  --color-textMuted: #6b7280;
  /* ... many more */
}
```

### Class Naming
- `.component` - main component container
- `.component-section` - major sections
- `.component-item` - individual items
- `.is-active / .is-loading / .is-error` - state classes
- `.btn-primary / .btn-secondary` - button variants

### Responsive Design
```css
/* Mobile first (default) */
.container { width: 100%; }

/* Tablet and up */
@media (min-width: 768px) {
  .container { width: 750px; }
  .grid { grid-template-columns: 1fr 1fr; }
}

/* Desktop and up */
@media (min-width: 1024px) {
  .container { width: 960px; }
  .grid { grid-template-columns: 1fr 1fr 1fr; }
}
```

## 🚀 Getting Started

### Prerequisites
- Node.js 14+ and npm/yarn
- React 18+
- Backend API running on http://localhost:5000

### Installation

1. **Install dependencies**:
```bash
cd frontend
npm install
# or
yarn install
```

2. **Create .env file**:
```bash
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_ENV=development
```

3. **Start development server**:
```bash
npm start
# or
yarn start
```

The app will open at `http://localhost:3000`

### Build for Production
```bash
npm run build
# or
yarn build
```

## 📚 Usage Examples

### Create and Run Investigation
```javascript
import { api } from './utils/apiClient';

async function runInvestigation() {
  try {
    // Create investigation
    const inv = await api.createInvestigation('john_doe', 'john@example.com');
    const caseId = inv.data.case_id;

    // Start deep scan
    await api.startDeepScan(caseId);

    // Poll for completion
    let status = 'running';
    while (status === 'running') {
      const investigation = await api.getInvestigation(caseId);
      status = investigation.data.status;
      console.log(`Progress: ${investigation.data.progress}%`);
      await new Promise(r => setTimeout(r, 2000));
    }

    // Get results
    const results = await api.getInvestigationResult(caseId);
    const graph = await api.getGraph(caseId);
    const stats = await api.getGraphStatistics(caseId);

    console.log('Investigation complete!', {
      findings: results.data,
      graph: graph.data,
      stats: stats.data,
    });
  } catch (error) {
    console.error('Investigation failed:', error);
  }
}
```

### Validate Investigation Form
```javascript
import { validateInvestigationForm, getSearchTips } from './utils/formValidation';

const formData = {
  username: 'john_doe',
  email: 'john@example.com',
  phone: '5551234567',
  dialCode: '+1',
  scanType: 'deep',
  filters: {
    platforms: ['twitter', 'github'],
    location: 'US',
    accountType: 'personal',
    verified: 'any',
  },
};

const validation = validateInvestigationForm(formData);
if (validation.isValid) {
  const tips = getSearchTips(formData);
  console.log('Search tips:', tips);
  // Submit form
} else {
  console.log('Validation errors:', validation.errors);
}
```

### Filter and Analyze Graph
```javascript
import {
  filterNodesByType,
  calculateGraphStats,
  findHubNodes,
} from './utils/graphUtils';

const graphData = await api.getGraph(caseId);
const { nodes, edges } = graphData.data;

// Filter to email nodes only
const emailNodes = filterNodesByType(nodes, ['email']);

// Get stats
const stats = calculateGraphStats(nodes, edges);
console.log(`Network density: ${stats.density}`);
console.log(`Average degree: ${stats.avgDegree}`);
console.log(`Risk distribution:`, stats.riskDistribution);

// Find most connected nodes
const hubs = findHubNodes(nodes, edges, topN=10);
console.log('Hub nodes:', hubs.map(n => n.label));
```

### Toggle Theme
```javascript
import { toggleTheme, getRiskColor } from './utils/themeUtils';

// Toggle between light/dark
const newTheme = toggleTheme();
console.log('Theme switched to:', newTheme);

// Get color for risk score
const color = getRiskColor(75); // High risk (red-orange)
document.querySelector('.risk-indicator').style.backgroundColor = color;
```

## 📦 Dependencies

- **React 18+**: Core UI library
- **React Router**: Navigation
- **Vis.js/Vis-network**: Graph visualization
- **Fetch API**: Built-in HTTP client (no external dependency)

## 🔒 Security

- Input sanitization via `formValidation.js`
- CORS handling via API client
- XSS prevention through React's built-in escaping
- CSRF tokens supported in API client (if backend requires)

## 📄 License

Part of the Conflict OSINT Framework. See root LICENSE file.

## 🤝 Contributing

1. Follow React best practices
2. Use component composition
3. Implement proper error handling
4. Add responsive design support
5. Include dark mode compatibility
6. Test with different browsers

## 📞 Support

For backend integration issues, see `backend/README.md` and `backend/SERVICE_INTEGRATION_GUIDE.md`.

For API documentation, see `docs/SDD.md` (System Design Document).
