"""
This script creates a new Evidently AI project in the workspace.
"""

from src.config_manager import load_config
import json
import logging
from evidently.ui.dashboards import (
    DashboardPanelPlot,
    DashboardPanelCounter,
    PanelValue,
    PlotType,
    ReportFilter,
    CounterAgg,
    TestFilter,
    DashboardPanelTestSuite,
    TestSuitePanelType,
)
from evidently.renderers.html_widgets import WidgetSize
from evidently import metrics
from evidently.suite.base_suite import Snapshot
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_json(file_path: str) -> dict:
    """
    Load a JSON file.
    """
    with open(file_path, "r") as file:
        return json.load(file)


def create_summary_panels(config: dict, project) -> None:
    """
    Create the summary panels for the dashboard.
    """
    # dashboard title panel
    title = config["info"]["project_name"]
    description = config["info"]["project_description"]

    # empty the dashboard
    project.dashboard.panels = []

    project.dashboard.add_panel(
        DashboardPanelCounter(
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            agg=CounterAgg.NONE,
            title=description,
            text=title,
            size=WidgetSize.HALF,
        )
    )

    # dashboard summary panel
    model_developer = config["info"]["model_developer"]
    contact_name = config["info"]["contact_name"]
    contact_email = config["info"]["contact_email"]

    project.dashboard.add_panel(
        DashboardPanelCounter(
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            agg=CounterAgg.NONE,
            text="Model Information",
            title=f"Model Developer: {model_developer}\nContact Name: {contact_name}\nContact Email: {contact_email}",
            size=WidgetSize.HALF,
        )
    )


def create_metric_panels(config: dict, tags: list, project) -> None:
    """
    Create the metric panels for the dashboard.
    """
    try:
        panel_mapping = load_json("src/utils/panels_map.json")
    except Exception as e:
        logger.error(f"Error loading tests mapping: {e}")
        return

    panel_info = []

    for panel in config["dashboard_panels"]:

        # get the panel name from the config
        panel_name = panel["name"]

        # use the name to get the panel info from the mapping
        try:
            panel_key = panel_mapping[panel_name]
        except KeyError as e:
            logger.warning(f"Invalid panel name: {panel_name}... skipping")
            continue

        # get the panel type from the config, default to line
        plot = panel.get("type", "line")
        panel_size = panel.get("size", "half")

        # get the plot type and size, default to line and half
        plot_type = getattr(PlotType, plot.upper(), PlotType.LINE)
        size = getattr(WidgetSize, panel_size.upper(), WidgetSize.HALF)

        panel_title = panel_key["title"]
        metric_id = panel_key["metric_id"]
        field_path = panel_key["field_path"]
        category = panel_key["category"]

        panel_info.append(
            {
                "panel_title": panel_title,
                "metric_id": metric_id,
                "field_path": field_path,
                "plot_type": plot_type,
                "size": size,
                "category": category,
                "tags": tags + [category],
            }
        )

    # sort the panel info by category
    sorted_panel_info = sorted(panel_info, key=lambda x: x["category"])

    current_category = None

    for panel in sorted_panel_info:
        if panel["category"] != current_category:
            current_category = panel["category"]
            project.dashboard.add_panel(
                DashboardPanelCounter(
                    filter=ReportFilter(metadata_values={}, tag_values=[]),
                    agg=CounterAgg.NONE,
                    title=current_category.replace("_", " ").title() + " Metrics",
                    size=WidgetSize.FULL,
                )
            )

        if "current" in panel["field_path"]:
            reference_field_path = panel["field_path"].replace("current", "reference")

            # create the panel with both current and reference values
            project.dashboard.add_panel(
                DashboardPanelPlot(
                    title=panel["panel_title"],
                    filter=ReportFilter(metadata_values={}, tag_values=panel["tags"]),
                    values=[
                        PanelValue(
                            metric_id=panel["metric_id"],
                            field_path=eval(panel["field_path"]),
                            legend="Current",
                        ),
                        PanelValue(
                            metric_id=panel["metric_id"],
                            field_path=eval(reference_field_path),
                            legend="Reference",
                        ),
                    ],
                    plot_type=panel["plot_type"],
                    size=panel["size"],
                )
            )
        else:
            # create the panel with only the current value
            project.dashboard.add_panel(
                DashboardPanelPlot(
                    title=panel["panel_title"],
                    filter=ReportFilter(metadata_values={}, tag_values=panel["tags"]),
                    values=[
                        PanelValue(
                            metric_id=panel["metric_id"],
                            field_path=eval(panel["field_path"]),
                            legend="Current",
                        )
                    ],
                    plot_type=panel["plot_type"],
                    size=panel["size"],
                )
            )


def test_to_function(tests: list, mapping: dict):
    """
    Convert the test keys to functions.
    """
    test_functions = []
    for test in tests:
        try:
            if "params" in test:
                test_functions.append(
                    {"test_id": mapping[test["name"]], "test_args": test["params"]}
                )
            else:
                test_functions.append(
                    {"test_id": mapping[test["name"]], "test_args": {}}
                )
        except KeyError as e:
            logger.warning(f"Invalid test name: {test['name']}... skipping, {e}")
            continue
    return test_functions


def get_tests(config: dict):
    """
    Get the test functions from the configuration file and the mapping.
    """
    test_mapping = load_json("src/utils/tests_map.json")
    data_quality_tests = config["tests"]["data_quality_tests"]
    data_drift_tests = config["tests"]["data_drift_tests"]

    regression_tests = []
    classification_tests = []

    if config["model_config"]["model_type"]["regression"]:
        regression_tests = config["tests"]["regression_tests"]

    if config["model_config"]["model_type"]["binary_classification"]:
        classification_tests = config["tests"]["classification_tests"]

    data_quality_functions = test_to_function(
        data_quality_tests, test_mapping["data_quality"]
    )
    data_drift_functions = test_to_function(
        data_drift_tests, test_mapping["data_drift"]
    )
    regression_functions = test_to_function(
        regression_tests, test_mapping["regression"]
    )
    classification_functions = test_to_function(
        classification_tests, test_mapping["classification"]
    )

    return {
        "data_quality": data_quality_functions,
        "data_drift": data_drift_functions,
        "regression": regression_functions,
        "classification": classification_functions,
    }


def create_test_panels(config: dict, tags: list, project) -> None:
    """
    Create the test panels for the dashboard.
    """
    # get the test functions
    test_functions = get_tests(config)

    # data quality tests panel
    data_quality_tests = test_functions["data_quality"]

    project.dashboard.add_panel(
        DashboardPanelTestSuite(
            title="Data Quality Tests",
            test_filters=[
                TestFilter(
                    test_id=test["test_id"],
                    test_args=test["test_args"],
                )
                for test in data_quality_tests
            ],
            filter=ReportFilter(
                metadata_values={},
                tag_values=tags + ["data"],
                include_test_suites=True,
            ),
            size=WidgetSize.FULL,
            panel_type=TestSuitePanelType.DETAILED,
        )
    )

    # data drift tests panel
    data_drift_tests = test_functions["data_drift"]

    project.dashboard.add_panel(
        DashboardPanelTestSuite(
            title="Data Drift Tests",
            test_filters=[
                TestFilter(
                    test_id=test["test_id"],
                    test_args=test["test_args"],
                )
                for test in data_drift_tests
            ],
            filter=ReportFilter(
                metadata_values={},
                tag_values=tags + ["data"],
                include_test_suites=True,
            ),
            size=WidgetSize.FULL,
            panel_type=TestSuitePanelType.DETAILED,
        )
    )

    if test_functions["regression"]:
        # regression tests panel
        regression_tests = test_functions["regression"]

        project.dashboard.add_panel(
            DashboardPanelTestSuite(
                title="Regression Tests",
                test_filters=[
                    TestFilter(
                        test_id=test["test_id"],
                        test_args=test["test_args"],
                    )
                    for test in regression_tests
                ],
                filter=ReportFilter(
                    metadata_values={},
                    tag_values=tags + ["regression"],
                    include_test_suites=True,
                ),
                size=WidgetSize.FULL,
                panel_type=TestSuitePanelType.DETAILED,
            )
        )

    if test_functions["classification"]:
        # classification tests panel
        classification_tests = test_functions["classification"]

        project.dashboard.add_panel(
            DashboardPanelTestSuite(
                title="Classification Tests",
                test_filters=[
                    TestFilter(
                        test_id=test["test_id"],
                        test_args=test["test_args"],
                    )
                    for test in classification_tests
                ],
                filter=ReportFilter(
                    metadata_values={},
                    tag_values=tags + ["classification"],
                    include_test_suites=True,
                ),
                size=WidgetSize.FULL,
                panel_type=TestSuitePanelType.DETAILED,
            )
        )


def log_snapshots(project, workspace):
    """
    Log the JSON snapshots to the workspace.

    Currently, the snapshots are stored in the snapshots directory.
    In the future, they will be stored in AWS S3, and this function will be updated to load them from there.
    """
    snapshots_dir = os.path.abspath(os.path.join(__file__, "..", "../snapshots"))
    for timestamp in os.listdir(snapshots_dir):
        if timestamp.startswith("."):
            continue
        timestamp_path = os.path.join(snapshots_dir, timestamp)
        for operation in os.listdir(timestamp_path):
            if operation.startswith("."):
                continue
            operation_path = os.path.join(timestamp_path, operation)
            for strata in os.listdir(operation_path):
                if strata.startswith("."):
                    continue
                strata_path = os.path.join(operation_path, strata)
                for output_file in os.listdir(strata_path):
                    if output_file.startswith("."):
                        continue
                    output_path = os.path.join(strata_path, output_file)
                    workspace.add_snapshot(project.id, Snapshot.load(output_path))


def create_project(workspace, config: dict) -> None:
    try:
        project = workspace.create_project(config["info"]["project_name"])
        project.description = config["info"]["project_description"]
        project.save()
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        return

    # log the snapshots
    log_snapshots(project, workspace)

    default_tags = ["main", "single"]

    # create the summary panels
    create_summary_panels(config, project)

    # create the metric panels
    create_metric_panels(config, default_tags, project)

    # create the test panels
    create_test_panels(config, default_tags, project)

    project.save()


if __name__ == "__main__":
    config = load_config()
    create_project(config)