import requests

r = requests.get("https://api.github.com/repos/kestra-io/kestra")
output = r.json()['stargazers_count']
print(output)