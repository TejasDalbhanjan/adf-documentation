def build_dataset_lineage(activities):
    lineage = []
    
    # Only generate lineage arrows for activities that actually move/transform data
    # This automatically filters out ForEach and IfCondition containers
    data_movement_types = [
        "Copy", 
        "ExecuteDataFlow", 
        "DatabricksNotebook", 
        "SqlServerStoredProcedure",
        "SynapseNotebook",
        "HDInsightHive",
        "HDInsightSpark"
    ]

    for activity in activities:
        if activity["type"] not in data_movement_types:
            continue

        datasets = activity.get("datasets", [])

        if len(datasets) >= 2:
            # Default assumption
            source = datasets[0]
            target = datasets[-1]

            # Smart Heuristic: Identify source vs target based on standard ADF naming
            for ds in datasets:
                ds_lower = ds.lower()
                if any(x in ds_lower for x in ["source", "src", "in"]):
                    source = ds
                elif any(x in ds_lower for x in ["target", "tgt", "sink", "out", "raw", "adls", "dest"]):
                    target = ds

            # Prevent rendering a loop if it resolves to the same dataset
            if source != target:
                lineage.append({
                    "source": source,
                    "target": target,
                    "activity": activity["name"]
                })

    return lineage