# LeaseHawk MVP - Vercel Deployment Guide

## Quick Deploy Instructions

### 1. Prerequisites
- Git repository committed (✅ Done)
- Vercel account ([signup here](https://vercel.com))
- Neon database account ([signup here](https://neon.tech)) - Optional, can use SQLite for demo

### 2. Deploy to Vercel

```bash
# Login to Vercel (opens browser)
npx vercel login

# Deploy the application
npx vercel --yes

# Set up environment variables (if using Neon/PostgreSQL)
npx vercel env add DATABASE_URL
```

### 3. Environment Variables

If you want to use a Neon PostgreSQL database (recommended for production):

1. **Create Neon Database:**
   - Go to https://neon.tech
   - Create a new project
   - Copy the connection string

2. **Add to Vercel:**
   ```bash
   # Add your Neon database URL
   npx vercel env add DATABASE_URL
   # Paste: postgresql://username:password@your-neon-endpoint/database-name
   ```

3. **Deploy with new environment:**
   ```bash
   npx vercel --prod
   ```

### 4. What's Included

✅ **Backend API** (`/api/` routes):
- `/api/gsa-pipeline/` - GSA opportunities with urgency scoring
- `/api/dashboard-stats/` - Dashboard statistics
- `/prospectuses/`, `/properties/`, `/matches/` - Data endpoints

✅ **Frontend** (React-like vanilla JS):
- Interactive GSA opportunities dashboard
- Map visualization with property matches
- Urgency indicators (High/Medium/Low priority)
- Real-time match scoring

✅ **Sample Data** (seeded in database):
- 5 GSA prospectuses ($4M total pipeline value)
- 5 matching properties with geographic distribution
- 9 pre-scored property matches

### 5. Database Options

**Option A: SQLite (Demo/Development)**
- Works immediately with included sample data
- No additional setup required
- Perfect for demonstration

**Option B: Neon PostgreSQL (Production)**
- Scalable cloud database
- Automatic backups and scaling
- Run the seed script after deployment:
  ```bash
  # After deployment, seed the Neon database
  curl -X POST https://your-app.vercel.app/api/seed-database
  ```

### 6. Verify Deployment

After deployment:
1. Visit your Vercel URL
2. Check `/api/status` endpoint
3. Verify GSA opportunities load in the dashboard
4. Test the interactive map functionality

### 7. Next Steps

- **Add Your Data:** Use the API endpoints to add real GSA prospectus data
- **Customize:** Modify filters and scoring algorithms
- **Scale:** Connect to production data sources
- **Monitor:** Set up Vercel analytics and monitoring

---

## Architecture Overview

```
Frontend (Static)           Backend (Serverless)         Database
├── index.html         →    ├── /api/index.py       →    ├── SQLite (dev)
├── app.js                  ├── GSA Pipeline API           └── Neon PG (prod)
├── style.css               ├── Dashboard Stats
└── maps integration        └── CRUD endpoints
```

Your LeaseHawk MVP is now ready for production! 🚀