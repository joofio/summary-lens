import json
from flask import render_template, request, jsonify
from lens_app import app
import requests
from lens_app.core import SERVER_URL, process_bundle, process_ips, summarize, summarize2
from fhir.resources.composition import Composition
from fhir.resources.annotation import Annotation

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
    preprocessor = request.args.get("preprocessors", "")
    lenses = request.args.get("lenses", "")
    patientIdentifier = request.args.get("patientIdentifier", "")
    model = request.args.get("model", "")
    print(preprocessor, lenses, patientIdentifier)
    if lenses not in ["lens-summary", "lens-summary-2"]:
        return "Error: lens not supported", 404
    if preprocessor not in ["preprocessing-service-manual"]:
        return "Error: preprocessor not supported", 404

    if request.method == "GET":
        if preprocessor == "" or lenses == "" or patientIdentifier == "":
            return "Error: missing parameters", 404

    print(SERVER_URL)
    if request.method == "POST":
        data = request.json
        epibundle = data.get("epi")
        ips = data.get("ips")
        print(epibundle)
        if ips is None and patientIdentifier == "":
            return "Error: missing IPS", 404
        # preprocessed_bundle, ips = separate_data(bundleid, patientIdentifier)
        if epibundle is None and bundleid is None:
            return "Error: missing EPI", 404

    if epibundle == None:
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
    if ips == None:
        # print(ips)
        ips = requests.get(
            SERVER_URL + "ips/api/fhir/Patient/$summary?identifier=" + patientIdentifier
        ).json()
        print(ips)
    # print(ips)
    gender, age, diagnostics, medications = process_ips(ips)

    # print(language, epi, gender, age, diagnostics, medications)
    if lenses == "lens-summary":
        response = summarize(language, epi, gender, age, diagnostics, medications)
    if lenses == "lens-summary-2":
        response = summarize2(
            language, drug_name, gender, age, diagnostics, medications, model
        )
    # Return the JSON response
    print(response)
    json_obj = {
        "resourceType": "Composition",
        "id": "example",
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
        "section": [
            {
                "title": title,
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "10157-6",
                            "display": "History of family member diseases Narrative",
                        }
                    ]
                },
                "text": {
                    "status": "additional",
                    "div": "",
                },
            },
        ],
    }
    comp = Composition.parse_obj(json_obj)
    comp.date = response["datetime"]
    comp.author[0].display = response["model"]
    note = Annotation.construct()
    note.text = response["prompt"]
    # comp.note[0].text = response["prompt"]
    comp.note = list()
    comp.note.append(note)
    comp.section[0].text.div = (
        '<div xmlns="http://www.w3.org/1999/xhtml">' + response["response"] + "</div>"
    )
    return jsonify(comp.dict())
