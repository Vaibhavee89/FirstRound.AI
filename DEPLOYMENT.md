# Deployment Guide

This guide describes how to deploy the FirstRound.AI application for free using **Vercel** (for the frontend) and **Render** (for the backend agent).

## Prerequisites

- GitHub account (with this repository pushed).
- [Vercel](https://vercel.com/) account (Free).
- [Render](https://render.com/) account (Free).
- API Keys ready (OpenAI, Deepgram, Daily, Twilio).

---

## 1. Deploy Backend (Agent) to Render

Since the agent requires a continuous process and Python environment, we will deploy it as a Docker Web Service on Render.

1.  Log in to the [Render Dashboard](https://dashboard.render.com/).
2.  Click **New +** -> **Web Service**.
3.  Connect your GitHub repository.
4.  Configure the service:
    -   **Name**: `firstround-agent` (or similar).
    -   **Region**: Choose one close to you.
    -   **Branch**: `main`.
    -   **Root Directory**: `agent` (Important! Check this).
    -   **Runtime**: `Docker`.
    -   **Instance Type**: `Free`.
5.  **Environment Variables**:
    Add the following keys (copy from your local `.env`):
    -   `DAILY_API_KEY`
    -   `OPENAI_API_KEY`
    -   `DEEPGRAM_API_KEY`
    -   `CARTESIA_API_KEY` (Optional)
    -   `TWILIO_ACCOUNT_SID`
    -   `TWILIO_AUTH_TOKEN`
    -   `TWILIO_PHONE_NUMBER`
    -   `WEBHOOK_BASE_URL`: **Set this to your Render URL** once created (e.g., `https://firstround-agent.onrender.com`). You can set it to a placeholder first and update it after creation.
    -   `FRONTEND_URL`: **Set this to your Vercel URL** (see section 2). You can add this later.
6.  Click **Create Web Service**.

Render will build the Docker container and deploy it. Once done, copy the **Service URL** (e.g., `https://firstround-agent.onrender.com`).

---

## 2. Deploy Frontend to Vercel

1.  Log in to [Vercel](https://vercel.com/).
2.  Click **Add New...** -> **Project**.
3.  Import your GitHub repository.
4.  Configure the project:
    -   **Framework Preset**: Next.js (should detect automatically).
    -   **Root Directory**: Click "Edit" and select `frontend`.
5.  **Environment Variables**:
    -   `NEXT_PUBLIC_AGENT_URL`: Paste your **Render Backend URL** here (remove any trailing slash, e.g., `https://firstround-agent.onrender.com`).
6.  Click **Deploy**.

Vercel will build and deploy the frontend. Once done, copy the **Domain** (e.g., `https://firstround-ai.vercel.app`).

---

## 3. Final Configuration

### Update Backend Backend Variables
Go back to your **Render Dashboard** -> **Environment** and update:
-   `WEBHOOK_BASE_URL`: Ensure it matches your Render URL (no trailing slash).
-   `FRONTEND_URL`: Set it to your new Vercel URL (e.g., `https://firstround-ai.vercel.app`).
**Redeploy** the service on Render for changes to take effect.

### Update Twilio Webhook
1.  Go to your [Twilio Console](https://console.twilio.com/).
2.  Navigate to **Phone Numbers** -> **Manage** -> **Active Numbers**.
3.  Click on your phone number.
4.  Under **Voice & Fax** -> **A Call Comes In**:
    -   Select **Webhook**.
    -   URL: `https://<YOUR-RENDER-URL>.onrender.com/twilio/voice-webhook`
    -   Method: `POST`.
5.  Click **Save**.

### Note on Free Tier Constraints
-   **Render Free Tier**: The backend service will "spin down" after 15 minutes of inactivity. The first request (or phone call) after inactivity might take 50+ seconds to respond/connect. For a production demo, upgrade to the Starter plan ($7/mo).
-   **Data Persistence**: On the free tier, files created in the container (like logs and audio recordings) **will be lost** when the service restarts or spins down.

---

## Troubleshooting

-   **Files missing**: Ensure `jobs.json` and `applications.json` are in the `frontend` folder (we moved them there).
-   **CORS Errors**: If the frontend cannot talk to the backend, check the web console. Ensure `NEXT_PUBLIC_AGENT_URL` is set correctly in Vercel (and you rebuilt the app after changing it).
