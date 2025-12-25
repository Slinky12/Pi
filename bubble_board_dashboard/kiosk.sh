#!/usr/bin/env bash
# Launch Chromium in kiosk mode pointed at the Streamlit app.
# Run AFTER "streamlit run app.py ..." is running.

URL="${1:-http://localhost:8501}"

# Turn off screen blanking (optional)
xset s off || true
xset -dpms || true
xset s noblank || true

chromium-browser --kiosk --incognito --noerrdialogs --disable-infobars --check-for-update-interval=31536000 "$URL"
