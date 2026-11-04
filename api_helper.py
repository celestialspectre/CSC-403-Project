import requests #run [python -m pip install requests] for this to work
from requests.auth import HTTPDigestAuth
import json

#https://docs.dnd5eapi.co/api/2014 and https://docs.dnd5eapi.co/api/2024 <-- api documentation


#This isolates each description into each bullet point and returns a list of the points
def parse_description(desc:str):
  aList = desc.split("\n")
  for i in range(len(aList)):
    aCount = 0
    for j in range(len(aList[i])):
      if aList[i][j:].count("*") == 0:
        aList[i] = aList[i][j:].strip()
        break
  return aList[1:]