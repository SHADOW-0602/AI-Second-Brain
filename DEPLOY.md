# Render Deployment Guide

## Quick Deploy

1. **Fork this repository** to your GitHub account

2. **Connect to Render**:
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Select this repository

3. **Configure Environment Variables**:
   Set these required environment variables in Render:
   ```
   QDRANT_URL=https://your-cluster.qdrant.io
   QDRANT_API_KEY=your_qdrant_api_key
   GROQ_API_KEY=your_groq_api_key
   GEMINI_API_KEY=your_gemini_api_key
   MISTRAL_API_KEY=your_mistral_api_key
   COHERE_API_KEY=your_cohere_api_key
   LANGCHAIN_API_KEY=your_langsmith_api_key (optional)
   ```

4. **Deploy**: Render will automatically build and deploy your application

## Manual Deployment (Alternative)

If you prefer manual setup:

1. **Create Web Service**:
   - Go to Render Dashboard
   - Click "New" → "Web Service"
   - Connect your repository

2. **Configure Build & Start**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `cd backend && python main.py`
   - Environment: `Python 3`

3. **Set Environment Variables** (same as above)

## Post-Deployment

- Your app will be available at: `https://your-app-name.onrender.com`
- Health check endpoint: `https://your-app-name.onrender.com/health`
- API docs: `https://your-app-name.onrender.com/docs`

## Prerequisites

Before deploying, ensure you have:
- Qdrant Cloud account with a cluster
- API keys for: Groq, Gemini, Mistral, Cohere
- (Optional) LangSmith account for tracing

## Performance Notes

- The app uses Render's free tier by default (starter plan)
- For production, consider upgrading to a paid plan for better performance
- The app includes optimizations for cloud deployment (disabled access logs, etc.)

## Troubleshooting

- Check Render logs if deployment fails
- Ensure all required environment variables are set
- Verify API keys are valid and have sufficient credits