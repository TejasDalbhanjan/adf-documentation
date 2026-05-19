import json


def safe_join(values):

    if not values:

        return "NA"

    return ",".join(values)


def safe_dict(value):

    if not value:

        return "{}"

    return json.dumps(value)