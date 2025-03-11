import re

##############################################################################
# Shared helper: phone number processing
##############################################################################
def process_phone_number(phone):
    original = phone.strip()
    sanitized = re.sub(r'\D', '', phone)
    cleaned = ""
    country = ""
    if sanitized:
        if len(sanitized) == 10 and sanitized.startswith("5"):
            cleaned = f"+90{sanitized}"
            country = "Turkey"
        elif len(sanitized) == 11 and sanitized.startswith("05"):
            cleaned = f"+9{sanitized[1:]}"
            country = "Turkey"
        elif len(sanitized) == 12 and sanitized.startswith("90"):
            cleaned = f"+{sanitized}"
            country = "Turkey"
        elif len(sanitized) == 10 and sanitized.startswith("85"):
            cleaned = f"+90{sanitized}"
            country = "Turkey"
        elif len(sanitized) == 12 and sanitized.startswith("9085"):
            cleaned = f"+{sanitized}"
            country = "Turkey"
        elif len(sanitized) == 11 and sanitized.startswith("79"):
            cleaned = f"+{sanitized}"
            country = "Russia"
        elif len(sanitized) == 11 and sanitized.startswith("89"):
            cleaned = f"+79{sanitized[2:]}"
            country = "Russia"
        elif len(sanitized) == 11 and sanitized.startswith("84"):
            cleaned = f"+74{sanitized[2:]}"
            country = "Russia"
        elif len(sanitized) == 11 and sanitized.startswith("88"):
            cleaned = f"+78{sanitized[2:]}"
            country = "Russia"
        elif len(sanitized) == 11 and sanitized.startswith("87"):
            cleaned = f"+77{sanitized[2:]}"
            country = "Kazakhstan"
        elif len(sanitized) == 11 and sanitized.startswith("77"):
            cleaned = f"+77{sanitized[2:]}"
            country = "Kazakhstan"
        elif len(sanitized) == 11 and (sanitized.startswith("99") or sanitized.startswith("49")):
            cleaned = f"+352{sanitized}"
            country = "Luxembourg"
        elif len(sanitized) == 14 and sanitized.startswith("352"):
            cleaned = f"+{sanitized}"
            country = "Luxembourg"
        elif len(sanitized) == 11 and (sanitized.startswith("98") or sanitized.startswith("243") or sanitized.startswith("240")):
            cleaned = f"+62{sanitized}"
            country = "Indonesia"
        elif len(sanitized) == 13 and sanitized.startswith("62"):
            cleaned = f"+{sanitized}"
            country = "Indonesia"
        elif len(sanitized) == 11 and sanitized.startswith("97"):
            cleaned = f"+49{sanitized}"
            country = "Germany"
        elif len(sanitized) == 13 and sanitized.startswith("4997"):
            cleaned = f"+{sanitized}"
            country = "Germany"
        elif len(sanitized) == 11 and sanitized.startswith("6"):
            cleaned = f"+49{sanitized}"
            country = "Germany"
        elif len(sanitized) == 10 and sanitized.startswith("775"):
            cleaned = f"+1{sanitized}"
            country = "US"
        elif len(sanitized) == 10 and sanitized.startswith("212"):
            cleaned = f"+1{sanitized}"
            country = "US"
        elif len(sanitized) == 11 and sanitized.startswith("131"):
            cleaned = f"+{sanitized}"
            country = "US"
        elif len(sanitized) == 8 and sanitized.startswith("185"):
            cleaned = f"+46{sanitized}"
            country = "Sweden"
        elif len(sanitized) == 11 and sanitized.startswith("100"):
            cleaned = f"+886{sanitized}"
            country = "Taiwan"
        elif len(sanitized) == 12 and sanitized.startswith("998"):
            cleaned = f"+{sanitized}"
            country = "Uzbekistan"
        elif len(sanitized) == 12 and sanitized.startswith("996"):
            cleaned = f"+{sanitized}"
            country = "Kyrgyzstan"
        elif len(sanitized) == 12 and sanitized.startswith("992"):
            cleaned = f"+{sanitized}"
            country = "Tajikistan"
        elif len(sanitized) == 12 and sanitized.startswith("375"):
            cleaned = f"+{sanitized}"
            country = "Belarus"
        elif len(sanitized) == 12 and sanitized.startswith("972"):
            cleaned = f"+{sanitized}"
            country = "Israel"
        elif len(sanitized) == 12 and sanitized.startswith("380"):
            cleaned = f"+{sanitized}"
            country = "Ukraine"
        elif len(sanitized) == 12 and sanitized.startswith("994"):
            cleaned = f"+{sanitized}"
            country = "Azerbaijan"
        elif len(sanitized) == 11 and sanitized.startswith("372"):
            cleaned = f"+{sanitized}"
            country = "Estonia"
        elif len(sanitized) == 11 and sanitized.startswith("373"):
            cleaned = f"+{sanitized}"
            country = "Moldova"
        elif len(sanitized) == 11 and sanitized.startswith("27"):
            cleaned = f"+{sanitized}"
            country = "South Africa"
        elif len(sanitized) == 13 and sanitized.startswith("49"):
            cleaned = f"+{sanitized}"
            country = "Germany"
        elif len(sanitized) == 11 and sanitized.startswith("1"):
            cleaned = f"+{sanitized}"
            country = "USA"
        elif len(sanitized) == 12 and sanitized.startswith("57"):
            cleaned = f"+{sanitized}"
            country = "Colombia"
        elif len(sanitized) == 11 and sanitized.startswith("33"):
            cleaned = f"+{sanitized}"
            country = "France"
        elif len(sanitized) == 12 and sanitized.startswith("39"):
            cleaned = f"+{sanitized}"
            country = "Italy"
        elif len(sanitized) == 11 and sanitized.startswith("36"):
            cleaned = f"+{sanitized}"
            country = "Hungary"
        elif len(sanitized) == 11 and sanitized.startswith("34"):
            cleaned = f"+{sanitized}"
            country = "Spain"
        elif len(sanitized) == 11 and sanitized.startswith("31"):
            cleaned = f"+{sanitized}"
            country = "Netherlands"
        elif len(sanitized) == 12 and sanitized.startswith("82"):
            cleaned = f"+{sanitized}"
            country = "Korea, South"
        elif phone.startswith("+"):
            cleaned = sanitized
            country = "Unknown"
        else:
            cleaned = original
            country = "N/A"
    else:
        cleaned = ""
        country = ""
    return {"original": original, "cleaned": cleaned, "country": country}
