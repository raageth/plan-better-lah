import requests
from collections import defaultdict

acad_year = "2023-2024"
url = f"https://api.nusmods.com/v2/{acad_year}/modules/CS2030S.json"

def main():
    # get modules
    modules = requests.get(url).json()
    data = modules['semesterData']
    info = defaultdict(defaultdict(list))
    for sem in data:
        pass
        # info[sem['semester']] = 
        # info[i['lessonType']].append(i)
    print(info)

if __name__ == "__main__":
    main()