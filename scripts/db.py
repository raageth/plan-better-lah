from algo.db import DBClient

if __name__ == '__main__':
    client = DBClient()
    client.refresh_module_info()