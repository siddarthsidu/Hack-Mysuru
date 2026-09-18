from pathlib import Path
from PIL import Image


CIVIC_ISSUE_RULES = {
    "garbage": {
        "keywords": [
            "garbage",
            "trash",
            "waste",
            "dump",
            "rubbish",
            "plastic",
            "litter",
        ],
        "severity": "high",
        "action": "Clear the waste and inspect the area for recurring dumping.",
    },
    "construction_waste": {
        "keywords": [
            "construction",
            "debris",
            "rubble",
            "cement",
            "brick",
            "concrete",
        ],
        "severity": "high",
        "action": "Remove construction debris and identify the dumping source.",
    },
    "pothole": {
        "keywords": [
            "pothole",
            "road damage",
            "road hole",
            "damaged road",
            "broken road",
        ],
        "severity": "high",
        "action": "Inspect the road and schedule repair based on traffic risk.",
    },
    "waterlogging": {
        "keywords": [
            "waterlogging",
            "flood",
            "standing water",
            "water accumulation",
            "flooded road",
        ],
        "severity": "high",
        "action": "Inspect drainage and clear the obstruction causing water accumulation.",
    },
    "overflowing_bin": {
        "keywords": [
            "overflowing bin",
            "full bin",
            "overflow bin",
            "bin overflow",
        ],
        "severity": "medium",
        "action": "Schedule waste collection and inspect collection frequency.",
    },
    "streetlight": {
        "keywords": [
            "streetlight",
            "street light",
            "lamp",
            "light pole",
            "broken light",
        ],
        "severity": "medium",
        "action": "Inspect the streetlight and replace or repair the faulty unit.",
    },
}


def analyze_image(
    image_path: str,
    description: str | None = None,
) -> dict:
    """
    Demo/local civic vision engine.

    This version does not require an external AI API.
    It validates the image and combines basic image metadata
    with the citizen's description to produce a structured
    civic analysis.

    Later this function can be replaced by a real multimodal
    model without changing the API contract.
    """

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError("Uploaded image was not found.")

    try:
        with Image.open(path) as image:
            width, height = image.size
            image_format = image.format
    except Exception as exc:
        raise ValueError("The uploaded file is not a valid image.") from exc

    text = (description or "").lower().strip()

    detected_issue = None
    matched_keywords = []

    for issue_type, rule in CIVIC_ISSUE_RULES.items():
        matches = [
            keyword
            for keyword in rule["keywords"]
            if keyword in text
        ]

        if matches:
            detected_issue = issue_type
            matched_keywords = matches
            break

    if detected_issue:
        rule = CIVIC_ISSUE_RULES[detected_issue]

        return {
            "success": True,
            "engine": "CivicRoute Local Vision Engine",
            "issue_type": detected_issue,
            "severity": rule["severity"],
            "confidence": 0.72,
            "description": (
                f"Possible {detected_issue.replace('_', ' ')} "
                "detected from the submitted evidence and complaint description."
            ),
            "explanation": (
                "The system matched civic-problem indicators in the "
                "submitted complaint and validated the uploaded image."
            ),
            "suggested_action": rule["action"],
            "matched_keywords": matched_keywords,
            "image": {
                "width": width,
                "height": height,
                "format": image_format,
            },
        }

    return {
        "success": True,
        "engine": "CivicRoute Local Vision Engine",
        "issue_type": "needs_review",
        "severity": "medium",
        "confidence": 0.35,
        "description": (
            "The submitted evidence could not be confidently "
            "classified into a supported civic issue."
        ),
        "explanation": (
            "No strong civic issue indicators were found in the "
            "submitted description. The report should be reviewed."
        ),
        "suggested_action": (
            "Request additional evidence or manually review the complaint."
        ),
        "matched_keywords": [],
        "image": {
            "width": width,
            "height": height,
            "format": image_format,
        },
    }