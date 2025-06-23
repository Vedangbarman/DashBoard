from flask import Flask, render_template, jsonify
import requests # <-- Import requests
import time
import random # Keep for other services or fallback

app = Flask(__name__)

# --- Configuration: Define your external dependencies ---
# Use actual API endpoints where possible, or status page URLs
EXTERNAL_SERVICES = {
    "GitHub Actions": {
        "type": "api",
        "url": "https://kctbh9vrtdwd.statuspage.io/api/v2/status.json", # GitHub's Status API
        "status_page_url": "https://www.githubstatus.com/" # Direct link for users
    },
    "AWS S3": {
        "type": "manual_check", # No simple direct API for overall AWS status
        "url": "https://status.aws.amazon.com/"
    },
    "Vercel": {
        "type": "manual_check", # Usually needs scraping or specific API access
        "url": "https://status.vercel.com/"
    },
    "Slack": {
        "type": "api",
        "url": "https://status.slack.com/api/v2.0.0/current", # Slack's Status API
        "status_page_url": "https://status.slack.com/"
    },
    "MongoDB Atlas": {
        "type": "manual_check", # Or specific Atlas API for your project
        "url": "https://status.cloud.mongodb.com/"
    },
}

# --- Function to get status from GitHub's StatusPage.io API ---
def get_github_status():
    try:
        response = requests.get(EXTERNAL_SERVICES["GitHub Actions"]["url"], timeout=5)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        indicator = data['status']['indicator'] # e.g., 'none', 'minor', 'major', 'critical'
        description = data['status']['description']

        if indicator == 'none':
            return {"color": "green", "message": "Operational"}
        elif indicator == 'minor':
            return {"color": "yellow", "message": f"Minor Issues: {description}"}
        elif indicator == 'major':
            return {"color": "orange", "message": f"Major Issues: {description}"}
        elif indicator == 'critical':
            return {"color": "red", "message": f"Critical Issues: {description}"}
        else:
            return {"color": "grey", "message": f"Unknown status: {description}"}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching GitHub status: {e}")
        return {"color": "grey", "message": "Could not fetch status (API Error)"}

# --- Function to get status from Slack's API ---
def get_slack_status():
    try:
        response = requests.get(EXTERNAL_SERVICES["Slack"]["url"], timeout=5)
        response.raise_for_status()
        data = response.json()
        health_status = data['status'] # e.g., 'ok', 'degraded', 'outage'
        
        if health_status == 'ok':
            return {"color": "green", "message": "Operational"}
        elif health_status == 'degraded':
            return {"color": "yellow", "message": "Degraded performance"}
        elif health_status == 'outage':
            return {"color": "red", "message": "Major Outage"}
        else:
            return {"color": "grey", "message": f"Unknown status: {health_status}"}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Slack status: {e}")
        return {"color": "grey", "message": "Could not fetch status (API Error)"}

@app.route('/')
def index():
    return render_template('index.html')

# --- Update the get_all_statuses route ---
@app.route('/api/status')
def get_all_statuses():
    statuses = {}
    for service_name, config in EXTERNAL_SERVICES.items():
        service_status = {"color": "grey", "message": "Status not implemented / Unknown", "url": config.get("status_page_url", config["url"])}

        if config["type"] == "api":
            if service_name == "GitHub Actions":
                service_status = get_github_status()
                service_status["url"] = config["status_page_url"] # Link to status page
            elif service_name == "Slack":
                service_status = get_slack_status()
                service_status["url"] = config["status_page_url"] # Link to status page
            # Add more API integrations here
        elif config["type"] == "manual_check":
            # For services without easy APIs, you'd either:
            # A) Implement web scraping (fragile, not shown here)
            # B) Use a default 'unknown' or 'manual check required' status
            # C) Use your random simulator as a placeholder
            simulated_status = {
                "operational": {"color": "green", "message": "Operational (Simulated)"},
                "degraded_performance": {"color": "yellow", "message": "Degraded (Simulated)"},
                "partial_outage": {"color": "orange", "message": "Partial Outage (Simulated)"},
                "major_outage": {"color": "red", "message": "Major Outage (Simulated)"},
            }
            if random.random() < 0.85:
                service_status = simulated_status["operational"]
            else:
                service_status = random.choice([
                    simulated_status["degraded_performance"],
                    simulated_status["partial_outage"],
                    simulated_status["major_outage"]
                ])
            service_status["url"] = config["url"]

        # Simulate uptime based on color
        if service_status["color"] == "green":
            service_status["uptime"] = "99.99%"
        elif service_status["color"] == "yellow":
            service_status["uptime"] = "98.5%"
        else:
            service_status["uptime"] = "95.0%"

        statuses[service_name] = service_status
    return jsonify(statuses)

# (Rest of your app.py remains the same)
if __name__ == '__main__':
    app.run(debug=True)