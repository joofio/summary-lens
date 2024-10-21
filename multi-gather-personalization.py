import requests


epis = {
    "xenical": "bundlepackageleaflet-en-4fab126d28f65a1084e7b50a23200363",
    "humalog": "bundlepackageleaflet-en-a38f06714db0c27b2ba704652e3f08c5",
    "biktarvy": "bundlepackageleaflet-en-94a96e39cfdcd8b378d12dd4063065f9",
    "karvea": "bundlepackageleaflet-en-dcaa4d32aa6658a8df831551503e52ee",
}

models = [
    "mistral",
    "llama3",
    "llama3.1",
    "llama-3.1-70b-Versatile",
    "Mixtral-8x7b-32768",
    "Llama3-70b-8192",
    "Llama3-8b-8192",
    "Llama-3.2-90b-Text-Preview",
]

for k, v in epis.items():
    for model in models:
        headers = {
            "Content-Type": "application/json"  # or the desired content type
        }
        response = requests.get(
            "http://localhost:5005/summary/"
            + v
            + "?preprocessors=preprocessing-service-manual&lenses=lens-summary-2&model="
            + model,
            headers=headers,
        )

        if response.status_code == 200:
            # Write response content to a file
            with open("response-" + model + "-" + k + ".html", "w") as file:
                file.write(response.json()["section"][0]["text"]["div"])
            print("Response written to response.json")
        else:
            print("Error:", response.status_code, response.text)
