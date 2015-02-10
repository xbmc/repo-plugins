def widgets_to_answer(widgets):
    """
    Convert list of widget objects to Udacity answer data
    """
    parts = []
    for widget in widgets:
        parts.append(
            {"model": "SubmissionPart",
             "marker": widget['data']['marker'],
             "content": widget['obj'].getContent()})

    answer_data = {
        "submission": {
            "model": "Submission",
            "operation": "GRADE",
            "parts": parts
        }
    }

    return answer_data


