import requests
from kestra import Kestra

r = requests.get("https://api.github.com/repos/kestra-io/kestra")
output = r.json()['stargazers_count']
Kestra.outputs({'output': output})