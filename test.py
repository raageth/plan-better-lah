import requests

acad_year = "2023-2024"
url = f"https://api.nusmods.com/v2/{acad_year}/modules/CS2030S.json"

def main():
    # get modules
    modules = requests.get(url).json()
    print(modules['semesterData'])

if __name__ == "__main__":
    main()