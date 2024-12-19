import uuid

import requests
from fhir.resources.annotation import Annotation
from fhir.resources.composition import Composition
from flask import jsonify, request

from lens_app import app
from lens_app.core import (
    SERVER_URL,
    process_bundle,
    process_ips,
    summarize,
    summarize2,
    summarize3,
    summarize_no_personalization,
)

print(app.config)


@app.route("/", methods=["GET"])
def hello():
    json_obj = {
        "message": "Hello and welcome to the Summary Lens API",
        "status": "OK",
    }
    return jsonify(json_obj)


##POST https://fosps.gravitatehealth.eu/focusing/focus/bundlepackageleaflet-es-56a32a5ee239fc834b47c10db1faa3fd?preprocessors=preprocessing-service-manual&patientIdentifier=Cecilia-1&lenses=lens-selector-mvp2_pregnancy


@app.route("/summary", methods=["GET", "POST"])
@app.route("/summary/<bundleid>", methods=["GET", "POST"])
def lens_app(bundleid=None):
    TITLE_DOC = {
        "en": "Electronic Product Information Summary",
        "es": "Resumen del Prospecto",
        "it": "Sintesi del prospetto",
        "dk": "Resumé af indlægsseddel",
        "da": "Resumé af indlægsseddel",
        "no": "Resumé av pakningsvedlegget",
    }
    epibundle = None
    ips = None
    # Get the query parameters from the request
    lenses = request.args.get("lenses", "")
    patientIdentifier = request.args.get("patientIdentifier", "")
    model = request.args.get("model", "")
    if model not in [
        "graviting-llama",
        "mistral",
        "llama3",
        "llama3.1",
        "llama-3.1-70b-Versatile",
        "Mixtral-8x7b-32768",
        "Llama3-70b-8192",
        "Llama3-8b-8192",
        "Llama-3.2-90b-Text-Preview",
    ]:
        return "Error: Unknown Model", 404
    print(lenses, patientIdentifier)
    if lenses not in ["lens-summary", "lens-summary-2"]:
        return "Error: lens not supported", 404

    if request.method == "GET" and lenses == "":
        return "Error: missing parameters", 404

    print(SERVER_URL)
    if request.method == "POST":
        data = request.json
        epibundle = data.get("epi")
        ips = data.get("ips")
        print(epibundle)

        if epibundle is None and bundleid is None:
            return "Error: missing EPI", 404

    if epibundle is None:
        print("epibundle is none")
        # print(epibundle)
        # print(bundleid)
        print(SERVER_URL + "epi/api/fhir/Bundle/" + bundleid)
        print(ips)
        epibundle = requests.get(SERVER_URL + "epi/api/fhir/Bundle/" + bundleid).json()
    print(epibundle)
    language, epi, drug_name = process_bundle(epibundle)
    # GET https://fosps.gravitatehealth.eu/ips/api/fhir/Patient/$summary?identifier=alicia-1

    title = TITLE_DOC[language]
    print(SERVER_URL)
    if ips is None and patientIdentifier != "":
        # print(ips)
        body = {
            "resourceType": "Parameters",
            "id": "example",
            "parameter": [
                {"name": "identifier", "valueIdentifier": {"value": patientIdentifier}}
            ],
        }
        ips = requests.post(
            SERVER_URL + "ips/api/fhir/Patient/$summary", json=body, timeout=10
        ).json()
    # print(ips)
    if ips:
        gender, age, diagnostics, medications = process_ips(ips)

    # print(language, epi, gender, age, diagnostics, medications)
    if ips is None:
        print("NO IPS")
        if model not in [
            "mistral",
            "llama3",
            "llama3.1",
            "llama-3.1-70b-Versatile",
            "Mixtral-8x7b-32768",
            "Llama3-70b-8192",
            "Llama3-8b-8192",
            "Llama-3.2-90b-Text-Preview",
        ]:
            return "Error: Model not supported without IPS", 404
        else:
            response = summarize_no_personalization(language, epi, model)
    elif lenses == "lens-summary":
        model = "llama3.1" if model == "graviting-llama" else model
        response = summarize(
            language, epi, gender, age, diagnostics, medications, model
        )
    elif lenses == "lens-summary-2":
        model = "llama3.1" if model == "graviting-llama" else model
        # to prevent change on the app 19/12/2024
        response = summarize(
            language, epi, gender, age, diagnostics, medications, model
        )
    elif lenses == "lens-summary-3":
        model = "llama3.1" if model == "graviting-llama" else model
        response = summarize3(
            language, epi, gender, age, diagnostics, medications, model
        )
    elif lenses == "lens-summary-2-2":
        model = "llama3.1" if model == "graviting-llama" else model
        response = summarize2(
            language, drug_name, gender, age, diagnostics, medications, model
        )

    # Return the JSON response
    print(response)
    if bundleid is None:
        bundleid = epibundle["id"]

    json_obj = {
        "resourceType": "Composition",
        "meta": {
            "profile": [
                "htthttp://hl7.eu/fhir/ig/gravitate-health/StructureDefinition/SummaryData"
            ]
        },
        "identifier": [
            {"system": "http://gravitate-health.eu/summary", "value": str(uuid.uuid4())}
        ],
        "status": "final",
        "type": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "11488-4",
                    "display": "Consult note",
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "LP183761-8",
                        "display": "Report",
                    }
                ]
            }
        ],
        "author": [{"display": "GH Lens"}],
        "date": "2012-01-04T09:10:14Z",
        "title": title,
        "relatesTo": [
            {"type": "derived-from", "resourceReference": {"reference": bundleid}}
        ],
        "section": [
            {
                "title": title,
                "text": {
                    "status": "additional",
                    "div": "",
                },
            },
        ],
    }
    print(response["datetime"].strftime("%Y-%m-%dT%H:%M:%SZ"))
    comp = Composition.parse_obj(json_obj)
    comp.date = response["datetime"].strftime("%Y-%m-%dT%H:%M:%SZ")
    comp.author[0].display = response["model"]
    note = Annotation.construct()
    note.text = response["prompt"].replace("\xa0", " ")
    # comp.note[0].text = response["prompt"]
    comp.note = list()
    comp.note.append(note)
    comp.section[0].text.div = (
        '<div xmlns="http://www.w3.org/1999/xhtml">' + response["response"] + "</div>"
    )
    return jsonify(comp.dict())
