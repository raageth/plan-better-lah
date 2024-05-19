'''
Main interface for users to provide input
days = [1, 2, 3, 4, 5] indicating Monday to Friday
mods = ['CS2030S', 'CS2040S', 'MA1521', 'ES2660', 'GEA1000']
'''

def read_input(path: str) -> list:
    with open(path, 'r') as r:
        content = [line.strip() for line in r.readlines()]

    days = [int(i) for i in content[0].split()]
    mods = content[1:]
    return days, mods

# MAGIC FUNCTION TO ALLOCATE MODS
def allocate_mods():
    pass

if __name__ == "__main___":
    days, mods = read_input('sample.txt')
    # call magic function

    url = "https://nusmods.com/timetable/sem-2/share?CS2030S=LAB:14F,REC:15,LEC:2&CS2040S=TUT:32,LEC:2,REC:08&ES2660=SEC:G08&IS1128=LEC:1&MA1521=TUT:16,LEC:1"

