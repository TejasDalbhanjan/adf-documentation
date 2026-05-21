import re
from governance.retry_checker import extract_retry_policy
from governance.security_checker import detect_security_issues
from parser.expression_parser import extract_dynamic_expressions

# -----------------------------------
# ARM Expression Resolver
# -----------------------------------
def resolve_arm_expression(expr, full_data):
    """
    Evaluates ARM template variables and parameters to extract the true 
    underlying ADF resource name (e.g., dataset or linked service).
    """
    if not isinstance(expr, str) or not expr.startswith("["):
        return expr

    resolved = expr

    if full_data:
        # 1. Resolve variables: variables('varName')
        var_matches = re.finditer(r"variables\('([^']+)'\)", resolved)
        for match in var_matches:
            var_name = match.group(1)
            var_val = full_data.get("variables", {}).get(var_name, var_name)
            resolved = resolved.replace(match.group(0), str(var_val))

        # 2. Resolve parameters: parameters('paramName')
        param_matches = re.finditer(r"parameters\('([^']+)'\)", resolved)
        for match in param_matches:
            param_name = match.group(1)
            param_val = full_data.get("parameters", {}).get(param_name, {}).get("defaultValue", param_name)
            resolved = resolved.replace(match.group(0), str(param_val))

    # 3. Handle concat(...) flattening
    if "concat(" in resolved:
        inner = resolved.replace("[concat(", "").replace(")]", "").replace("'", "").replace(" ", "")
        resolved = "".join(inner.split(","))

    # 4. Clean up any remaining ARM brackets/quotes
    resolved = resolved.replace("[", "").replace("]", "").replace("'", "")

    # 5. Extract actual resource name (ADF ARM names are 'factoryName/resourceName')
    return resolved.split("/")[-1]


# -----------------------------------
# Build Dataset -> Linked Service Map
# -----------------------------------
def build_dataset_linked_service_map(data):
    dataset_map = {}
    resources = data.get("resources", [])

    for resource in resources:
        resource_type = resource.get("type", "").lower()

        if "datasets" in resource_type:
            # Resolve ARM dataset name
            raw_name = resource.get("name", "")
            dataset_name = resolve_arm_expression(raw_name, data)

            properties = resource.get("properties", {})
            linked_service = properties.get("linkedServiceName", {})

            # Resolve ARM Linked Service name
            if isinstance(linked_service, dict):
                raw_ls = linked_service.get("referenceName", "NA")
                ls_name = resolve_arm_expression(raw_ls, data)
            else:
                ls_name = resolve_arm_expression(linked_service, data)

            dataset_map[dataset_name] = ls_name

    return dataset_map

# -----------------------------------
# Pipeline Name, Parameters, Variables
# -----------------------------------
def extract_pipeline_name(pipeline_data, full_data=None):
    raw_name = pipeline_data.get("name", "Unknown Pipeline")
    source_data = full_data if full_data else pipeline_data
    resolved_name = resolve_arm_expression(raw_name, source_data)
    return resolved_name

def extract_pipeline_parameters(data):
    return data.get("properties", {}).get("parameters", {})

def extract_pipeline_variables(data):
    return data.get("properties", {}).get("variables", {})

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
    recursive_reference_scan(obj, classified)

    # Remove Duplicates
    for key in classified:
        classified[key] = list(set(classified[key]))
    return classified

def recursive_reference_scan(obj, classified):
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

# -----------------------------------
# Activity Parameters (SMART CAPTURE)
# -----------------------------------
def extract_activity_parameters(activity):
    """
    Dynamically captures all activity properties (like queries, URLs, batch counts)
    while ignoring nested activities to prevent massive messy JSON blocks.
    """
    parameters = {}
    type_properties = activity.get("typeProperties", {})
    
    # Exclude nested activity arrays so they don't bloat the parameters column
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

# -----------------------------------
# Activities Extraction
# -----------------------------------
def extract_activities(pipeline_data, full_data=None):
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
    activities = propagate_child_references(activities)
    return activities

# -----------------------------------
# Nested Activity Parsing
# -----------------------------------
def parse_nested_activities(activity_list, activities, dataset_ls_map, parent=None, full_data=None):
    for activity in activity_list:
        activity_name = activity.get("name", "Unknown")
        activity_type = activity.get("type", "Unknown")

        # dependsOn
        depends_on = []
        for dep in activity.get("dependsOn", []):
            depends_on.append({
                "activity": dep.get("activity"),
                "conditions": dep.get("dependencyConditions", [])
            })

        # Reference Classification
        references = classify_references(activity)

        # Resolve all extracted references through ARM evaluator
        for key in references:
            references[key] = list(set([
                resolve_arm_expression(ref, full_data) for ref in references[key]
            ]))

        # Dataset -> Linked Service Mapping
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

        parameters = extract_activity_parameters(activity)

        # Append Activity
        activities.append({
            "name": activity_name,
            "type": activity_type,
            "parent": parent,
            "depends_on": depends_on,
            "datasets": references["datasets"],
            "linked_services": references["linked_services"],
            "dataflows": references["dataflows"],
            "pipelines": references["pipelines"],
            "parameters": parameters,
            "retry_policy": extract_retry_policy(activity),
            "expressions": extract_dynamic_expressions(activity),
            "security_issues": detect_security_issues(activity),
            "notebook_path": activity.get("typeProperties", {}).get("notebookPath", "NA"),
            "stored_procedure": activity.get("typeProperties", {}).get("storedProcedureName", "NA")
        })

        # Recursive Traversal
        type_props = activity.get("typeProperties", {})
        
        for key in ["activities", "ifTrueActivities", "ifFalseActivities", "defaultActivities"]:
            nested = type_props.get(key, [])
            if nested:
                parse_nested_activities(nested, activities, dataset_ls_map, parent=activity_name, full_data=full_data)

        # Switch Cases
        for case in type_props.get("cases", []):
            parse_nested_activities(case.get("activities", []), activities, dataset_ls_map, parent=activity_name, full_data=full_data)

# -----------------------------------
# Propagate References
# -----------------------------------
def propagate_child_references(activities):
    activity_lookup = {activity["name"]: activity for activity in activities}

    for activity in reversed(activities):
        parent_name = activity.get("parent")
        if not parent_name:
            continue

        parent = activity_lookup.get(parent_name)
        if not parent:
            continue

        for key in ["datasets", "linked_services", "pipelines", "dataflows", "expressions"]:
            parent[key] = list(set(parent[key] + activity[key]))

    return activities