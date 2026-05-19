from governance.retry_checker import (
    extract_retry_policy
)

from governance.security_checker import (
    detect_security_issues
)

from parser.expression_parser import (
    extract_dynamic_expressions
)

# -----------------------------------
# Build Dataset -> Linked Service Map
# -----------------------------------
def build_dataset_linked_service_map(data):

    dataset_map = {}

    resources = data.get("resources", [])

    for resource in resources:

        resource_type = resource.get("type", "").lower()

        # only datasets
        if "datasets" in resource_type:

            # full ARM name: factory/dataset
            full_name = resource.get("name", "")

            dataset_name = full_name.split("/")[-1]

            properties = resource.get("properties", {})

            linked_service = properties.get("linkedServiceName", {})

            if isinstance(linked_service, dict):
                linked_service = linked_service.get("referenceName", "NA")

            dataset_map[dataset_name] = linked_service

    return dataset_map

# -----------------------------------
# Pipeline Name
# -----------------------------------

def extract_pipeline_name(
    data
):

    return data.get(
        "name",
        "Unknown Pipeline"
    )


# -----------------------------------
# Pipeline Parameters
# -----------------------------------

def extract_pipeline_parameters(
    data
):

    return (
        data.get(
            "properties",
            {}
        ).get(
            "parameters",
            {}
        )
    )


# -----------------------------------
# Reference Extraction
# -----------------------------------

def classify_references(
    obj
):

    classified = {

        "datasets": [],
        "linked_services": [],
        "dataflows": [],
        "pipelines": []
    }

    recursive_reference_scan(

        obj,

        classified
    )

    # -----------------------------------
    # Remove Duplicates
    # -----------------------------------

    for key in classified:

        classified[key] = list(
            set(
                classified[key]
            )
        )

    return classified


def recursive_reference_scan(
    obj,
    classified
):

    # -----------------------------------
    # Dictionary
    # -----------------------------------

    if isinstance(obj, dict):

        reference_name = obj.get(
            "referenceName"
        )

        reference_type = obj.get(
            "type"
        )

        # -----------------------------------
        # Dataset
        # -----------------------------------

        if (
            reference_name
            and reference_type == "DatasetReference"
        ):

            classified[
                "datasets"
            ].append(
                reference_name
            )

        # -----------------------------------
        # Linked Service
        # -----------------------------------

        elif (
            reference_name
            and reference_type == "LinkedServiceReference"
        ):

            classified[
                "linked_services"
            ].append(
                reference_name
            )

        # -----------------------------------
        # Data Flow
        # -----------------------------------

        elif (
            reference_name
            and reference_type == "DataFlowReference"
        ):

            classified[
                "dataflows"
            ].append(
                reference_name
            )

        # -----------------------------------
        # Pipeline
        # -----------------------------------

        elif (
            reference_name
            and reference_type == "PipelineReference"
        ):

            classified[
                "pipelines"
            ].append(
                reference_name
            )

        # -----------------------------------
        # Recursive Scan
        # -----------------------------------

        for value in obj.values():

            recursive_reference_scan(

                value,

                classified
            )

    # -----------------------------------
    # List
    # -----------------------------------

    elif isinstance(obj, list):

        for item in obj:

            recursive_reference_scan(

                item,

                classified
            )


# -----------------------------------
# Activity Parameters
# -----------------------------------

def extract_activity_parameters(
    activity
):

    parameters = {}

    type_properties = activity.get(
        "typeProperties",
        {}
    )

    parameter_keys = [

        "parameters",

        "baseParameters",

        "storedProcedureParameters",

        "dataFlowParameters"
    ]

    for key in parameter_keys:

        value = type_properties.get(
            key
        )

        if value:

            parameters[key] = value

    return parameters


# -----------------------------------
# Activities Extraction
# -----------------------------------

def extract_activities(
    pipeline_data,
    full_data=None
):

    activities = []

    # -----------------------------------
    # ARM Template Support
    # -----------------------------------

    source_data = (
        full_data
        if full_data
        else pipeline_data
    )

    dataset_ls_map = (
        build_dataset_linked_service_map(
            source_data
        )
    )

    root_activities = (
        pipeline_data.get(
            "properties",
            {}
        ).get(
            "activities",
            []
        )
    )

    parse_nested_activities(

        root_activities,

        activities,

        dataset_ls_map,

        parent=None
    )
    activities = propagate_child_references(
        activities
    )
    return activities


# -----------------------------------
# Nested Activity Parsing
# -----------------------------------

def parse_nested_activities(

    activity_list,

    activities,

    dataset_ls_map,

    parent=None
):

    for activity in activity_list:

        activity_name = activity.get(
            "name",
            "Unknown"
        )

        activity_type = activity.get(
            "type",
            "Unknown"
        )
        direct_ls = activity.get("linkedServiceName", {}).get("referenceName")

        # -----------------------------------
        # dependsOn
        # -----------------------------------

        depends_on = []

        raw_dependencies = activity.get(
            "dependsOn",
            []
        )

        for dep in raw_dependencies:

            depends_on.append({

                "activity":
                    dep.get(
                        "activity"
                    ),

                "conditions":
                    dep.get(
                        "dependencyConditions",
                        []
                    )
            })

        # -----------------------------------
        # Reference Classification
        # -----------------------------------

        references = classify_references(
            activity
        )

        # -----------------------------------
        # Dataset -> Linked Service Mapping
        # -----------------------------------

        derived_linked_services = []

        # activity-level linked service (IMPORTANT FIX)
        direct_ls = activity.get(
            "linkedServiceName",
            {}
        ).get("referenceName")

        if direct_ls:
            derived_linked_services.append(direct_ls)

        # dataset -> linked service mapping
        for dataset in references["datasets"]:
            ls = dataset_ls_map.get(dataset)
            if ls and ls != "NA":
                derived_linked_services.append(ls)

        # merge both
        references["linked_services"].extend(derived_linked_services)

        # remove duplicates
        references["linked_services"] = list(set(references["linked_services"]))

        # references[
        #     "linked_services"
        # ] = list(
        #     set(
        #         references[
        #             "linked_services"
        #         ]
        #     )
        # )

        # -----------------------------------
        # Parameters
        # -----------------------------------

        parameters = (
            extract_activity_parameters(
                activity
            )
        )

        # -----------------------------------
        # Append Activity
        # -----------------------------------

        activities.append({

            "name":
                activity_name,

            "type":
                activity_type,

            "parent":
                parent,

            "depends_on":
                depends_on,

            "datasets":
                references[
                    "datasets"
                ],

            "linked_services":
                references[
                    "linked_services"
                ],

            "dataflows":
                references[
                    "dataflows"
                ],

            "pipelines":
                references[
                    "pipelines"
                ],

            "parameters":
                parameters,

            "retry_policy":
                extract_retry_policy(
                    activity
                ),

            "expressions":
                extract_dynamic_expressions(
                    activity
                ),

            "security_issues":
                detect_security_issues(
                    activity
                ),

            "notebook_path":
                activity.get(
                    "typeProperties",
                    {}
                ).get(
                    "notebookPath",
                    "NA"
                ),

            "stored_procedure":
                activity.get(
                    "typeProperties",
                    {}
                ).get(
                    "storedProcedureName",
                    "NA"
                )
        })

        # -----------------------------------
        # Generic Nested Activities
        # -----------------------------------

        nested_activities = (
            activity.get(
                "typeProperties",
                {}
            ).get(
                "activities",
                []
            )
        )

        if nested_activities:

            parse_nested_activities(

                nested_activities,

                activities,

                dataset_ls_map,

                parent=activity_name
            )

        # -----------------------------------
        # If True Activities
        # -----------------------------------

        if_true = (
            activity.get(
                "typeProperties",
                {}
            ).get(
                "ifTrueActivities",
                []
            )
        )

        if if_true:

            parse_nested_activities(

                if_true,

                activities,

                dataset_ls_map,

                parent=activity_name
            )

        # -----------------------------------
        # If False Activities
        # -----------------------------------

        if_false = (
            activity.get(
                "typeProperties",
                {}
            ).get(
                "ifFalseActivities",
                []
            )
        )

        if if_false:

            parse_nested_activities(

                if_false,

                activities,

                dataset_ls_map,

                parent=activity_name
            )

        # -----------------------------------
        # Switch Cases
        # -----------------------------------

        cases = (
            activity.get(
                "typeProperties",
                {}
            ).get(
                "cases",
                []
            )
        )

        for case in cases:

            parse_nested_activities(

                case.get(
                    "activities",
                    []
                ),

                activities,

                dataset_ls_map,

                parent=activity_name
            )

        # -----------------------------------
        # Default Activities
        # -----------------------------------

        default_activities = (
            activity.get(
                "typeProperties",
                {}
            ).get(
                "defaultActivities",
                []
            )
        )

        if default_activities:

            parse_nested_activities(

                default_activities,

                activities,

                dataset_ls_map,

                parent=activity_name
            )
            
def propagate_child_references(
    activities
):

    activity_lookup = {

        activity["name"]: activity

        for activity in activities
    }

    # reverse traversal

    for activity in reversed(activities):

        parent_name = activity.get(
            "parent"
        )

        if not parent_name:
            continue

        parent = activity_lookup.get(
            parent_name
        )

        if not parent:
            continue

        # merge datasets

        parent["datasets"] = list(
            set(
                parent["datasets"]
                + activity["datasets"]
            )
        )

        # merge linked services

        parent["linked_services"] = list(
            set(
                parent["linked_services"]
                + activity["linked_services"]
            )
        )

        # merge pipelines

        parent["pipelines"] = list(
            set(
                parent["pipelines"]
                + activity["pipelines"]
            )
        )

        # merge dataflows

        parent["dataflows"] = list(
            set(
                parent["dataflows"]
                + activity["dataflows"]
            )
        )

        # merge expressions

        parent["expressions"] = list(
            set(
                parent["expressions"]
                + activity["expressions"]
            )
        )

    return activities