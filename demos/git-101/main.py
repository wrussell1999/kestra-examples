import requests

r = requests.get('https://api.github.com/repos/kestra-io/kestra')
gh_stars = r.json()['stargazers_count']
print(gh_stars)
