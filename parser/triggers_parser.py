def extract_triggers(data):
    triggers = []
    properties = data.get(
        "properties",
        {}
    )
    annotations = properties.get(
        "annotations",
        []
    )
    triggers.append({

        "trigger_type": "PipelineAnnotations",

        "values": annotations
    })

    return triggers