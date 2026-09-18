from datetime import datetime, timezone


CRITICAL_ISSUES = {
    "waterlogging",
    "pothole",
}

HIGH_ISSUES = {
    "garbage",
    "construction_waste",
    "overflowing_bin",
}


def calculate_priority(
    issue_type: str,
    severity: str | None = None,
    urgency: str | None = None,
    description: str | None = None,
    reported_at: datetime | None = None,
    is_duplicate: bool = False,
    routing_confidence: float | None = None,
) -> dict:
    """
    Explainable priority engine for CivicRoute.

    Returns:
        priority: LOW / NORMAL / HIGH / CRITICAL
        score: numeric priority score
        reasons: list explaining the decision
    """

    issue_type = (issue_type or "").lower().strip()
    severity = (severity or "medium").lower().strip()
    urgency = (urgency or "normal").lower().strip()
    description = (description or "").lower().strip()

    score = 0
    reasons = []

    # ---------------------------------------------------------
    # 1. ISSUE TYPE
    # ---------------------------------------------------------

    if issue_type in CRITICAL_ISSUES:
        score += 25
        reasons.append(
            f"{issue_type.replace('_', ' ').capitalize()} can create "
            "significant public safety or mobility impact."
        )

    elif issue_type in HIGH_ISSUES:
        score += 15
        reasons.append(
            f"{issue_type.replace('_', ' ').capitalize()} requires "
            "timely civic response."
        )

    else:
        score += 5

    # ---------------------------------------------------------
    # 2. SEVERITY
    # ---------------------------------------------------------

    severity_scores = {
        "critical": 40,
        "high": 25,
        "medium": 10,
        "low": 0,
    }

    severity_score = severity_scores.get(severity, 10)

    if severity_score:
        score += severity_score
        reasons.append(
            f"Reported severity is {severity}."
        )

    # ---------------------------------------------------------
    # 3. URGENCY
    # ---------------------------------------------------------

    urgency_scores = {
        "critical": 30,
        "high": 20,
        "normal": 5,
        "low": 0,
    }

    urgency_score = urgency_scores.get(urgency, 5)

    if urgency_score:
        score += urgency_score
        reasons.append(
            f"Reported urgency is {urgency}."
        )

    # ---------------------------------------------------------
    # 4. SAFETY KEYWORDS
    # ---------------------------------------------------------

    safety_keywords = [
        "accident",
        "dangerous",
        "danger",
        "unsafe",
        "emergency",
        "blocked completely",
        "life threatening",
        "injury",
        "risk",
        "hazard",
    ]

    matched_safety_keywords = [
        keyword
        for keyword in safety_keywords
        if keyword in description
    ]

    if matched_safety_keywords:
        score += 25
        reasons.append(
            "Safety-related indicators detected: "
            + ", ".join(matched_safety_keywords[:4])
            + "."
        )

    # ---------------------------------------------------------
    # 5. AGE OF COMPLAINT
    # ---------------------------------------------------------

    if reported_at:
        if reported_at.tzinfo is None:
            reported_time = reported_at.replace(tzinfo=timezone.utc)
        else:
            reported_time = reported_at

        now = datetime.now(timezone.utc)
        age_hours = max(
            0,
            (now - reported_time).total_seconds() / 3600,
        )

        if age_hours >= 72:
            score += 20
            reasons.append(
                "Complaint has remained open for more than 72 hours."
            )

        elif age_hours >= 48:
            score += 15
            reasons.append(
                "Complaint has remained open for more than 48 hours."
            )

        elif age_hours >= 24:
            score += 10
            reasons.append(
                "Complaint has remained open for more than 24 hours."
            )

    # ---------------------------------------------------------
    # 6. DUPLICATE SIGNAL
    # ---------------------------------------------------------

    if is_duplicate:
        score += 5
        reasons.append(
            "A similar complaint was previously detected nearby."
        )

    # ---------------------------------------------------------
    # 7. ROUTING CONFIDENCE
    # ---------------------------------------------------------

    if routing_confidence is not None:

        if routing_confidence < 0.50:
            score += 5
            reasons.append(
                "Routing confidence is low, so manual review may be required."
            )

    # ---------------------------------------------------------
    # 8. FINAL PRIORITY
    # ---------------------------------------------------------

    if score >= 80:
        priority = "CRITICAL"

    elif score >= 55:
        priority = "HIGH"

    elif score >= 30:
        priority = "NORMAL"

    else:
        priority = "LOW"

    # ---------------------------------------------------------
    # 9. RESPONSE GUIDANCE
    # ---------------------------------------------------------

    actions = {
        "CRITICAL": (
            "Immediate attention recommended. "
            "Assign to an available authority officer and "
            "consider escalation."
        ),
        "HIGH": (
            "Prioritize for early field inspection and action."
        ),
        "NORMAL": (
            "Process through the normal authority queue."
        ),
        "LOW": (
            "Add to the regular civic work queue."
        ),
    }

    return {
        "priority": priority,
        "score": score,
        "reasons": reasons,
        "recommended_action": actions[priority],
    }