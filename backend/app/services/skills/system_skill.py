import platform


def system_info() -> str:
    return (
        f"You are running {platform.system()} {platform.release()} on "
        f"{platform.machine()}. Processor: {platform.processor() or 'unknown'}."
    )


def matches(text: str) -> bool:
    t = text.lower()
    return any(
        w in t
        for w in (
            "system",
            "computer",
            "os",
            "operating system",
            "platform",
            "device info",
        )
    )
