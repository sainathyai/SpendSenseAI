# SpendSenseAI Admin Dashboard (React + TypeScript)

Modern, professional admin dashboard for SpendSenseAI operator portal.

## ✨ Features

- 🎨 **Modern UI** - Built with Ant Design
- 💬 **Floating Chat** - Query tool in bottom-right corner
- ✅ **Fixed Balance Display** - Shows correct net worth (assets - debts)
- 🎯 **Type-Safe** - Full TypeScript support
- ⚡ **Fast** - Vite for lightning-fast dev server
- 📱 **Responsive** - Works on all screen sizes

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

The dashboard will be available at `http://localhost:5173`

## 📋 Prerequisites

- Backend API running on `http://localhost:8000`
- Node.js 18+ and npm

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── api/          # API client
│   ├── components/   # Reusable components
│   ├── layouts/      # Layout components
│   ├── pages/        # Page components
│   ├── App.tsx       # Main app with routing
│   └── main.tsx      # Entry point
├── package.json
└── vite.config.ts
```

## 🎯 Key Components

### AllUsers Page
- Displays all customers with correct net worth calculation
- Sortable, filterable table
- Click any row to view details

### Floating Query Chat
- Click the purple chat button in bottom-right
- Ask natural language questions
- Get instant results from the database

### Admin Layout
- Dark sidebar navigation
- Gradient header
- Health status indicator

## 💡 Usage

### View All Users
1. Navigate to the dashboard
2. See all users in the table
3. **Net Worth** column shows: Assets - Debts (FIXED!)
4. Click any user to view details

### Use Query Tool
1. Click the floating chat icon (💬) in bottom-right
2. Type a question like:
   - `show balances for CUST000001`
   - `list customers`
   - `debt info for CUST000001`
3. Get instant results

## 🎨 Customization

### Change Colors
Edit `src/App.tsx`:
```typescript
colorPrimary: '#667eea', // Change this
```

### API Endpoint
The API URL is set to `http://localhost:8000` by default.

## 🐛 Troubleshooting

### Backend not connecting
- Make sure FastAPI backend is running on port 8000
- Check browser console for CORS errors

### Table shows wrong balances
- The balance calculation is fixed in the backend
- Make sure you're using the latest backend code

## 🔄 Migration from Streamlit

This React dashboard replaces the Streamlit UI:
- ✅ Keeps all FastAPI endpoints unchanged
- ✅ Better performance and UI
- ✅ Floating chat (impossible in Streamlit)
- ✅ Production-ready

## 📦 Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Ant Design** - UI components
- **React Query** - Data fetching
- **React Router** - Routing
- **Axios** - HTTP client

## 🚀 Production Build

```bash
npm run build
```

Outputs to `dist/` folder. Deploy to:
- Vercel
- Netlify
- AWS S3 + CloudFront
- Any static hosting

## 🎉 What's New vs Streamlit

| Feature | Streamlit | React Dashboard |
|---------|-----------|-----------------|
| Balance Display | ❌ Wrong | ✅ Fixed |
| Floating Chat | ❌ Impossible | ✅ Yes |
| Styling | ❌ Limited | ✅ Full control |
| Performance | 🐢 Slow | ⚡ Fast |
| Mobile | ❌ Poor | ✅ Responsive |
| Production Ready | ❌ No | ✅ Yes |
