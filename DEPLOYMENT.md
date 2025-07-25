# Deployment Guide

## Option 1: Streamlit Cloud (Recommended - Easiest)

**Streamlit Cloud** is the easiest way to deploy your Streamlit app. It's free and specifically designed for Streamlit applications.

### Steps:

1. **Push your code to GitHub** (already done ✅)
2. **Go to [share.streamlit.io](https://share.streamlit.io)**
3. **Sign in with your GitHub account**
4. **Click "New app"**
5. **Select your repository**: `rmaluski/black-scholes-option-pricing-model`
6. **Set the main file path**: `app.py`
7. **Click "Deploy"**

Your app will be live in minutes at a URL like: `https://your-app-name.streamlit.app`

## Option 2: Render.com (Fixed)

If you want to use Render, here's the correct setup:

### Steps:

1. **Go to [render.com](https://render.com)**
2. **Sign up/Login with GitHub**
3. **Click "New +" → "Web Service"**
4. **Connect your GitHub repository**
5. **Configure the service:**
   - **Name**: `black-scholes-app`
   - **Environment**: `Docker`
   - **Branch**: `master`
   - **Root Directory**: Leave empty
   - **Build Command**: Leave empty (uses Dockerfile)
   - **Start Command**: Leave empty (uses Dockerfile)
6. **Click "Create Web Service"**

## Option 3: Railway.app (Alternative)

Railway is another easy option:

### Steps:

1. **Go to [railway.app](https://railway.app)**
2. **Sign up with GitHub**
3. **Click "New Project" → "Deploy from GitHub repo"**
4. **Select your repository**
5. **Railway will automatically detect it's a Python app**
6. **Deploy**

## Troubleshooting Common Issues

### Issue: "Module not found" errors

**Solution**: Make sure `requirements.txt` includes all dependencies (already fixed ✅)

### Issue: Port configuration errors

**Solution**: The Dockerfile now uses the correct Streamlit port (8501)

### Issue: Database connection errors

**Solution**: The app uses SQLite locally, which works fine in containers

### Issue: Render exit code 128

**Solution**: Use the Docker deployment option, not Python

## Local Testing

Before deploying, test locally:

```bash
streamlit run app.py
```

## Environment Variables (if needed)

If you need to set environment variables later:

- **Streamlit Cloud**: Add in the app settings
- **Render**: Add in the Environment section
- **Railway**: Add in the Variables section

## Recommended: Streamlit Cloud

**Use Streamlit Cloud** - it's the easiest option and specifically designed for Streamlit apps. You'll have your app live in under 5 minutes!
