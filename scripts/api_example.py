import requests
from kestra import Kestra

r = requests.get("https://api.github.com/repos/kestra-io/kestra")
gh_stars = r.json()['stargazers_count']
Kestra.outputs({'gh_stars': gh_stars})