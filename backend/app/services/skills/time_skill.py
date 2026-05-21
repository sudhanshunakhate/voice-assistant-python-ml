from datetime import datetime


def tell_time() -> str:
    now = datetime.now()
    return (
        f"The current time is {now.strftime('%I:%M %p').lstrip('0') or '12:%M %p'} "
        f"and the date is {now.strftime('%A, %d %B %Y')}."
    )


def matches(text: str) -> bool:
    t = text.lower()
    return any(
        w in t
        for w in (
            "time",
            "date",
            "what day",
            "today's date",
            "clock",
        )
    )
