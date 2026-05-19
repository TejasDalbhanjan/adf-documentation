def extract_linked_service_details(activity):

    linked_services = []

    recursive_scan(
        activity,
        linked_services
    )

    return list(set(linked_services))



def recursive_scan(
    obj,
    linked_services
):

    if isinstance(obj, dict):

        reference_name = obj.get(
            "referenceName"
        )

        reference_type = obj.get(
            "type"
        )

        if (
            reference_name
            and reference_type == "LinkedServiceReference"
        ):

            linked_services.append(
                reference_name
            )

        for value in obj.values():

            recursive_scan(
                value,
                linked_services
            )

    elif isinstance(obj, list):

        for item in obj:

            recursive_scan(
                item,
                linked_services
            )