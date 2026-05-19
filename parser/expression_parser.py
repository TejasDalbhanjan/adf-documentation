def extract_dynamic_expressions(
    obj
):

    expressions = []

    recursive_expression_scan(

        obj,

        expressions
    )

    return list(
        set(expressions)
    )


def recursive_expression_scan(

    obj,

    expressions
):

    if isinstance(obj, dict):

        for value in obj.values():

            recursive_expression_scan(

                value,

                expressions
            )

    elif isinstance(obj, list):

        for item in obj:

            recursive_expression_scan(

                item,

                expressions
            )

    elif isinstance(obj, str):

        cleaned = obj.strip()

        if cleaned.startswith("@"):

            expressions.append(
                cleaned
            )