import requests

acad_year = "2023-2024"
url = f"https://api.nusmods.com/v2/{acad_year}"

def main():
    # get modules
    modules = requests.get(url + "/moduleList.json").json()
    print(modules[0]['moduleCode'])

if __name__ == "__main__":
    main()