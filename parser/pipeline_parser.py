def extract_pipeline_name(data):

    return data.get(
        "name",
        "Unknown Pipeline"
    )


def extract_pipeline_parameters(data):

    return (
        data.get("properties", {})
        .get("parameters", {})
    )


# -----------------------------------
# Reference Extraction
# -----------------------------------

def classify_references(obj):

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

    # remove duplicates
    for key in classified:

        classified[key] = list(
            set(classified[key])
        )

    return classified


def recursive_reference_scan(
    obj,
    classified
):

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

            classified["datasets"].append(
                reference_name
            )

        # -----------------------------------
        # Linked Service
        # -----------------------------------

        elif (
            reference_name
            and reference_type == "LinkedServiceReference"
        ):

            classified["linked_services"].append(
                reference_name
            )

        # -----------------------------------
        # Data Flow
        # -----------------------------------

        elif (
            reference_name
            and reference_type == "DataFlowReference"
        ):

            classified["dataflows"].append(
                reference_name
            )

        # -----------------------------------
        # Pipeline
        # -----------------------------------

        elif (
            reference_name
            and reference_type == "PipelineReference"
        ):

            classified["pipelines"].append(
                reference_name
            )

        # recursive scan
        for value in obj.values():

            recursive_reference_scan(
                value,
                classified
            )

    elif isinstance(obj, list):

        for item in obj:

            recursive_reference_scan(
                item,
                classified
            )

def extract_activity_parameters(activity):

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

        value = type_properties.get(key)

        if value:

            parameters[key] = value

    return parameters

# -----------------------------------
# Activities Extraction
# -----------------------------------

def extract_activities(data):

    activities = []

    root_activities = (
        data.get("properties", {})
        .get("activities", [])
    )

    parse_nested_activities(
        root_activities,
        activities,
        parent=None
    )

    return activities


def parse_nested_activities(
    activity_list,
    activities,
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
                    dep.get("activity"),

                "conditions":
                    dep.get(
                        "dependencyConditions",
                        []
                    )
            })

        # -----------------------------------
        # references classification
        # -----------------------------------

        references = classify_references(
            activity
        )

        # -----------------------------------
        # parameters
        # -----------------------------------

        parameters = extract_activity_parameters(
            activity
        )

        # -----------------------------------
        # append activity
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
                references["datasets"],

            "linked_services":
                references["linked_services"],

            "dataflows":
                references["dataflows"],

            "pipelines":
                references["pipelines"],

            "parameters":
                parameters
        })

        # -----------------------------------
        # Generic nested activities
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
                parent=activity_name
            )

        # -----------------------------------
        # IfCondition
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
                parent=activity_name
            )

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
                parent=activity_name
            )

        # -----------------------------------
        # Switch Default
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
                parent=activity_name
            )