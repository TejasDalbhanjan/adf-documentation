import re
from governance.retry_checker import extract_retry_policy
from governance.security_checker import detect_security_issues
from parser.expression_parser import extract_dynamic_expressions


def resolve_arm_expression(expr, full_data):
    """
    Evaluates ARM template variables and parameters to extract the true 
    underlying ADF resource name (e.g., dataset or linked service).
    """
    if not isinstance(expr, str) or not expr.startswith("["):
        return expr

    resolved = expr

    if full_data:
        # Resolve variables: variables('varName')
        var_matches = re.finditer(r"variables\('([^']+)'\)", resolved)
        for match in var_matches:
            var_name = match.group(1)
            var_val = full_data.get("variables", {}).get(var_name, var_name)
            resolved = resolved.replace(match.group(0), str(var_val))

        # Resolve parameters: parameters('paramName')
        param_matches = re.finditer(r"parameters\('([^']+)'\)", resolved)
        for match in param_matches:
            param_name = match.group(1)
            param_val = full_data.get("parameters", {}).get(param_name, {}).get("defaultValue", param_name)
            resolved = resolved.replace(match.group(0), str(param_val))

    # Handle concat(...) flattening
    if "concat(" in resolved:
        inner = resolved.replace("[concat(", "").replace(")]", "").replace("'", "").replace(" ", "")
        resolved = "".join(inner.split(","))

    # Clean up any remaining ARM brackets/quotes
    resolved = resolved.replace("[", "").replace("]", "").replace("'", "")

    # Extract actual resource name (ADF ARM names are 'factoryName/resourceName')
    return resolved.split("/")[-1]


def build_dataset_linked_service_map(data):
    """
    Creates a lookup dictionary mapping dataset names to their underlying linked services,
    resolving any ARM expressions along the way.
    """
    dataset_map = {}
    resources = data.get("resources", [])

    for resource in resources:
        resource_type = resource.get("type", "").lower()

        if "datasets" in resource_type:
            raw_name = resource.get("name", "")
            dataset_name = resolve_arm_expression(raw_name, data)

            properties = resource.get("properties", {})
            linked_service = properties.get("linkedServiceName", {})

            if isinstance(linked_service, dict):
                raw_ls = linked_service.get("referenceName", "NA")
                ls_name = resolve_arm_expression(raw_ls, data)
            else:
                ls_name = resolve_arm_expression(linked_service, data)

            dataset_map[dataset_name] = ls_name

    return dataset_map


def extract_pipeline_name(pipeline_data, full_data=None):
    """Safely extracts and resolves the pipeline name."""
    raw_name = pipeline_data.get("name", "Unknown Pipeline")
    source_data = full_data if full_data else pipeline_data
    return resolve_arm_expression(raw_name, source_data)


def extract_pipeline_parameters(data):
    """Extracts top-level pipeline parameters."""
    return data.get("properties", {}).get("parameters", {})


def extract_pipeline_variables(data):
    """Extracts top-level pipeline variables."""
    return data.get("properties", {}).get("variables", {})


def classify_references(obj):
    """
    Recursively scans an activity payload to categorize all referenced 
    datasets, linked services, dataflows, and child pipelines.
    """
    classified = {
        "datasets": [],
        "linked_services": [],
        "dataflows": [],
        "pipelines": []
    }
    
    recursive_reference_scan(obj, classified)

    # Deduplicate lists before returning
    for key in classified:
        classified[key] = list(set(classified[key]))
        
    return classified


def recursive_reference_scan(obj, classified):
    """Helper function to deeply traverse nested dictionaries for ADF references."""
    if isinstance(obj, dict):
        reference_name = obj.get("referenceName")
        reference_type = obj.get("type")

        if reference_name and reference_type == "DatasetReference":
            classified["datasets"].append(reference_name)
        elif reference_name and reference_type == "LinkedServiceReference":
            classified["linked_services"].append(reference_name)
        elif reference_name and reference_type == "DataFlowReference":
            classified["dataflows"].append(reference_name)
        elif reference_name and reference_type == "PipelineReference":
            classified["pipelines"].append(reference_name)

        for value in obj.values():
            recursive_reference_scan(value, classified)

    elif isinstance(obj, list):
        for item in obj:
            recursive_reference_scan(item, classified)


def extract_activity_parameters(activity):
    """
    Dynamically captures all activity properties (like queries, URLs, batch counts)
    while explicitly ignoring nested activities to prevent massive JSON bloat.
    """
    parameters = {}
    type_properties = activity.get("typeProperties", {})
    
    exclude_keys = [
        "activities", 
        "ifTrueActivities", 
        "ifFalseActivities", 
        "defaultActivities", 
        "cases"
    ]

    for key, value in type_properties.items():
        if key not in exclude_keys:
            parameters[key] = value

    return parameters


def extract_activities(pipeline_data, full_data=None):
    """
    Primary entry point to parse a pipeline. Maps datasets to linked services,
    extracts all nested activities, and propagates dependencies up the chain.
    """
    activities = []
    source_data = full_data if full_data else pipeline_data
    
    dataset_ls_map = build_dataset_linked_service_map(source_data)
    root_activities = pipeline_data.get("properties", {}).get("activities", [])

    parse_nested_activities(
        root_activities,
        activities,
        dataset_ls_map,
        parent=None,
        full_data=source_data
    )
    
    return propagate_child_references(activities)


def parse_nested_activities(activity_list, activities, dataset_ls_map, parent=None, full_data=None):
    """
    Recursively drills into containers (ForEach, Switch, IfCondition) to extract
    every child activity and its dependencies, maintaining the parent-child hierarchy.
    """
    for activity in activity_list:
        activity_name = activity.get("name", "Unknown")
        activity_type = activity.get("type", "Unknown")

        depends_on = [
            {
                "activity": dep.get("activity"),
                "conditions": dep.get("dependencyConditions", [])
            }
            for dep in activity.get("dependsOn", [])
        ]

        references = classify_references(activity)

        # Resolve extracted references through the ARM evaluator
        for key in references:
            references[key] = list(set([
                resolve_arm_expression(ref, full_data) for ref in references[key]
            ]))

        # Map datasets directly to their linked services
        derived_linked_services = []
        direct_ls = activity.get("linkedServiceName", {}).get("referenceName")
        
        if direct_ls:
            derived_linked_services.append(resolve_arm_expression(direct_ls, full_data))

        for dataset in references["datasets"]:
            ls = dataset_ls_map.get(dataset)
            if ls and ls != "NA":
                derived_linked_services.append(ls)

        references["linked_services"].extend(derived_linked_services)
        references["linked_services"] = list(set(references["linked_services"]))

        # Append the flattened activity payload
        activities.append({
            "name": activity_name,
            "type": activity_type,
            "parent": parent,
            "depends_on": depends_on,
            "datasets": references["datasets"],
            "linked_services": references["linked_services"],
            "dataflows": references["dataflows"],
            "pipelines": references["pipelines"],
            "parameters": extract_activity_parameters(activity),
            "retry_policy": extract_retry_policy(activity),
            "expressions": extract_dynamic_expressions(activity),
            "security_issues": detect_security_issues(activity),
            "notebook_path": activity.get("typeProperties", {}).get("notebookPath", "NA"),
            "stored_procedure": activity.get("typeProperties", {}).get("storedProcedureName", "NA")
        })

        # Traverse nested child containers
        type_props = activity.get("typeProperties", {})
        
        for key in ["activities", "ifTrueActivities", "ifFalseActivities", "defaultActivities"]:
            nested = type_props.get(key, [])
            if nested:
                parse_nested_activities(nested, activities, dataset_ls_map, parent=activity_name, full_data=full_data)

        # Handle Switch Cases specifically
        for case in type_props.get("cases", []):
            parse_nested_activities(case.get("activities", []), activities, dataset_ls_map, parent=activity_name, full_data=full_data)


def propagate_child_references(activities):
    """
    Rolls up metadata. If a child activity inside a ForEach touches a dataset, 
    this ensures the parent ForEach is also marked as touching that dataset.
    """
    activity_lookup = {activity["name"]: activity for activity in activities}

    # Iterate in reverse to ensure deep children propagate up to top-level parents
    for activity in reversed(activities):
        parent_name = activity.get("parent")
        if not parent_name:
            continue

        parent = activity_lookup.get(parent_name)
        if not parent:
            continue

        # Merge child lists into the parent
        for key in ["datasets", "linked_services", "pipelines", "dataflows", "expressions"]:
            parent[key] = list(set(parent[key] + activity[key]))

    return activities