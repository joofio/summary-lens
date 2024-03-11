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


@app.route("/summary/<bundle>", methods=["GET"])
def lens_app(bundle):
    # Get the query parameters from the request
    preprocessor = request.args.get("preprocessors", "")
    lenses = request.args.get("lenses", "")
    patientIdentifier = request.args.get("patientIdentifier", "")
    model = request.args.get("model", "")
    print(preprocessor, lenses, patientIdentifier)
    if preprocessor == "" or lenses == "" or patientIdentifier == "":
        return "Error: missing parameters", 404
    if preprocessor not in ["preprocessing-service-manual"]:
        return "Error: preprocessor not supported", 404

    if lenses not in ["lens-summary", "lens-summary-2"]:
        return "Error: lens not supported", 404
    print(SERVER_URL)

    # preprocessed_bundle, ips = separate_data(bundleid, patientIdentifier)
    bundle = requests.get(SERVER_URL + "epi/api/fhir/Bundle/" + bundle)

    language, epi, drug_name = process_bundle(bundle.json())
    # GET https://fosps.gravitatehealth.eu/ips/api/fhir/Patient/$summary?identifier=alicia-1
    print(SERVER_URL)
    ips = requests.get(
        SERVER_URL + "ips/api/fhir/Patient/$summary?identifier=" + patientIdentifier
    )
    # print(ips)
    gender, age, diagnostics, medications = process_ips(ips.json())

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
        "identifier": [
            {"system": "http://healthintersections.com.au/test", "value": "1"}
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
        "title": "Consultation Note",
        "section": [
            {
                "title": "History of family member diseases",
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
                    "status": "generated",
                    "div": '<div xmlns="http://www.w3.org/1999/xhtml">\n\t\t\t\t<p>History of family member diseases - not available</p>\n\t\t\t</div>',
                },
                "emptyReason": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/list-empty-reason",
                            "code": "withheld",
                            "display": "Information Withheld",
                        }
                    ]
                },
            },
        ],
    }
    comp = Composition.parse_obj(json_obj)
    comp.date = str(response["datetime"])
    comp.author[0].display = response["model"]
    note = Annotation.construct()
    note.text = response["prompt"]
    # comp.note[0].text = response["prompt"]
    comp.note = list()
    comp.note.append(note)
    comp.section[0].text.div = (
        '<div xmlns="http://www.w3.org/1999/xhtml">'
        + response["response"]
        + "</div>"
    )
    return jsonify(comp.dict())
