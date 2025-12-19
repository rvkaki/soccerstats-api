# Fly.io Deployment Guide

## Prerequisites

1. Install [Fly CLI](https://fly.io/docs/getting-started/installing-flyctl/)
2. Sign up for a [Fly.io account](https://fly.io/app/sign-up) (free tier available)

## Deployment Steps

1. **Login to Fly.io:**
   ```bash
   fly auth login
   ```

2. **Initialize your app (first time only):**
   ```bash
   fly launch
   ```
   - When prompted, choose a name for your app (or use the default)
   - Choose a region (e.g., `iad` for US East)
   - Don't deploy yet (answer "no" when asked)

3. **Deploy your app:**
   ```bash
   fly deploy
   ```

4. **Get your app URL:**
   ```bash
   fly status
   ```
   Your API will be available at: `https://your-app-name.fly.dev`

5. **Set up auto-scaling (optional but recommended):**
   The `fly.toml` is already configured with `auto_stop_machines` and `auto_start_machines` to save resources on the free tier.

## Environment Variables

No environment variables are required for the backend. The app reads JSON files from disk and fetches data from StatsBomb's public API.

## Important Notes

- The free tier includes 3 shared-cpu-1x VMs with 256MB RAM each
- Machines will auto-stop when idle and auto-start when receiving requests (configured in `fly.toml`)
- Your API URL will be: `https://your-app-name.fly.dev/api`
- Make sure to add this URL to your frontend's `NEXT_PUBLIC_API_URL` environment variable in Vercel

## Troubleshooting

- View logs: `fly logs`
- SSH into your machine: `fly ssh console`
- Check status: `fly status`

