# Quick Deploy to Render - Checklist

## Pre-Deployment (Do this first!)

### 1. Commit all changes to Git

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin master
```

### 2. Get your Anthropic API Key

1. Go to [https://console.anthropic.com](https://console.anthropic.com)
2. Navigate to API Keys section
3. Copy your API key (starts with `sk-ant-...`)
4. **Keep it safe** - you'll need it during deployment

---

## Render Deployment (Choose One Method)

### 🚀 Method 1: Blueprint Deploy (EASIEST - Recommended)

1. **Go to Render:** [https://dashboard.render.com](https://dashboard.render.com)

2. **Click:** New → Blueprint

3. **Connect Repository:**
   - Select: `transaction-monitoring` repository
   - Render will detect `render.yaml` automatically

4. **Configure:**
   - Service Group Name: `transaction-monitoring`
   - Click "Apply"

5. **Add API Key:**
   - When prompted, enter your `ANTHROPIC_API_KEY`
   - Click "Apply" to start deployment

6. **Wait for deployment** (~5-10 minutes for first deploy)

7. **Initialize Database:**
   - Go to your web service
   - Click "Shell" tab
   - Run:
     ```bash
     python -c "from app.models.database import init_db; init_db()"
     ```

8. **Done!** Access your app at the provided URL

---

### 🔧 Method 2: Manual Deploy (More Control)

#### Step A: Create Database

1. Click: New → PostgreSQL
2. Settings:
   - Name: `transaction-monitoring-db`
   - Region: Oregon (or closest to you)
   - Plan: Free
3. Click "Create Database"
4. Wait ~2 minutes for provisioning
5. **Copy the Internal Database URL** (you'll need this)

#### Step B: Create Web Service

1. Click: New → Web Service
2. Connect your GitHub repository: `transaction-monitoring`
3. Configure:

   **Basic Settings:**
   - Name: `transaction-monitoring-dashboard`
   - Region: Oregon (same as database)
   - Branch: `master`
   - Runtime: Python 3

   **Build Settings:**
   - Build Command:
     ```
     pip install --upgrade pip && pip install -r requirements-render.txt
     ```
   - Start Command:
     ```
     streamlit run streamlit_app/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
     ```

   **Environment Variables:**
   Click "Add Environment Variable" for each:

   | Key | Value |
   |-----|-------|
   | DATABASE_URL | (Paste Internal Database URL from Step A) |
   | ANTHROPIC_API_KEY | (Your API key from pre-deployment) |
   | PYTHON_VERSION | 3.11.0 |

4. Click "Create Web Service"

5. Wait for deployment (~5-10 minutes)

6. Initialize database (same as Method 1, Step 7)

---

## Post-Deployment Verification

### Test Your Deployment

1. **Access the URL** provided by Render (e.g., `https://your-app.onrender.com`)

2. **Check login page loads:**
   - Should see "Transaction Screening System" header
   - Login form should be visible

3. **Test database connection:**
   - Go to Render Dashboard → Web Service → Shell
   - Run: `python -c "from config.settings import DATABASE_URL; print('Database connected!' if DATABASE_URL else 'No database')"`

4. **Check logs for errors:**
   - Render Dashboard → Web Service → Logs
   - Look for any red error messages

### Common First-Time Issues

❌ **"Application Error"**
- Check logs for specific error
- Verify all environment variables are set
- Ensure database is initialized

❌ **"Cannot connect to database"**
- Verify `DATABASE_URL` environment variable is set
- Check database is running (green status in dashboard)

❌ **Page loads but features don't work**
- Check `ANTHROPIC_API_KEY` is set correctly
- Initialize database if not done yet

---

## Updating Your App

Every time you push to GitHub, Render automatically redeploys:

```bash
# Make changes
git add .
git commit -m "Your update message"
git push origin master

# Render auto-deploys in 2-3 minutes
```

---

## Free Tier Limitations

⚠️ **Important to know:**

1. **App spins down after 15 min of inactivity**
   - First request after spin-down: ~30-60 seconds to wake up
   - Solution: Upgrade to Starter plan ($7/mo) for always-on

2. **Free PostgreSQL expires after 90 days**
   - You'll need to upgrade or migrate data
   - Starter PostgreSQL: $7/month for persistent storage

3. **750 hours/month limit**
   - Should be sufficient for testing/development
   - Upgrade to Starter for unlimited hours

---

## Upgrade to Production (When Ready)

For a production-ready setup:

1. **Upgrade Web Service to Starter:** $7/month
   - Always-on (no spin-down)
   - Better performance
   - Unlimited hours

2. **Upgrade Database to Starter:** $7/month
   - Persistent (doesn't expire)
   - Better performance
   - Automatic backups

**Total production cost: $14/month**

---

## Next Steps After Deployment

- [ ] Test all dashboard features
- [ ] Add sample data for testing
- [ ] Configure user roles (if applicable)
- [ ] Set up monitoring (optional: UptimeRobot for free pings)
- [ ] Add custom domain (optional, available on paid plans)
- [ ] Enable automatic deploys from GitHub

---

## Need Help?

- **Render Logs:** Dashboard → Service → Logs
- **Render Docs:** [render.com/docs](https://render.com/docs)
- **Streamlit Docs:** [docs.streamlit.io](https://docs.streamlit.io)
- **Full Guide:** See `RENDER_DEPLOYMENT.md` for detailed troubleshooting

---

**Happy Deploying! 🚀**
