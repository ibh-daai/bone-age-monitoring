AI Model Monitoring System Configuration Guide
==============================================

Introduction
------------

This documentation is written to help you understand and configure the AI Model Monitoring system developed by the AIDE Lab using the provided `config.json` file.

Sections
--------

The configuration file is structured into five sections: `model_config`, `columns`, `validation_rules`, `tests`, and `alerts`. Examples are shown in color.

### model_config

-   **model_id** (`string`): Unique identifier for the model.
-   **model_type** (`object`): Specifies the type of model.
    -   **regression** (`boolean`): Set to `true` to enable regression metrics.
    -   **binary_classification** (`boolean`): Set to `true` to enable binary classification metrics.
-   **provide_reference** (`boolean`): Set to `true` if providing a reference dataset for comparison. If `false`, the system will split the first uploaded dataset to use as a reference.

#### Notes:
The reference dataset should be in the exact same format as the data file outlined in the config. It should be in /data/reference_data.csv. If the reference dataset is not provided, the system will use the first uploaded dataset as the reference, only if it is a large enough dataset to be statistically significant when split.

#### Example
```json
"model_config": {
    "model_id": "bone_age_01",
    "model_type": {
        "regression": true,
        "binary_classification": true,
    "provide_reference": true
    }
},
```
### columns

Defines how to map your data columns to the required schema properties. If a required column is missing, replace the column name with `null`.

-   **study_id** (`string`): Unique identifiers for the study.
-   **patient_id** (`string`): Unique identifiers for the patients.
-   **model_id** (`string`): Unique identifier for the model.
-   **predictions** (`object`):
    -   **regression** (`string`): Column name for predicted regression values.
    -   **classification** (`string`): Column name for predicted classification values.
-   **labels** (`object`):
    -   **regression** (`string`): Column name for regression labels.
    -   **classification** (`string`): Column name for classification labels.
-   **features** (`array` of `string`): Column names for all the features. Optional, can include as many features as you like.
-   **timestamp** (`string`): Column name for timestamps.

#### Example
```json
"data_handling": {
    "columns": {
        "study_id": "StudyID",
        "patient_id": "PatientID",
        "model_id": "ModelID",
        "predictions": {
            "regression": "predicted_age",
            "classification": "classification"
        },
        "labels": {
            "regression": "label",
            "classification": "classification_label"
        },
        "features": [
            "sex",
            "chronological_age",
            "standard_deviation",
            "two_standard_deviations",
            "upper_limit",
            "lower_limit",
            "closest_age"
        ],
        "timestamp": null
    }
}
```
### validation_rules

Specifies the valid ranges or acceptable values for each feature to ensure data quality and accuracy during analysis. Validation rules can either be a numerical range (defined by an inclusive min and max value), or an enum (set of strings or booleans).

Enum example:
-   **feature_name** (`string`): The name of the feature.
    -   **type** (`string`): The type of validation rule. Set to `range` for numerical ranges, or `enum` for a set of acceptable values.
    -   **values** (`list`): The list of acceptable values for an enum

Range example:
-   **feature_name** (`string`): The name of the feature.
    -   **type** (`string`): The type of validation rule. Set to `range` for numerical ranges, or `enum` for a set of acceptable values.
    -   **min** (`number`): The minimum value for the range.
    -   **max** (`number`): The maximum value for the range.

### Example
```json
    "validation_rules": {
        "sex": {
            "type": "enum",
            "values": ["M", "F"]
        },
        "chronological_age": {
            "type": "range",
            "min": 0,
            "max": 400
        },
        "standard_deviation": {
            "type": "range",
            "min": 0,
            "max": 13.05
        },
        "two_standard_deviations": {
            "type": "range",
            "min": 0,
            "max": 26.1
        },
        "upper_limit": {
            "type": "range",
            "min": 0,
            "max": 300
        },
        "lower_limit": {
            "type": "range",
            "min": 0,
            "max": 300
        },
        "closest_age": {
            "type": "range",
            "min": 0,
            "max": 216
        }
    }
```
### tests

Enable or disable specific tests for regression and classification models.

-   **regression_tests** (`array` of `objects`):
    -   **name** (`string`): The name of the test (do not edit).
    -   **description** (`string`): A brief description of the test (optional edit).
    -   **enable** (`boolean`): Set to `true` to enable the test and `false` to disable.
-   **classification_tests** (`array` of `objects`):
    -   **name** (`string`): The name of the test (do not edit).
    -   **description** (`string`): A brief description of the test (optional edit).
    -   **enable** (`boolean`): Set to `true` to enable the test and `false` to disable.

#### Example
```json
"tests": {
    "regression_tests": [
        {
            "name": "mae",
            "description": "Compares with MAE of the reference data. Alerts with a difference of 10%.",
            "enable": true
        },
        {
            "name": "rmse",
            "description": "Compares with RMSE of the reference data. Alerts with a difference of 10%.",
            "enable": false
        },
        {
            "name": "mean_error",
            "description": "Compares with mean error of the reference data (or expected value of 0).",
            "enable": false
        },
        {
            "name": "mape",
            "description": "Compares with MAPE of the reference data. Alerts with a difference of 10%.",
            "enable": true
        },
        {
            "name": "absolute_max_error",
            "description": "Compares with Absolute Max Error of the reference data. Alerts with a difference of 10%.",
            "enable": false
        },
        {
            "name": "r2",
            "description": "Compares with R2 of the reference data. Alerts with a difference of 10%.",
            "enable": false
        }
    ],
    "classification_tests": [
        {
            "name": "accuracy",
            "description": "Compares with accuracy of the reference data. Alerts with a difference of 20%.",
            "enable": true
        },
        {
            "name": "precision",
            "description": "Compares with precision/PPV of the reference data. Alerts with a difference of 20%.",
            "enable": true
        },
        {
            "name": "recall",
            "description": "Compares with recall/sensitivity/TPR of the reference data. Alerts with a difference of 20%.",
            "enable": true
        },
        {
            "name": "f1",
            "description": "Compares with f1 score of the reference data. Alerts with a difference of 20%.",
            "enable": true
        },
        {
            "name": "specificity",
            "description": "Compares with specificity/tnr of the reference data. Alerts with a difference of 20%.",
            "enable": true
        },
        {
            "name": "fpr",
            "description": "Compares with fpr/type 1 error rate of the reference data. Alerts with a difference of 20%.",
            "enable": true
        },
        {
            "name": "fnr",
            "description": "Compares with fnr/type 2 error of the reference data. Alerts with a difference of 20%.",
            "enable": false
        },
        {
            "name": "roc_auc",
            "description": "Compares with ROC AUC of the reference data. Alerts with a difference of 20% or < 0.5.",
            "enable": false
        }
    ]
}
```

### alerts

Configure alert settings for the system.

-   **enable** (`boolean`): Set to `true` to enable alerts, `false` to disable.
-   **alert_links** (`array` of `object`):
    -   **type** (`string`): The type of alert method (supports only Microsoft Teams channel currently).
    -   **url** (`string`): URL for the Teams channel (or other alert type).

#### Example
```json
"alerts": {
    "enable": true,
    "alert_links": [
        {
            "type": "microsoft teams channel",
            "url": "<TODO>"
        }
    ]
}
````