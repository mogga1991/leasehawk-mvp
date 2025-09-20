# 🚀 Deploy LeaseHawk to Railway

## Quick Deploy Commands

```bash
# 1. Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# 2. Login to Railway
railway login

# 3. Navigate to project root
cd leasehawk-mvp

# 4. Initialize Railway project
railway init
# Choose: "Create new project"
# Name: "leasehawk-mvp"

# 5. Add PostgreSQL database
railway add
# Select: "PostgreSQL"

# 6. Deploy your code
railway up

# 7. Set environment variables
railway variables set OPENAI_API_KEY=your-openai-key-here
railway variables set ANTHROPIC_API_KEY=your-anthropic-key-here
railway variables set NOTION_TOKEN=your-notion-token-here
railway variables set NOTION_PROSPECTUS_DB=your-prospectus-db-id
railway variables set NOTION_PROPERTY_DB=your-property-db-id

# 8. Load initial data
railway run python backend/load_production_data.py

# 9. Get your live URL
railway open
```

## Your Live URLs

After deployment, you'll have:
- **Main App**: `https://leasehawk-mvp-production.up.railway.app`
- **API Docs**: `https://leasehawk-mvp-production.up.railway.app/docs`
- **Opportunities**: `https://leasehawk-mvp-production.up.railway.app/opportunities/`

## Test Your Deployment

```bash
# Test the API
curl https://your-app-url.railway.app/

# Check opportunities
curl https://your-app-url.railway.app/opportunities/

# Upload a PDF
curl -X POST https://your-app-url.railway.app/upload-pdf-to-notion/ \
  -F "file=@path/to/your/prospectus.pdf"
```

## Monitor Your App

```bash
# View logs
railway logs

# Check status
railway status

# Restart if needed
railway restart
```

## Your $239K Opportunities

Once deployed, your app will show:
- **Franklin County VA**: $4.23M/year → $84,600 fee
- **Salt Lake City VA**: $7.76M/year → $155,200 fee
- **Total Potential**: $239,800

## Share Your Platform

Send this to investors, partners, or property owners:
"Check out our live government lease intelligence platform at [your-railway-url]"

## Next Steps

1. Share your URL with potential partners
2. Upload more GSA PDFs through the web interface  
3. Add properties to test matching
4. Monitor usage in Railway dashboard
5. Scale up as you win contracts!

🎯 **Ready to win your first government contract!**