import pandas as pd
import requests
import hashlib
import time
from datetime import datetime, timedelta
import json
import os


# path
path = "C:/Users/XXXXXX/Doc/"

# === Configuration ===
client_id = "XXX"
api_key = "XXX"
owner = "XXX"
server_domain = 'app2.salesmanago.com'

# === Time Range ===
yesterday = int((datetime.now() - timedelta(days=1)).timestamp() * 1000)
now = int(datetime.now().timestamp() * 1000)
request_time = int(time.time() * 1000)
sha_value = "XXX"

# === Timestamp for filenames ===
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

# === Payloads for API requests ===
base_payload = {
    "clientId": client_id,
    "apiKey": api_key,
    "requestTime": request_time,
    "sha": sha_value,
    "owner": owner,
    "from": yesterday,
    "to": now
}

# === Fetch created and modified contacts ===
def fetch_contacts(endpoint):
    url = f'https://{server_domain}/api/contact/{endpoint}'
    response = requests.post(url, json=base_payload)
    if response.status_code == 200:
        return response.json().get(endpoint, [])
    else:
        print(f"Error fetching {endpoint}: {response.status_code} - {response.text}")
        return []

created_contacts = fetch_contacts("createdContacts")
modified_contacts = fetch_contacts("modifiedContacts")
all_contacts = created_contacts + modified_contacts
id_list = [contact['id'] for contact in all_contacts][:5]  # Limit to 5 for testing

# === Fetch full contact details ===
output_data = []
for contact_id in id_list:
    payload = base_payload.copy()
    payload["contactId"] = [contact_id]
    url = f'https://{server_domain}/api/contact/listById'
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        output_data.append(response.json())
    else:
        print(f"Error fetching contact {contact_id}: {response.status_code} - {response.text}")

# === Load tag-to-preference mapping ===
mapping_df = pd.read_excel(path + 'Transformed_TAGs_Preference_Center_Mapping (1).xlsx', sheet_name='Sheet1')
conversion_dict = dict(zip(mapping_df['Tags'], mapping_df['Preferences']))

# === Extract and convert contact data ===
extracted_data = []
tag_changes_log = []

for contact in output_data:
    for info in contact.get('contacts', []):
        original_tags = [tag['tag'] for tag in info.get('contactTags', [])]
        converted_tags = [
            {"tag": conversion_dict[tag['tag']], "score": tag['score']}
            for tag in info.get('contactTags', [])
            if tag['tag'] in conversion_dict
        ]
        extracted_data.append({
            "name": info.get('name'),
            "email": info.get('email'),
            "id": info.get('id'),
            "company": info.get('company'),
            "original_tags": original_tags,
            "converted_tags": converted_tags
        })
        if converted_tags:
            tag_changes_log.append({
                "email": info.get('email'),
                "original_tags": original_tags,
                "converted_tags": [tag['tag'] for tag in converted_tags]
            })

# === Save extracted data and tag changes ===
with open(f'/extracted_contacts_{timestamp}.txt', 'w', encoding='utf-8') as f:
    json.dump(extracted_data, f, indent=4)

with open(f'tag_changes_log_{timestamp}.json', 'w', encoding='utf-8') as f:
    json.dump(tag_changes_log, f, indent=4)

print(f"Saved: extracted_contacts_{timestamp}.txt and tag_changes_log_{timestamp}.json")

# === Load preference ID mapping ===
pref_df = pd.read_excel(path + 'PLPreferencesMapping 1 1.xlsx", engine='openpyxl')
preferences_dict = {
    row['custompreference']: {
        "purposeId": row['Purposeid'],
        "preferenceId": row['preferenceid'],
        "customPreferenceId": row['custompreferenceID']
    }
    for _, row in pref_df.iterrows()
}

# === Generate final JSON structure ===
contacts_json = []
for contact in extracted_data:
    name = contact.get("name", "")
    first_name = name.split()[0] if name else ""
    last_name = name.split()[-1] if name and len(name.split()) > 1 else ""
    purposes = []
    for tag in contact.get("converted_tags", []):
        tag_info = preferences_dict.get(tag["tag"])
        if tag_info:
            transaction_type = "OPT_IN" if tag["score"] == 1 else "OPT_OUT"
            purposes.append({
                "Id": tag_info["purposeId"],
                "TransactionType": "CHANGE_PREFERENCES",
                "CustomPreferences": [{
                    "Id": tag_info["preferenceId"],
                    "Choices": [{
                        "OptionId": tag_info["customPreferenceId"],
                        "TransactionType": transaction_type
                    }]
                }]
            })
    if purposes:
        contacts_json.append({
            "identifier": contact["email"],
            "identifierType": "Email",
            "dsDataElements": {
                "FirstName": first_name,
                "LastName": last_name,
                "CompanyName": contact.get("company", "")
            },
            "purposes": purposes
        })

# === Save final JSON ===
with open(f"/contacts_with_preferences_full_{timestamp}.json", "w", encoding="utf-8") as f:
    json.dump(contacts_json, f, indent=4, ensure_ascii=False)

print(f"Saved: contacts_with_preferences_full_{timestamp}.json")
