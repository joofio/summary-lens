from datetime import datetime
from fhirpathpy import evaluate
from dotenv import load_dotenv
import os
from openai import OpenAI


load_dotenv()

SERVER_URL = "https://fosps.gravitatehealth.eu/"  # prod
SERVER_URL = "https://gravitate-health.lst.tfo.upm.es/"  # dev


client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv("MY_API_KEY"),
)


LANGUAGE_MAP = {
    "es": "Spanish",
    "en": "English",
    "de": "German",
    "fr": "French",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "ru": "Russian",
    "tr": "Turkish",
    "ar": "Arabic",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "vi": "Vietnamese",
    "th": "Thai",
    "el": "Greek",
    "cs": "Czech",
    "hu": "Hungarian",
    "ro": "Romanian",
    "sv": "Swedish",
    "fi": "Finnish",
    "da": "Danish",
    "no": "Norwegian",
    "is": "Icelandic",
    "et": "Estonian",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "mt": "Maltese",
    "hr": "Croatian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "bg": "Bulgarian",
    "cy": "Welsh",
    "ga": "Irish",
    "gd": "Gaelic",
    "eu": "Basque",
    "ca": "Catalan",
    "gl": "Galician",
}


def process_bundle(bundle):
    # print(bundle)
    language = bundle["language"]
    # print(language)
    comp = bundle["entry"][0]["resource"]
    epi_full_text = []
    for sec in comp["section"]:
        if sec.get("section"):
            for subsec in sec["section"]:
                print(subsec["text"]["div"])
                epi_full_text.append({subsec["title"]: subsec["text"]["div"]})
    # print(sec["text"])

    return language, epi_full_text


def process_ips(ips):
    pat = evaluate(ips, "Bundle.entry.where(resource.resourceType=='Patient')", [])[0][
        "resource"
    ]

    gender = pat["gender"]
    bd = pat["birthDate"]

    # Convert the string to a datetime object
    birth_date = datetime.strptime(bd, "%Y-%m-%d")

    # Get the current date
    current_date = datetime.now()

    # Calculate the age
    age = (
        current_date.year
        - birth_date.year
        - ((current_date.month, current_date.day) < (birth_date.month, birth_date.day))
    )
    conditions = evaluate(
        ips, "Bundle.entry.where(resource.resourceType=='Condition')", []
    )
    diagnostics = []
    print(conditions)
    for cond in conditions:
        diagnostics.append(cond["resource"]["code"]["text"])

    medications = evaluate(
        ips, "Bundle.entry.where(resource.resourceType=='Medication')", []
    )
    meds = []
    for med in medications:
        meds.append(med["resource"]["code"]["coding"][0]["display"])

    return gender, age, diagnostics, meds


def summarize(language, epi, gender, age, diagnostics, medications):
    epi_text = [k + v for k, v in epi[0].items()]
    # print(epi_text)
    lang = LANGUAGE_MAP[language]
    prompt = (
        "Please summarize this electronic patient information leaflet "
        + epi_text[0]
        + " in four paragraphs, taken into account that a person reading it is of the gender "
        + gender
        + " and age "
        + str(age)
        + " with the following diagnostics "
        + "and".join(diagnostics)
        + " and medications "
        + " and ".join(medications)
        + ". Please take into account possible interactions and advice for the patient charachteristcs and try to link to information in the leaflet. Please respond in "
        + lang
    )
    print("the prompt will be:" + prompt)

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are helping a patient better understand a electronic patient information leaflet. Your response should be to try to summarize the leaflet in two paragraphs. The patient is a person. The patient knows you do not provide health advice, but wants to get a summary of a very large and complicated document. You want to focus on summarizing the document, while providing information about counter indication of advice for the patient's medication, gender (like child bearing age and pregancy), other diagnostics",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        model="gpt-3.5-turbo",
    )
    return chat_completion
