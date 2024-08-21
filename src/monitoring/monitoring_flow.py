"""
Prefect flow for monitoring dashboard pipeline.
"""

from prefect import flow, task
from prefect.task_runners import SequentialTaskRunner
import logging
from datetime import datetime

import warnings
from sklearn.exceptions import UndefinedMetricWarning

from src.utils.config_manager import load_config
from scripts.data_details import load_details
from src.data_preprocessing.etl import etl_pipeline
from src.dashboard.generate_snapshots import generate_stratified_reports, generate_stratified_tests
from src.monitoring.stratify import DataSplitter
from src.dashboard.workspace_manager import WorkspaceManager
from src.dashboard.create_project import create_or_update

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@task
def load_configuration():
    return load_config()


@task
def load_data_details():
    return load_details()


@task
def run_etl(config):
    return etl_pipeline(config)


@task
def generate_snapshots(data, reference_data, config, timestamp, details):
    splitter = DataSplitter()
    generate_stratified_reports(
        data, reference_data, config, config["model_config"]["model_type"], timestamp, splitter, details
    )
    generate_stratified_tests(
        data, reference_data, config, config["model_config"]["model_type"], timestamp, splitter, details
    )


@task
def create_dashboard(config):
    workspace_instance = WorkspaceManager.get_instance()
    create_or_update(workspace_instance.workspace, config)


@flow(name="Monitoring Flow", task_runner=SequentialTaskRunner())  # dont make it sequential
def monitoring_flow():
    # timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    timestamp = "2024-07-01T00:00:00"
    config = load_configuration()
    details = load_data_details()
    data, reference_data = run_etl(config)

    if data is None:
        logger.info("No new data available. Monitoring flow completed successfully with no updates.")
        return

    generate_snapshots(data, reference_data, config, timestamp, details)
    create_dashboard(config)
    logger.info("Monitoring flow completed successfully.")


if __name__ == "__main__":
    warnings.simplefilter(action="ignore", category=FutureWarning)
    warnings.simplefilter(action="ignore", category=UndefinedMetricWarning)
    warnings.simplefilter(action="ignore", category=RuntimeWarning)
    warnings.simplefilter(action="ignore", category=UserWarning)

    monitoring_flow()