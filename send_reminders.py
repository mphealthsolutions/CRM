#!/usr/bin/env python3
"""
MP Health Solutions — Daily Reminder Script
Runs via GitHub Actions every morning.
Fetches due reminders from Google Apps Script, then sends
a digest email via Gmail (using App Password) or SendGrid.
"""

import os
import json
import urllib.request
import urllib.parse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ── Config from GitHub Secrets ───────────────────────────────
APPS_SCRIPT_URL  = os.environ["APPS_SCRIPT_URL"]   # Deployed Apps Script URL
GMAIL_USER       = os.environ["GMAIL_USER"]         # your@mphealthsolutions.com
GMAIL_APP_PASS   = os.environ["GMAIL_APP_PASS"]     # 16-char Gmail App Password
REMINDER_TO      = os.environ.get("REMINDER_TO", GMAIL_USER)

CLAUDE_API_KEY   = os.environ.get("CLAUDE_API_KEY", "")  # Optional AI summaries


# ── Fetch reminders from Apps Script ─────────────────────────

def fetch_reminders():
    url = f"{APPS_SCRIPT_URL}?action=getDueReminders"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read())["reminders"]


# ── Optional: Claude API to draft a summary ──────────────────

def draft_ai_summary(reminders):
    if not CLAUDE_API_KEY or not reminders:
        return None

    reminder_text = "\n".join(
        f"- [{r['type'].upper()}] {r['message']} (date: {r['date']})"
        for r in reminders
    )

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 400,
        "messages": [{
            "role": "user",
            "content": (
                "You are an assistant for MP Health Solutions, a healthcare consulting firm. "
                "Write a concise, friendly morning briefing (3-5 sentences) summarizing these "
                "CRM reminders for Ajit Pai. Focus on the most time-sensitive items. "
                "Sign off as 'Your MPHS CRM'.\n\n"
                f"Reminders:\n{reminder_text}"
            )
        }]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01"
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        return data["content"][0]["text"]


# ── Build HTML email ─────────────────────────────────────────

TYPE_META = {
    "follow_up": {"icon": "📅", "label": "Follow-Up Due",      "color": "#013e86"},
    "check_in":  {"icon": "🔔", "label": "Check-In Overdue",   "color": "#ff8200"},
    "renewal":   {"icon": "📄", "label": "Contract Renewal",   "color": "#0F6E56"},
}

def build_email(reminders, ai_summary=None):
    today = datetime.today().strftime("%A, %B %-d, %Y")
    count = len(reminders)

    rows = ""
    for r in reminders:
        meta = TYPE_META.get(r["type"], {"icon": "•", "label": r["type"], "color": "#555"})
        c    = r["contact"]
        rows += f"""
        <tr>
          <td style="padding:14px 16px;border-bottom:1px solid #e6f4ee;">
            <div style="font-size:11px;font-weight:700;letter-spacing:.06em;
                        color:{meta['color']};text-transform:uppercase;margin-bottom:4px;">
              {meta['icon']} {meta['label']}
            </div>
            <div style="font-size:15px;font-weight:600;color:#111111;">{c.get('name','')}</div>
            <div style="font-size:13px;color:#666666;">{c.get('company','')} · {c.get('title','')}</div>
            <div style="font-size:12px;color:#999;margin-top:2px;">{r['message']}</div>
          </td>
          <td style="padding:14px 16px;border-bottom:1px solid #e6f4ee;
                     vertical-align:top;white-space:nowrap;">
            <a href="mailto:{c.get('email','')}"
               style="display:inline-block;padding:6px 14px;background:#0F6E56;
                      color:#fff;border-radius:6px;text-decoration:none;
                      font-size:12px;font-weight:600;">
              Email
            </a>
          </td>
        </tr>"""

    ai_block = ""
    if ai_summary:
        ai_block = f"""
        <div style="margin:24px 0;padding:18px 20px;background:#e6f4ee;
                    border-left:3px solid #0F6E56;border-radius:4px;">
          <div style="font-size:11px;font-weight:700;letter-spacing:.08em;
                      color:#0F6E56;text-transform:uppercase;margin-bottom:8px;">
            AI Morning Briefing
          </div>
          <div style="font-size:14px;color:#111111;line-height:1.6;">
            {ai_summary}
          </div>
        </div>"""

    no_reminders = "" if count else """
        <div style="padding:32px;text-align:center;color:#666666;font-size:14px;">
          ✅ No reminders due today. Great job staying on top of your contacts!
        </div>"""

    html = f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f8f8f6;font-family:'Inter','Helvetica Neue',Arial,sans-serif;">
  <div style="max-width:600px;margin:32px auto;background:#fff;
              border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08);">

    <!-- Header -->
    <div style="background:#0F6E56;padding:28px 32px;">
      <img src="https://www.mphealthsolutions.com/logo-mp-health.png"
           alt="M&amp;P Health Solutions" height="36"
           style="display:block;margin-bottom:16px;" />
      <div style="font-size:22px;font-weight:700;color:#fff;">
        CRM Daily Digest
      </div>
      <div style="font-size:13px;color:#e6f4ee;margin-top:4px;">{today}</div>
    </div>

    <!-- Summary bar -->
    <div style="background:#e6f4ee;padding:14px 32px;border-bottom:1px solid #d7e4f1;">
      <span style="font-size:13px;color:#0F6E56;font-weight:600;">
        {f'{count} reminder{"s" if count != 1 else ""} require your attention today.'
         if count else 'All clear — no reminders due today.'}
      </span>
    </div>

    <!-- Body -->
    <div style="padding:24px 32px;">
      {ai_block}
      {no_reminders}
      {"<table width='100%' cellpadding='0' cellspacing='0'>" + rows + "</table>" if count else ""}
    </div>

    <!-- Footer -->
    <div style="padding:20px 32px;border-top:1px solid #e6f4ee;
                font-size:11px;color:#666666;text-align:center;">
      Sent automatically by your MPHS CRM &nbsp;·&nbsp; GitHub Actions
    </div>
  </div>
</body></html>"""

    return html


# ── Send via Gmail SMTP ───────────────────────────────────────

def send_email(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = REMINDER_TO
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASS)
        server.sendmail(GMAIL_USER, REMINDER_TO, msg.as_string())
    print(f"✅ Reminder email sent to {REMINDER_TO}")


# ── Main ─────────────────────────────────────────────────────

def main():
    print("Fetching reminders...")
    reminders = fetch_reminders()
    print(f"Found {len(reminders)} reminder(s).")

    ai_summary = None
    if CLAUDE_API_KEY:
        print("Drafting AI summary...")
        try:
            ai_summary = draft_ai_summary(reminders)
        except Exception as e:
            print(f"AI summary skipped: {e}")

    today = datetime.today().strftime("%b %-d")
    subject = (
        f"MPHS CRM · {len(reminders)} Reminder{'s' if len(reminders) != 1 else ''} — {today}"
        if reminders else f"MPHS CRM · All Clear — {today}"
    )

    html = build_email(reminders, ai_summary)
    send_email(subject, html)


if __name__ == "__main__":
    main()
