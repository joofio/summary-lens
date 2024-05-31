import requests

PAT = ["Cecilia-1", "Pedro-1", "alicia-1"]
PAT = ["alicia-1"]

EPI = [
    "bundlepackageleaflet-es-29436a85dac3ea374adb3fa64cfd2578",  # HIPÉRICO ARKOPHARMA
    "bundlepackageleaflet-es-94a96e39cfdcd8b378d12dd4063065f9",  # biktarvy
    "bundlepackageleaflet-es-04c9bd6fb89d38b2d83eced2460c4dc1",  # flucelvax
    "bundlepackageleaflet-es-925dad38f0afbba36223a82b3a766438",  # calcio
    "bundlepackageleaflet-es-4fab126d28f65a1084e7b50a23200363",  # xenical
    "bundlepackageleaflet-es-2f37d696067eeb6daf1111cfc3272672",  # tegretrol
]
# HOST = "http://localhost:5005/summary/"
HOST = "http://gravitate-health.lst.tfo.upm.es/ai/summary/"
for p in PAT:
    for e in EPI:
        myreq = (
            HOST
            + e
            + "?preprocessors=preprocessing-service-manual&patientIdentifier="
            + p
            + "&lenses=lens-summary-2&model=graviting-llama"
        )
        print(myreq)
        response = requests.get(myreq)
        print("Pat", p, "ePI", e, response.status_code)
        print(response.json())
    # if response.status_code == 500:
    # print(response.status_code)

# GET http://localhost:5005/focusing/focus/
# bundlepackageleaflet-es-56a32a5ee239fc834b47c10db1faa3fd
# ?preprocessors=preprocessing-service-manual&patientIdentifier=Cecilia-1
# &lenses=lens-summary-2&model=gpt-4
