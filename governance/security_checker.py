def detect_security_issues(
    activity
):

    issues = []

    activity_json = str(activity)

    if "password" in activity_json.lower():

        issues.append(
            "Possible hardcoded password"
        )

    if "accountkey" in activity_json.lower():

        issues.append(
            "Possible storage account key"
        )

    if "sasToken".lower() in activity_json.lower():

        issues.append(
            "Possible SAS token exposure"
        )

    return issues