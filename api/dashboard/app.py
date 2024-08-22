"""
Backend file for the monitoring dashboard. This file contains the API endpoints for the dashboard.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from src.dashboard.workspace_manager import WorkspaceManager
from scripts.data_details import load_details
from src.utils.config_manager import load_config
from src.dashboard.create_project import update_panels
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS

config = load_config()
details = load_details()
workspace_instance = WorkspaceManager.get_instance()
ws = workspace_instance.workspace

dashboard_url = os.environ.get("DASHBOARD_URL", "http://localhost:3000")
evidently_url = os.environ.get("EVIDENTLY_URL", "http://localhost:8000")


def get_filters(config: dict) -> dict:
    cols = config["columns"]
    strata_mapping = {
        "hospital": details["hospital_unique_values"],
    }
    if cols["instrument_type"]:
        strata_mapping["instrument_type"] = details["instrument_type_unique_values"]
    if cols["patient_class"]:
        strata_mapping["patient_class"] = details["patient_class_unique_values"]

    sex_values = details["sex_unique_values"]
    sex_list = []
    for sex in sex_values:
        if sex.lower() == "f":
            sex_list.append("female")
        elif sex.lower() == "m":
            sex_list.append("male")
        else:
            sex_list.append(sex)
    strata_mapping["sex"] = sex_list

    if config["age_filtering"]["filter_type"] == "custom":
        custom_ranges = config["age_filtering"]["custom_ranges"]
        range_list = [f"[{range_['min']}-{range_['max']}]" for range_ in custom_ranges]
        strata_mapping["age"] = range_list
    else:
        strata_mapping["age"] = [
            "[0-18]",
            "[18-65]",
            "[65+]",
        ]
    return strata_mapping


@app.route("/get_filter_options", methods=["GET"])
def get_filter_options():
    return jsonify(get_filters(config))


@app.route("/apply_filters", methods=["POST"])
def apply_filters():
    filters = request.json
    tags = [v for k, v in filters.items() if v]

    # if exactly one tag, add the tag 'single' to the list of tags
    if len(tags) == 1:
        tags.append("single")

    project = ws.search_project(config["info"]["project_name"])[0]

    logger.debug("tags: %s", tags)
    if tags:
        logger.info("Applying filters: %s", tags)
        update_panels(ws, config, tags)
    else:
        logger.info("No filters applied")
        update_panels(ws, config)

    dashboard_url = f"{dashboard_url}/dashboard"
    return jsonify({"status": "updated", "filtered_url": dashboard_url})


@app.route("/get_dashboard_url", methods=["GET"])
def get_dashboard_url():
    project = ws.search_project(config["info"]["project_name"])[0]
    dashboard_url = f"{evidently_url}/projects/{project.id}"
    return jsonify({"dashboard_url": dashboard_url})


if __name__ == "__main__":
    port = int(os.environ.get("DASHBOARD_API_PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True)
