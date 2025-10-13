# PPDB Deployment Guide for Render.com

## Prerequisites
- Git repository with your code
- Render.com account (free tier available)
- Database file (database.db) and field mapping (field_mapping.csv) in the repository

## Files Required for Deployment

### 1. render.yaml
Configuration file for Render.com that defines the service settings.

### 2. requirements.txt
Python dependencies including:
- nicegui>=3.0.4
- pandas>=2.3.3
- openpyxl>=3.1.5

### 3. main.py
Your application entry point that runs on port 8080.

## Deployment Steps

### Step 1: Prepare Your Repository
1. Ensure all files are committed to your Git repository:
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

### Step 2: Create a Render Account
1. Go to https://render.com
2. Sign up for a free account
3. Connect your GitHub/GitLab/Bitbucket account

### Step 3: Deploy on Render

#### Option A: Using render.yaml (Recommended)
1. Go to Render Dashboard
2. Click "New" → "Blueprint"
3. Connect your repository
4. Render will automatically detect the `render.yaml` file
5. Click "Apply" to deploy

#### Option B: Manual Setup
1. Go to Render Dashboard
2. Click "New" → "Web Service"
3. Connect your repository
4. Configure the following settings:
   - **Name**: ppdb (or your preferred name)
   - **Region**: Singapore (or your preferred region)
   - **Branch**: main
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: Free
5. Click "Create Web Service"

### Step 4: Monitor Deployment
1. Watch the deployment logs in the Render dashboard
2. Wait for the build and deployment to complete (usually 2-5 minutes)
3. Your app will be available at: `https://your-app-name.onrender.com`

## Important Notes

### Database File
- The `database.db` file (8.9MB) will be included in your repository
- **Warning**: This database is read-only in the free tier
- Any changes to the database will be lost when the service restarts
- For persistent data, consider upgrading to a paid plan with persistent disk

### Free Tier Limitations
- Service will spin down after 15 minutes of inactivity
- First request after inactivity may take 30-60 seconds to wake up
- 750 hours of runtime per month (sufficient for most use cases)

### Configuration Details
- **Port**: The app runs on port 8080 (configured in main.py:761)
- **Host**: Set to '0.0.0.0' to accept connections from Render
- **Python Version**: 3.11.9

## Troubleshooting

### Build Fails
- Check that all dependencies are in requirements.txt
- Verify Python version compatibility

### App Won't Start
- Check logs in Render dashboard
- Verify database.db and field_mapping.csv are in the repository
- Ensure main.py has the correct host and port settings

### App is Slow
- Free tier services sleep after inactivity
- Consider upgrading to paid tier for always-on service

## Updating Your App
To update your deployed app:
```bash
git add .
git commit -m "Update description"
git push origin main
```
Render will automatically detect changes and redeploy.

## Environment Variables (Optional)
If needed, you can add environment variables in the Render dashboard:
1. Go to your service settings
2. Click "Environment"
3. Add key-value pairs

## Support
- Render Documentation: https://render.com/docs
- NiceGUI Documentation: https://nicegui.io/documentation
