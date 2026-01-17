# Deploy Taskpedia Review App Online

## Option 1: Render.com (Recommended - FREE & Easy)

### Setup Steps:

1. **Prepare the app for deployment**:

```bash
# Create requirements.txt
cat > requirements.txt << EOF
Flask==3.0.0
gunicorn==21.2.0
EOF

# Create Procfile for Render
cat > Procfile << EOF
web: gunicorn browse_review_app:app
EOF
```

2. **Push to GitHub** (already done):
```bash
git add requirements.txt Procfile
git commit -m "Add deployment files"
git push origin sarthak-dev
```

3. **Deploy on Render**:
   - Go to https://render.com
   - Sign up with GitHub
   - Click "New +" → "Web Service"
   - Connect your GitHub repo: `sarthaktiwary12/Taskpedia`
   - Branch: `sarthak-dev`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn browse_review_app:app`
   - Choose FREE plan
   - Click "Create Web Service"

4. **Your app will be live at**: `https://taskpedia-XXXXX.onrender.com`

**Pros**:
- ✅ Free (no credit card)
- ✅ HTTPS included
- ✅ Auto-deploys on git push
- ✅ Simple setup

**Cons**:
- ⚠️ Sleeps after 15 min inactivity (wakes up in ~30 seconds)
- ⚠️ 750 hours/month free tier

---

## Option 2: Railway.app (Also Great - FREE)

### Setup Steps:

1. **Same requirements.txt as above**

2. **Deploy**:
   - Go to https://railway.app
   - Sign in with GitHub
   - "New Project" → "Deploy from GitHub repo"
   - Select: `sarthaktiwary12/Taskpedia`
   - Branch: `sarthak-dev`
   - Railway auto-detects Python/Flask
   - Click "Deploy"

3. **Configure**:
   - Go to Settings → Generate Domain
   - Your app: `https://taskpedia.up.railway.app`

**Pros**:
- ✅ Free $5 credit/month
- ✅ No sleep (stays awake)
- ✅ Fast deploys
- ✅ Easy setup

---

## Option 3: Fly.io (Advanced - More Control)

### Setup:

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Launch app
flyctl launch --name taskpedia-review

# Deploy
flyctl deploy
```

**Your app**: `https://taskpedia-review.fly.dev`

---

## Option 4: Vercel (Serverless)

Requires converting to serverless format. Not recommended for this Flask app.

---

## Quick Deploy Script (Render)

I'll create everything you need:

```bash
#!/bin/bash
# deploy.sh - Quick deploy to Render

# 1. Create requirements.txt
cat > requirements.txt << EOF
Flask==3.0.0
gunicorn==21.2.0
EOF

# 2. Create Procfile
cat > Procfile << EOF
web: gunicorn browse_review_app:app --bind 0.0.0.0:\$PORT
EOF

# 3. Commit and push
git add requirements.txt Procfile
git commit -m "Add deployment configuration for Render"
git push origin sarthak-dev

echo "✅ Files ready!"
echo ""
echo "Next steps:"
echo "1. Go to https://render.com"
echo "2. Sign in with GitHub"
echo "3. New Web Service → Connect repo: Taskpedia"
echo "4. Branch: sarthak-dev"
echo "5. Build: pip install -r requirements.txt"
echo "6. Start: gunicorn browse_review_app:app"
echo "7. Click Deploy!"
```

---

## Important: Data Persistence

⚠️ **Problem**: `value_ratings.jsonl` gets lost on each deploy (file storage is ephemeral)

### Solution Options:

### A. PostgreSQL Database (Recommended for production)
- Use Render's free PostgreSQL addon
- Store ratings in database instead of file

### B. GitHub Auto-Commit (Simple hack)
- App commits ratings back to GitHub every hour
- Ratings persist in the repo

### C. Cloud Storage
- Use AWS S3 or Google Cloud Storage
- Store ratings.jsonl in cloud bucket

### D. Accept Data Loss (OK for review/testing)
- Download ratings JSON before each restart
- Re-import if needed

---

## Share with Others

Once deployed, share the URL:
- `https://taskpedia-xxxxx.onrender.com` (Render)
- `https://taskpedia.up.railway.app` (Railway)

**For collaborators**:
1. Send them the URL
2. They review tasks
3. They click "Export" to download their ratings
4. Send you the JSON file
5. You import their ratings

---

## Environment Variables (if needed)

If you add authentication or API keys later:

**Render**: Settings → Environment → Add Variable
**Railway**: Variables tab → Add Variable

---

## Which to Choose?

| Feature | Render | Railway | Fly.io |
|---------|--------|---------|--------|
| Free Tier | ✅ Yes | ✅ Yes | ✅ Yes |
| Always On | ❌ Sleeps | ✅ Yes | ✅ Yes |
| Easy Setup | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Best For | Quick demos | Active use | Production |

**My Recommendation**: Start with **Render** (easiest) or **Railway** (no sleep).

---

## Next Steps

Want me to:
1. Create the deployment files (requirements.txt, Procfile)?
2. Set up PostgreSQL for persistent ratings?
3. Add authentication so only you can rate tasks?
