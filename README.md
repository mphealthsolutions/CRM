# MPHS CRM

A free, lightweight CRM for MP Health Solutions built on:
- **GitHub Pages** — hosts the web app
- **Google Sheets** — stores all contact data
- **Google Apps Script** — REST API between the UI and Sheets
- **GitHub Actions** — sends daily reminder emails (weekday mornings)
- **Claude API** *(optional)* — AI-written morning briefing in the email

---

## Architecture

```
Browser (GitHub Pages)
    │  fetch (POST)
    ▼
Google Apps Script Web App   ←→   Google Sheet (Contacts tab)
                                         ▲
GitHub Actions (daily cron)  ──────────-┘
    │
    ▼
Gmail SMTP → your inbox
```

---

## Setup (one-time, ~20 minutes)

### Step 1 — Fork / push this repo to GitHub

1. Create a new repo at github.com
2. Push all files from this folder to that repo
3. In repo **Settings → Pages**, set source to `main` branch, root `/`
4. Your app will be live at `https://xxxxxx.github.io/crm`

---

### Step 2 — Create the Google Sheet

1. Go to [sheets.google.com](https://sheets.google.com) and create a new spreadsheet
2. Name it **xxxx CRM**
3. Leave it blank — the Apps Script will create the headers automatically

---

### Step 3 — Deploy the Google Apps Script

1. In your Google Sheet, go to **Extensions → Apps Script**
2. Delete any existing code in `Code.gs`
3. Copy and paste the entire contents of `apps-script/Code.gs`
4. Click **Save** (floppy disk icon)
5. Click **Deploy → New deployment**
   - Type: **Web app**
   - Execute as: **Me**
   - Who has access: **Anyone**
6. Click **Deploy** → authorize when prompted
7. **Copy the Web App URL** — you'll need it in Step 5

> ⚠️ Every time you edit the Apps Script, click **Deploy → Manage deployments → Edit** and create a new version.

---

### Step 4 — Gmail App Password (for reminder emails)

1. Go to your Google account → **Security → 2-Step Verification** (must be enabled)
2. Search for **App Passwords** at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Create a new App Password → Select app: **Mail**, device: **Other** → name it "xxxx CRM"
4. **Copy the 16-character password**

---

### Step 5 — Add GitHub Secrets

In your GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret Name      | Value |
|-----------------|-------|
| `APPS_SCRIPT_URL` | The Web App URL from Step 3 |
| `GMAIL_USER`      | your Google Workspace email |
| `GMAIL_APP_PASS`  | The 16-char App Password from Step 4 |
| `REMINDER_TO`     | Email to receive reminders (can be same as GMAIL_USER) |
| `CLAUDE_API_KEY`  | *(Optional)* Your Anthropic API key for AI email summaries |

---

### Step 6 — Connect the web app

1. Open your GitHub Pages URL
2. Click **Settings** in the sidebar
3. Paste the Apps Script URL and click **Save & Test Connection**
4. ✅ You're live!

---

## Daily Reminders

GitHub Actions runs **Monday–Friday at 8:00 AM Eastern**.

You'll receive a digest email covering:
- 📅 **Follow-ups** due today or overdue
- 🔔 **Check-ins** — Active contacts with no contact in 30+ days
- 📄 **Renewals** — Contracts expiring within 30 days

If `CLAUDE_API_KEY` is set, the email will also include an AI-written morning briefing.

To trigger manually: **Actions tab → Daily CRM Reminders → Run workflow**

---

## Cost

| Item | Cost |
|------|------|
| GitHub (Pages + Actions) | Free |
| Google Workspace (you already have it) | $0 additional |
| Claude API (optional, light use) | ~$1–3/month |
| **Total** | **$0–3/month** |

---

## File Structure

```
├── index.html                        # CRM web app (GitHub Pages)
├── apps-script/
│   └── Code.gs                       # Google Apps Script backend
├── scripts/
│   └── send_reminders.py             # Daily reminder email script
├── .github/
│   └── workflows/
│       └── daily-reminders.yml       # GitHub Actions cron job
└── README.md
```
