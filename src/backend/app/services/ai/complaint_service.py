import re


ISSUE_KEYWORDS = {
    "garbage": [
        "garbage",
        "trash",
        "waste",
        "rubbish",
        "litter",
        "dump",
        "dumping",
    ],
    "construction_waste": [
        "construction",
        "debris",
        "rubble",
        "cement",
        "brick",
        "concrete",
    ],
    "pothole": [
        "pothole",
        "road hole",
        "road damage",
        "damaged road",
        "broken road",
    ],
    "waterlogging": [
        "waterlogging",
        "water logging",
        "flood",
        "flooded",
        "standing water",
        "water accumulation",
    ],
    "overflowing_bin": [
        "overflowing bin",
        "overflow bin",
        "full bin",
        "bin is full",
    ],
    "streetlight": [
        "streetlight",
        "street light",
        "lamp",
        "broken light",
        "light pole",
    ],
}


SEVERITY_KEYWORDS = {
    "critical": [
        "dangerous",
        "accident",
        "blocked completely",
        "major flood",
        "emergency",
        "life threatening",
    ],
    "high": [
        "large",
        "heavy",
        "overflowing",
        "blocked",
        "danger",
        "unsafe",
        "severe",
        "major",
    ],
    "medium": [
        "broken",
        "damaged",
        "small",
        "moderate",
        "bad",
    ],
}


def _detect_issue(text: str):
    scores = {}

    for issue_type, keywords in ISSUE_KEYWORDS.items():
        score = sum(
            1
            for keyword in keywords
            if keyword in text
        )

        if score:
            scores[issue_type] = score

    if not scores:
        return "needs_review", 0.35

    issue_type = max(
        scores,
        key=scores.get,
    )

    confidence = min(
        0.60 + (scores[issue_type] * 0.08),
        0.94,
    )

    return issue_type, round(confidence, 2)


def _detect_severity(text: str):
    for severity in ["critical", "high", "medium"]:
        for keyword in SEVERITY_KEYWORDS[severity]:
            if keyword in text:
                return severity

    return "medium"


def _extract_duration(text: str):
    patterns = [
        r"(\d+)\s*(day|days)",
        r"(\d+)\s*(hour|hours)",
        r"(\d+)\s*(week|weeks)",
        r"(\d+)\s*(month|months)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            number = match.group(1)
            unit = match.group(2)

            return f"{number} {unit}"

    if "yesterday" in text:
        return "since yesterday"

    if "today" in text:
        return "since today"

    return None


def _build_summary(
    text: str,
    issue_type: str,
):
    clean_text = " ".join(text.split())

    if len(clean_text) > 180:
        clean_text = clean_text[:177] + "..."

    if issue_type == "needs_review":
        return clean_text

    readable_type = issue_type.replace(
        "_",
        " ",
    )

    return (
        f"{readable_type.capitalize()} reported: "
        f"{clean_text}"
    )


def _suggest_action(issue_type: str):
    actions = {
        "garbage": (
            "Inspect the location and arrange waste "
            "clearance. Check for recurring dumping."
        ),
        "construction_waste": (
            "Inspect the site, remove construction debris "
            "and identify the dumping source."
        ),
        "pothole": (
            "Inspect the road condition and schedule "
            "repair based on traffic and safety risk."
        ),
        "waterlogging": (
            "Inspect drainage, identify blockage and "
            "clear accumulated water."
        ),
        "overflowing_bin": (
            "Arrange waste collection and inspect "
            "collection frequency."
        ),
        "streetlight": (
            "Inspect the lighting unit and repair or "
            "replace the faulty equipment."
        ),
        "needs_review": (
            "Request additional information or manually "
            "review the complaint."
        ),
    }

    return actions.get(
        issue_type,
        actions["needs_review"],
    )


def analyze_complaint(text: str):
    if not text or not text.strip():
        raise ValueError(
            "Complaint description cannot be empty."
        )

    normalized_text = " ".join(
        text.lower().split()
    )

    issue_type, confidence = _detect_issue(
        normalized_text
    )

    severity = _detect_severity(
        normalized_text
    )

    duration = _extract_duration(
        normalized_text
    )

    summary = _build_summary(
        text.strip(),
        issue_type,
    )

    suggested_action = _suggest_action(
        issue_type
    )

    urgency = (
        "critical"
        if severity == "critical"
        else "high"
        if severity == "high"
        else "normal"
    )

    return {
        "success": True,
        "engine": "CivicRoute Complaint Intelligence",
        "issue_type": issue_type,
        "severity": severity,
        "urgency": urgency,
        "confidence": confidence,
        "duration": duration,
        "summary": summary,
        "suggested_action": suggested_action,
    }