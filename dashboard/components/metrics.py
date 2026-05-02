def confidence_badge(level: str) -> str:
    badges = {
        "high": "🟢 High confidence",
        "medium": "🟡 Medium confidence",
        "low": "🔴 Low confidence",
    }
    return badges.get(level, "⚪ Unknown")

def sentiment_label(score: float) -> str:
    if score > 0.33:
        return "Positive"
    elif score < -0.33:
        return "Negative"
    return "Neutral"
