# Render Deployment Guide for Transaction Monitoring Dashboard

## Overview
This guide walks you through deploying the Transaction Monitoring Dashboard on Render.com.

**Why Render over Heroku?**
- No 500MB slug limit (Render allows larger applications)
- Free PostgreSQL database included
- Better free tier for learning/testing
- Easier deployment process

---

## Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository
2. **Render Account** - Sign up at [render.com](https://render.com)
3. **Anthropic API Key** - Required for AI features

---

## Deployment Steps

### Step 1: Push Code to GitHub

```bash
# If not already done
git add .
git commit -m "Prepare for Render deployment"
git push origin master
```

### Step 2: Create Render Account

1. Go to [https://render.com](https://render.com)
2. Sign up using your GitHub account (recommended)
3. Authorize Render to access your repositories

### Step 3: Deploy Using Blueprint (Easiest Method)

1. **Connect Repository:**
   - Click "New" → "Blueprint"
   - Select your GitHub repository: `transaction-monitoring`
   - Render will auto-detect the `render.yaml` file

2. **Configure Services:**
   - Service Group Name: `transaction-monitoring`
   - Click "Apply"

3. **Set Environment Variables:**
   - Render will prompt for `ANTHROPIC_API_KEY`
   - Add your API key from [https://console.anthropic.com](https://console.anthropic.com)
   - Click "Apply" to start deployment

### Step 4: Manual Deployment (Alternative Method)

If you prefer manual setup:

#### A. Create PostgreSQL Database

1. Click "New" → "PostgreSQL"
2. Settings:
   - **Name:** `transaction-monitoring-db`
   - **Database:** `transaction_monitoring`
   - **User:** (auto-generated)
   - **Region:** Oregon (or your preferred region)
   - **Plan:** Free
3. Click "Create Database"
4. Wait for database to provision (~2 minutes)

#### B. Create Web Service

1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Settings:
   - **Name:** `transaction-monitoring-dashboard`
   - **Region:** Oregon (same as database)
   - **Branch:** `master` (or your main branch)
   - **Runtime:** Python 3
   - **Build Command:**
     ```bash
     pip install --upgrade pip && pip install -r requirements-render.txt
     ```
   - **Start Command:**
     ```bash
     streamlit run streamlit_app/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
     ```
   - **Plan:** Free (or Starter for better performance)

4. **Environment Variables:**
   Add these in the "Environment" section:

   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | (Internal connection string from your database) |
   | `ANTHROPIC_API_KEY` | Your Anthropic API key |
   | `PYTHON_VERSION` | 3.11.0 |

5. Click "Create Web Service"

---

## Step 5: Initialize Database

Once deployed, you need to initialize the database:

1. Go to your web service dashboard
2. Click "Shell" tab
3. Run these commands:

```bash
python -c "from app.models.database import init_db; init_db()"
```

Or if you have seed data:

```bash
python generate_test_data.py
```

---

## Step 6: Access Your Dashboard

1. Your app will be available at: `https://transaction-monitoring-dashboard.onrender.com`
2. Wait for initial deployment (first deploy takes 5-10 minutes)
3. Subsequent deploys are faster (~2-3 minutes)

---

## Configuration Details

### Database Connection

The app automatically uses PostgreSQL on Render via the `DATABASE_URL` environment variable.

**Local SQLite (Development):**
```python
DATABASE_URL = "sqlite:///./transaction_monitoring.db"
```

**Render PostgreSQL (Production):**
```python
DATABASE_URL = "postgresql://user:password@host:5432/database"
```

This is handled automatically in [config/settings.py](config/settings.py:5).

### Environment Variables Required

| Variable | Purpose | Where to Get |
|----------|---------|--------------|
| `DATABASE_URL` | PostgreSQL connection | Auto-populated by Render |
| `ANTHROPIC_API_KEY` | AI recommendations | [console.anthropic.com](https://console.anthropic.com) |
| `PYTHON_VERSION` | Python runtime | Set to `3.11.0` |

---

## Optimization Tips

### 1. **Reduce Build Size**

We created `requirements-render.txt` which excludes TensorFlow/Keras to stay under size limits:

- **Original `requirements.txt`:** ~2GB with TensorFlow
- **Optimized `requirements-render.txt`:** ~500MB without deep learning

### 2. **Free Tier Limitations**

Render Free tier includes:
- ✅ 512 MB RAM
- ✅ Free PostgreSQL (90 days, then expires)
- ⚠️ Spins down after 15 minutes of inactivity
- ⚠️ 750 hours/month (may spin down near month-end)

**To avoid spin-down:** Upgrade to Starter plan ($7/month) for always-on service.

### 3. **Database Persistence**

Free PostgreSQL expires after 90 days. For production:
- Upgrade to Starter PostgreSQL ($7/month) for persistence
- Or use external database (e.g., ElephantSQL, Supabase)

---

## Troubleshooting

### Issue: Build Fails with "Out of Memory"

**Solution:** The optimized `requirements-render.txt` should prevent this. If still failing:

1. Remove unused packages:
   ```txt
   # Comment out in requirements-render.txt
   # shap>=0.43.0
   # lime>=0.2.0.1
   ```

2. Or upgrade to a paid plan with more memory

### Issue: App Shows "Application Error"

**Check logs:**
1. Go to your Render dashboard
2. Click on your web service
3. Click "Logs" tab
4. Look for error messages

**Common fixes:**
- Verify `DATABASE_URL` is set correctly
- Check all environment variables are configured
- Ensure database is initialized (see Step 5)

### Issue: Database Connection Errors

**Verify connection:**
```bash
# In Render Shell
python -c "from config.settings import DATABASE_URL; print(DATABASE_URL)"
```

**Fix:** Ensure `DATABASE_URL` environment variable is set and database is running.

### Issue: App is Slow to Load

**Causes:**
- Free tier spins down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds

**Solutions:**
- Upgrade to Starter plan ($7/month) for always-on
- Use external uptime monitoring (e.g., UptimeRobot) to ping every 10 minutes

---

## Cost Breakdown

### Free Tier (Testing/Development)
- Web Service: Free (with spin-down)
- PostgreSQL: Free (90 days)
- **Total: $0/month** (first 90 days)

### Production Setup (Recommended)
- Web Service: Starter ($7/month)
- PostgreSQL: Starter ($7/month)
- **Total: $14/month**

---

## Updating Your Deployment

Render automatically deploys when you push to your connected branch:

```bash
# Make changes locally
git add .
git commit -m "Update dashboard features"
git push origin master

# Render auto-deploys (takes 2-3 minutes)
```

### Manual Deploy

1. Go to Render dashboard
2. Click on your web service
3. Click "Manual Deploy" → "Deploy latest commit"

---

## Security Best Practices

1. **Never commit API keys** - Always use environment variables
2. **Use HTTPS** - Render provides free SSL certificates
3. **Enable XSRF protection** - Already configured in `.streamlit/config.toml`
4. **Restrict database access** - Use Render's internal networking

---

## Additional Resources

- **Render Docs:** [https://render.com/docs](https://render.com/docs)
- **Streamlit Deployment:** [https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)
- **PostgreSQL on Render:** [https://render.com/docs/databases](https://render.com/docs/databases)

---

## Support

If you encounter issues:

1. Check Render logs (Dashboard → Service → Logs)
2. Review [Render Community Forum](https://community.render.com)
3. Check Streamlit documentation for app-specific issues

---

## Success Checklist

- [ ] Code pushed to GitHub
- [ ] Render account created and connected to GitHub
- [ ] Database created (PostgreSQL)
- [ ] Web service created and deployed
- [ ] Environment variables configured (`DATABASE_URL`, `ANTHROPIC_API_KEY`)
- [ ] Database initialized (tables created)
- [ ] App accessible at Render URL
- [ ] Login page loads successfully
- [ ] Dashboard features working (test with sample data)

---

**You're all set! Your Transaction Monitoring Dashboard is now live on Render!** 🎉
