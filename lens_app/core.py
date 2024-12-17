from datetime import datetime
from fhirpathpy import evaluate
from dotenv import load_dotenv
import os
from openai import OpenAI
import json
from ollama import Client
import pypandoc
from bs4 import BeautifulSoup
from groq import Groq

load_dotenv()

SERVER_URL = os.getenv("SERVER_URL")
MODEL_URL = os.getenv("MODEL_URL")
print("Charging the model: " + MODEL_URL)
client = Client(host=MODEL_URL)

if MODEL_URL is None:
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.getenv("OPENAI_KEY"),
    )

groqclient = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
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
            print("Error parsing response")
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

    if conditions:
        for cond in conditions:
            diagnostics.append(cond["resource"]["code"]["coding"][0]["display"])

    medications = evaluate(
        ips, "Bundle.entry.where(resource.resourceType=='Medication')", []
    )
    meds = []
    for med in medications:
        meds.append(med["resource"]["code"]["coding"][0]["display"])

    return gender, age, diagnostics, meds


def transform_fhir_epi(epi):
    # print(epi)
    new_epi = ""
    idx = 0

    for ep in epi:
        # print("eeeeeeee", ep)
        idx += 1
        for k, v in ep.items():
            if idx not in [0, 1, 8]:
                #  print(idx, "----", k, v)
                soup = BeautifulSoup(v, "html.parser")
                cleaned_html = ""
                # Remove all text nodes
                for element in soup.find_all(text=True):
                    #  print(element)
                    cleaned_html += element.extract() + " "

                new_epi += "\n" + k + "\n\n" + cleaned_html
    print("LENGTH", len(new_epi))
    print("LENGTH", len(new_epi.split()))
    return new_epi


def format_response(res):
    # print("Raw response: " + res)

    # response_markdown = res.strip()

    # print("Stripped response: " + response_markdown)
    # # Replace bullet symbols (•) with an asterisk (*)
    # cleaned_data = response_markdown.replace("•", "\n*")
    # response = markdown.markdown(cleaned_data)

    # response = response.replace("\n", "")

    response = pypandoc.convert_text(res, "html", format="gfm")

    return response


def summarize_no_personalization(language, epi, model):
    epi_text = transform_fhir_epi(epi)

    lang = LANGUAGE_MAP[language]
    print("++++" * 40, lang)
    prompt = (
        "Write a concise summary of the following text delimited by triple backquotes. Return your response in bullet points which covers the key points of the text. "
        + "You must only use the information provided in the text and avoid introducing any new information. "
        + "The summary should be clear, accurate, and comprehensive, highlighting the main ideas and key details of the text. "
        + "It is of extreme importance that you summarize the document in "
        + lang
        + " and this is totally mandatory. Otherwise the reader will not understand. \n"
        + "```"
        + epi_text
        + "```"
        + "\nBULLET POINT SUMMARY:"
    )
    print("the prompt will be:" + prompt)

    systemMessage = (
        """
        As a professional summarizer, create a concise and comprehensive summary of the provided text, be it an article, post, conversation, or passage, while adhering to these guidelines:
        
        1. You must answer in """
        + lang
        + """ and this is totally mandatory. Otherwise I will not understand. \n
        
        2. Craft a summary that is detailed, thorough, in-depth, and complex, while maintaining clarity and conciseness.
        3. Incorporate main ideas and essential information, eliminating extraneous language and focusing on critical aspects.
        4. Rely strictly on the provided text, without including external information.
        5. You MUST be impersonal and refer to the patient as a person, but NEVER for its name.\n
        6. You must be direct and not lose time on introducing the summary, and MUST NOT GREET the patient.\n
        7. You MUST start with the summary without introduction.\n
        """
    )
    #        5. Format the summary in paragraph form for easy understanding.
    #        6. Ensure the summary is well-structured, coherent, and logically organized.

    if "groq" in model:
        chat_completion = groqclient.chat.completions.create(
            messages=[
                {"role": "system", "content": systemMessage},
                {"role": "user", "content": prompt},
            ],
            model="llama3-70b-8192",
            temperature=0.05,
        )

        response = format_response(chat_completion.choices[0].message.content)
    else:
        result = client.chat(
            model="llama3",
            messages=[
                {"content": systemMessage, "role": "system"},
                {"content": prompt, "role": "assistant"},
            ],
            stream=False,
            keep_alive="-1m",
            options={"seed": 1234, "temperature": 0},
        )

        response = format_response(result["message"]["content"])

    return {
        "response": response,
        "prompt": prompt,
        "datetime": datetime.now(),
        "model": model,
        "lens": "summary_no_personalization",
    }


def summarize(language, epi, gender, age, diagnostics, medications, model):
    epi_text = transform_fhir_epi(epi)

    lang = LANGUAGE_MAP[language]
    print("++++" * 40, lang)
    prompt = (
        "Write a concise summary of the following text delimited by triple backquotes. Return your response in bullet points which covers the key points of the text. "
        + "You must only use the information provided in the text and avoid introducing any new information. "
        + "The summary should be clear, accurate, and comprehensive, highlighting the main ideas and key details of the text. "
        + "It is of extreme importance that you summarize the document in "
        + lang
        + " and this is totally mandatory. Otherwise the reader will not understand. \n"
        + "It should be written in a way that a person of gender: "
        + gender
        + " and with "
        + str(age)
        + " of age should be able to understand."
        "You must reference highlight something that relates with the following topics and terms:"
        + "|".join(diagnostics)
        + "|".join(medications)
        + "```"
        + epi_text
        + "```"
        + "\nBULLET POINT SUMMARY:"
    )
    print("the prompt will be:" + prompt)

    systemMessage = (
        """
        As a professional summarizer, create a concise and comprehensive summary of the provided text, be it an article, post, conversation, or passage, while adhering to these guidelines:
        
        1. You must answer in """
        + lang
        + """ and this is totally mandatory. Otherwise I will not understand. \n
        
        2. Craft a summary that is detailed, thorough, in-depth, and complex, while maintaining clarity and conciseness.
        3. Incorporate main ideas and essential information, eliminating extraneous language and focusing on critical aspects.
        4. Rely strictly on the provided text, without including external information.

        7. You must take into account the patient information. \n
        8. You MUST be impersonal and refer to the patient as a person, but NEVER for its name.\n
        9. You must be direct and not lose time on introducing the summary, and MUST NOT GREET the patient.\n
        10. You MUST start with the summary without introduction.\n
        """
    )
    #        5. Format the summary in paragraph form for easy understanding.
    #        6. Ensure the summary is well-structured, coherent, and logically organized.

    if "groq" in model:
        chat_completion = groqclient.chat.completions.create(
            messages=[
                {"role": "system", "content": systemMessage},
                {"role": "user", "content": prompt},
            ],
            model="llama3-70b-8192",
            temperature=0.05,
        )

        response = format_response(chat_completion.choices[0].message.content)
    else:
        result = client.chat(
            model="llama3",
            messages=[
                {"content": systemMessage, "role": "system"},
                {"content": prompt, "role": "assistant"},
            ],
            stream=False,
            keep_alive="-1m",
            options={"seed": 1234, "temperature": 0},
        )

        response = format_response(result["message"]["content"])

    return {
        "response": response,
        "prompt": prompt,
        "datetime": datetime.now(),
        "model": model,
        "lens": "summarize",
    }


def summarize2(
    language, drug_name, gender, age, diagnostics, medications, model="graviting-llama"
):
    # print(epi_text)
    # model = "gpt-4"
    lang = LANGUAGE_MAP[language]

    diagnostics_texts = ""

    if diagnostics:
        diagnostics_texts = "with the following diagnostics "
        for diag in diagnostics:
            diagnostics_texts += diag + ", "

    else:
        diagnostics_texts = "without any diagnostics"

    prompt = f"The drug name is {drug_name}. Please explain it in a way a person with {age} years old can understand. Also take into account the patient is a {gender} {diagnostics_texts} and medications {medications}. Please explain the pros and cons of the medication. Especially for the other medication I am taking and conditions. You must answer in {lang} and this is totally mandatory. Otherwise I will not understand. Answer right below this line:"
    print("the prompt will be:\n" + prompt)
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
            model="llama3.1",
            messages=[
                {"content": systemMessage, "role": "system"},
                {"content": prompt_message, "role": "assistant"},
            ],
            stream=False,
            options={"seed": 1234, "temperature": 0}
        )

        response = format_response(result["message"]["content"])

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
            keep_alive="-1m",
        )

        response = format_response(result["message"]["content"])

    if "llama3" in model:
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
            model="llama3",
            messages=[
                {"content": systemMessage, "role": "system"},
                {"content": prompt_message, "role": "assistant"},
            ],
            stream=False,
            keep_alive="-1m",
        )

        response = format_response(result["message"]["content"])

    return {
        "response": response,
        "prompt": prompt,
        "datetime": datetime.now(),
        "model": model,
        "lens": "summarize2",
    }
