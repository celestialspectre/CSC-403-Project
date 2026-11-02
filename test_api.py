import requests #run [python -m pip install requests] for this to work
from requests.auth import HTTPDigestAuth
import json

conditions = ['blinded', 'charmed', 'deafened', 'exhaustion', 'frightened', 'grappled', 'incapacitated', 'invisible', 'paralyzed', 'petrified', 'poisoned', 'prone', 'restrained', 'stunned', 'unconscious']

#https://docs.dnd5eapi.co/api/2014 and https://docs.dnd5eapi.co/api/2024 <-- api documentation
url = "https://www.dnd5eapi.co/api/2024/" #api base url
data = '{"query"}'

append = "conditions/blinded"


payload = {}
headers = {
  'Accept': 'application/json'
}


response = requests.request("GET", url+append, headers=headers, data=payload) #queries the api. "conditions/blinded gives the output for the blinded condition"


dict = json.loads(response.text) #splits json output into a dictinoary 
print(dict)



"""
cond = input("break this: ")
condList = cond.split(", ")
print(condList)
"""