def confirmation_status_color(
    registration_status: str,
    confirmation_status: str,
) -> str:
    if registration_status == "cancelled" or confirmation_status in {
        "declined",
        "expired",
        "delivery_failed",
    }:
        return "danger"

    if confirmation_status == "confirmed":
        return "success"

    return "waiting"
