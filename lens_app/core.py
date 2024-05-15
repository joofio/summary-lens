from datetime import datetime
from fhirpathpy import evaluate
from dotenv import load_dotenv
import os
from openai import OpenAI
import requests
import json
from ollama import Client

load_dotenv()

SERVER_URL = os.getenv("SERVER_URL")
MODEL_URL = os.getenv("MODEL_URL")
print(MODEL_URL)
client = Client(host=MODEL_URL)

if MODEL_URL is None:
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.getenv("OPENAI_KEY"),
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


def parse_response(response, type="response"):
    parsed_response = ""
    for line in response.split("\n"):
        # print(line)
        try:
            d = json.loads(line)
            if type == "response":
                parsed_response += d["response"]
            if type == "chat":
                parsed_response += d["message"]["content"]
        except:
            pass
    return parsed_response


def process_bundle(bundle):
    # print(bundle)
    mp = evaluate(
        bundle,
        "Bundle.entry.where(resource.resourceType=='MedicinalProductDefinition')",
        [],
    )[0]["resource"]
    #  print(mp)
    drug_name = mp["name"][0]["productName"]
    language = bundle["language"]
    # print(language)
    comp = bundle["entry"][0]["resource"]
    epi_full_text = []
    for sec in comp["section"]:
        if sec.get("section"):
            for subsec in sec["section"]:
                #  print(subsec["text"]["div"])
                epi_full_text.append({subsec["title"]: subsec["text"]["div"]})
    # print(sec["text"])

    return language, epi_full_text, drug_name


def process_ips(ips):
    print(ips)
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
    # print(conditions)
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
    model = "gpt-4"

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
        model=model,
    )
    return {
        "response": chat_completion.choices[0].message.content,
        "prompt": prompt,
        "datetime": datetime.now().isoformat(),
        "model": model,
    }


def summarize2(
    language, drug_name, gender, age, diagnostics, medications, model="llama"
):
    # print(epi_text)
    # model = "gpt-4"
    lang = LANGUAGE_MAP[language]
    prompt = (
        "The drug name is "
        + drug_name
        + ". Please explain it in a way a person with "
        + str(age)
        + " years old can understand. Also take into account the patient is a "
        + gender
        + " with the following diagnostics "
        + "".join(diagnostics)
        + " and medications "
        + "".join(medications)
        + ". Please explain the pros and cons of the medication. Especially for the other medication I am taking and conditions. You must answer in "
        + lang
        + " and this is totally mandatory. Otherwise I will not understand."
        + "\n\nAnswer:\n\n"
    )
    if "gpt" in model:
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
            model=model,
        )
        response = (chat_completion.choices[0].message.content,)

    if "graviting-llama" in model:
        # result = requests.post(
        #     "http://localhost:11434/api/generate",
        #     json={
        #         "model": "llama2",
        #         "prompt": prompt,
        #     },
        # )
        #  print(response)

        systemMessage = (
            """
        You must follow this indications extremety strictly:\n
        1. You must answer in """
            + lang
            + """ \n
        2. You must provide a summary of the medication and its pros and cons. \n
        3. You must take into account the patient information. \n
        4. You MUST be impersonal and refer to the patient as a person, but NEVER for its name.\n
        5. You must be direct and not lose time on introducing the summary, and MUST NOT GREET the patient.\n
        """
        )

        print("prompt is:" + prompt)

        prompt_message = prompt

        result = client.chat(
            model="graviting-llama",
            messages=[
                {"content": systemMessage, "role": "system"},
                {"content": prompt_message, "role": "assistant"},
            ],
            stream=False,
            keep_alive="0m",
        )

        response = result["message"]["content"]

    if "mistral" in model:
        systemMessage = (
            """
        You must follow this indications extremety strictly:\n
        1. You must answer in """
            + lang
            + """ \n
        2. You must provide a summary of the medication and its pros and cons. \n
        3. You must take into account the patient information. \n
        4. You MUST be impersonal and refer to the patient as a person, but NEVER for its name.\n
        5. You must be direct and not lose time on introducing the summary, and MUST NOT GREET the patient.\n
        """
        )

        print("prompt is:" + prompt)

        prompt_message = prompt
        result = client.chat(
            model="mistral",
            messages=[
                {"content": systemMessage, "role": "system"},
                {"content": prompt_message, "role": "assistant"},
            ],
            stream=False,
            keep_alive="0m",
        )

        response = result["message"]["content"]

        # response = parse_response(result.text, type="chat")

    return {
        "response": response,
        "prompt": prompt,
        "datetime": datetime.now().isoformat(),
        "model": model,
    }
