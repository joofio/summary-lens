from flask import render_template, request, jsonify
from lens_app import app
import requests
from lens_app.core import SERVER_URL, process_bundle, process_ips, summarize, summarize2

print(app.config)


@app.route("/", methods=["GET"])
def hello():
    return render_template("index.html", result="")


##POST https://fosps.gravitatehealth.eu/focusing/focus/bundlepackageleaflet-es-56a32a5ee239fc834b47c10db1faa3fd?preprocessors=preprocessing-service-manual&patientIdentifier=Cecilia-1&lenses=lens-selector-mvp2_pregnancy


@app.route("/focusing/focus/<bundle>", methods=["GET"])
def lens_app(bundle):
    # Get the query parameters from the request
    preprocessor = request.args.get("preprocessors", "")
    lenses = request.args.get("lenses", "")
    patientIdentifier = request.args.get("patientIdentifier", "")
    print(preprocessor, lenses, patientIdentifier)
    if preprocessor == "" or lenses == "" or patientIdentifier == "":
        return "Error: missing parameters", 404
    if preprocessor not in ["preprocessing-service-manual"]:
        return "Error: preprocessor not supported", 404

    if lenses not in ["lens-summary", "lens-summary-2"]:
        return "Error: lens not supported", 404

    # preprocessed_bundle, ips = separate_data(bundleid, patientIdentifier)
    bundle = requests.get(SERVER_URL + "epi/api/fhir/Bundle/" + bundle)

    language, epi, drug_name = process_bundle(bundle.json())
    # GET https://fosps.gravitatehealth.eu/ips/api/fhir/Patient/$summary?identifier=alicia-1
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
            language, drug_name, gender, age, diagnostics, medications
        )
    # Return the JSON response
    print(response)
    return jsonify(response.choices[0].message.content)
