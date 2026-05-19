import re


def is_arm_template(data):

    return "resources" in data


def resolve_variable_value(

    variable_name,

    arm_json
):

    variables = arm_json.get(
        "variables",
        {}
    )

    return variables.get(

        variable_name,

        variable_name
    )


def clean_arm_name(

    name,

    arm_json
):

    if not isinstance(name, str):

        return "Unknown"

    variable_match = re.search(

        r"variables\('([^']+)'\)",

        name
    )

    if variable_match:

        variable_name = (
            variable_match.group(1)
        )

        return resolve_variable_value(

            variable_name,

            arm_json
        )

    parameter_match = re.search(

        r"parameters\('([^']+)'\)",

        name
    )

    if parameter_match:

        return parameter_match.group(1)

    return (

        name
        .replace("[", "")
        .replace("]", "")
        .replace("'", "")
        .replace("/", "_")
    )


def extract_pipelines_from_arm(
    arm_json
):

    pipelines = []

    resources = arm_json.get(
        "resources",
        []
    )

    for resource in resources:

        resource_type = resource.get(
            "type",
            ""
        )

        if (
            "pipelines"
            in resource_type.lower()
        ):

            raw_name = resource.get(
                "name",
                "UnknownPipeline"
            )

            pipeline_name = clean_arm_name(

                raw_name,

                arm_json
            )

            pipelines.append({

                "name":
                    pipeline_name,

                "properties":
                    resource.get(
                        "properties",
                        {}
                    )
            })

    return pipelines