import requests #run [python -m pip install requests] for this to work
from requests.auth import HTTPDigestAuth
import json

conditions = ['blinded', 'charmed', 'deafened', 'exhaustion', 'frightened', 'grappled', 'incapacitated', 'invisible', 'paralyzed', 'petrified', 'poisoned', 'prone', 'restrained', 'stunned', 'unconscious']
classes = []

#https://docs.dnd5eapi.co/api/2014 and https://docs.dnd5eapi.co/api/2024 <-- api documentation
url = "https://www.dnd5eapi.co/api/2024/" #api base url
data = '{"query"}'

append = "spells"


payload = {}
headers = {
  'Accept': 'application/json'
}


response = requests.request("GET", url+append, headers=headers, data=payload) #queries the api. "conditions/blinded gives the output for the blinded condition"


dict = json.loads(response.text) #splits json output into a dictinoary 
#print(dict) 
spell_list = []
for result in dict["results"]:
    spell_list.append(result["index"])

    
#print(dict["results"][0]["index"])
print(spell_list)

#for i in range(0,1):
#    spell_name = dict["results"][i]["index"]
#    append=f"spells/{spell_name}"
#    response = requests.request("GET", url+append, headers=headers, data=payload) #queries the api. "conditions/blinded gives the output for the blinded condition"
#    dict2 = json.loads(response.text)
#    print(f"{dict2["name"]} —— lvl {dict2["level"]}")
#    print("-----")
#    print(f"Range: {dict2["range"]} —— Duration: {dict2["duration"]}")
#    print(f"Materials: {dict2["material"].capitalize()}")
#    print(f"{dict2["description"].strip().replace("\n  ", " ")}")
#    print("========================")