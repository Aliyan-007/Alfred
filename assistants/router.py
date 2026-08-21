import re


# Common Roman Urdu words.
ROMAN_URDU_WORDS = {
    "aap",
    "ap",
    "aapka",
    "aapki",
    "aapko",
    "aapne",
    "mujhe",
    "mujh",
    "mera",
    "meri",
    "mere",
    "hum",
    "ham",
    "hain",
    "hoon",
    "hun",
    "hai",
    "kaise",
    "kaisa",
    "kaisi",
    "kya",
    "kyun",
    "kyu",
    "kyon",
    "kab",
    "kahan",
    "kidhar",
    "ka",
    "ki",
    "ke",
    "ko",
    "se",
    "mein",
    "main",
    "me",
    "par",
    "pe",
    "aur",
    "lekin",
    "magar",
    "bhi",
    "nahi",
    "nahin",
    "nah",
    "bilkul",
    "theek",
    "thik",
    "shukriya",
    "sawal",
    "sawaal",
    "pooch",
    "poochna",
    "poochne",
    "bataye",
    "batao",
    "bataiye",
    "madad",
    "kar",
    "karo",
    "karein",
    "karti",
    "karta",
    "karna",
    "chahta",
    "chahti",
    "chahiye",
    "mujhse",
    "aapse",
    "aik",
    "ek",
    "do",
    "acha",
    "achha",
    "accha",
    "kyunke",
    "kyunki",
    "abhi",
    "aaj",
    "kal",
    "yahan",
    "wahan",
    "mera",
    "naam",
    "student",
}


def contains_non_latin(text: str) -> bool:
    """
    Detect Urdu, Arabic, Hindi/Devanagari and other
    non-Latin scripts.
    """

    for character in text:

        code = ord(character)

        # Arabic / Urdu.
        if 0x0600 <= code <= 0x06FF:
            return True

        # Arabic supplement.
        if 0x0750 <= code <= 0x077F:
            return True

        # Arabic extended.
        if 0x08A0 <= code <= 0x08FF:
            return True

        # Devanagari / Hindi.
        if 0x0900 <= code <= 0x097F:
            return True

    return False


def detect_assistant(text: str) -> str:
    """
    Decide which assistant should answer.

    ALFRED:
        English

    F.R.I.D.A.Y.:
        Urdu
        Roman Urdu
        Hindi-script transcription of Urdu
        Urdu-English mixed speech
    """

    text = text.strip()

    if not text:
        return "ALFRED"

    # -----------------------------------------------------
    # Urdu / Arabic / Hindi script
    # -----------------------------------------------------

    if contains_non_latin(text):
        return "F.R.I.D.A.Y."

    # -----------------------------------------------------
    # Roman Urdu
    # -----------------------------------------------------

    words = re.findall(
        r"[a-zA-Z]+",
        text.lower(),
    )

    if not words:
        return "ALFRED"

    roman_urdu_matches = sum(
        1
        for word in words
        if word in ROMAN_URDU_WORDS
    )

    # Strong Roman Urdu signal.
    if roman_urdu_matches >= 2:
        return "F.R.I.D.A.Y."

    # A single very strong Urdu marker.
    strong_markers = {
        "mujhe",
        "aap",
        "aapse",
        "mujhse",
        "hain",
        "hoon",
        "sawal",
        "sawaal",
        "shukriya",
        "kaise",
        "kaisi",
        "kyun",
        "nahi",
        "madad",
    }

    if any(
        word in strong_markers
        for word in words
    ):
        return "F.R.I.D.A.Y."

    # -----------------------------------------------------
    # Default
    # -----------------------------------------------------

    return "ALFRED"