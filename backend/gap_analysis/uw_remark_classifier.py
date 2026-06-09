def classify_uw_remark(
    uw_remark
):

    if not uw_remark:

        return "PARTIALLY_AGREED"

    remark = str(
        uw_remark
    ).lower().strip()

    not_agreed_keywords = [

        "not agreed",

        "not covered",

        "excluded",

        "declined",

        "rejected",

        "not acceptable",

        "not available"

    ]

    for keyword in not_agreed_keywords:

        if keyword in remark:

            return "NOT_AGREED"

    agreed_keywords = [

        "agreed",

        "covered",

        "accepted",

        "yes"

    ]

    for keyword in agreed_keywords:

        if keyword in remark:

            return "AGREED"

    return "PARTIALLY_AGREED"