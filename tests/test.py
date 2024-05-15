import requests


PAT = ["Cecilia-1", "Pedro-1", "alicia-1"]

EPI = [
    "bundlepackageleaflet-es-29436a85dac3ea374adb3fa64cfd2578",
    "bundlepackageleaflet-es-94a96e39cfdcd8b378d12dd4063065f9",
]
HOST = "http://localhost:5005/summary/"
# HOST = "http://gravitate-health.lst.tfo.upm.es/ai/summary/"
for p in PAT:
    for e in EPI:
        response = requests.get(
            HOST
            + e
            + "?preprocessors=preprocessing-service-manual&patientIdentifier="
            + p
            + "&lenses=lens-summary-2&model=mistral"
        )
        print("Pat", p, "ePI", e, response.status_code)
    # if response.status_code == 500:
    # print(response.status_code)

# GET http://localhost:5005/focusing/focus/
# bundlepackageleaflet-es-56a32a5ee239fc834b47c10db1faa3fd
# ?preprocessors=preprocessing-service-manual&patientIdentifier=Cecilia-1
# &lenses=lens-summary-2&model=gpt-4
