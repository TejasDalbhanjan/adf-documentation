def extract_retry_policy(
    activity
):

    policy = activity.get(
        "policy",
        {}
    )

    return {

        "retry": policy.get(
            "retry",
            0
        ),

        "timeout": policy.get(
            "timeout",
            "NA"
        ),

        "retry_interval": policy.get(
            "retryIntervalInSeconds",
            "NA"
        )
    }