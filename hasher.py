class CuckooBird:
    def __init__(self, size):
        self.size = size
        self.table1 = [None] * size
        self.table2 = [None] * size

    def hash_function1(self, key):
        return hash(key) % self.size

    def hash_function2(self, key):
        return (hash(key) // self.size) % self.size

    def insert(self, key):
        if self.search(key):
            return

        for _ in range(self.size):
            index1 = self.hash_function1(key)
            if self.table1[index1] is None:
                self.table1[index1] = key
                return

            key, self.table1[index1] = self.table1[index1], key
            index2 = self.hash_function2(key)
            if self.table2[index2] is None:
                self.table2[index2] = key
                return

            key, self.table2[index2] = self.table2[index2], key

        # If the loop completes without finding an empty slot, rehash and try again
        self.rehash()
        self.insert(key)

    def search(self, key):
        index1 = self.hash_function1(key)
        index2 = self.hash_function2(key)
        return self.table1[index1] == key or self.table2[index2] == key

    def rehash(self):
        new_size = self.size * 2
        new_table1 = [None] * new_size
        new_table2 = [None] * new_size

        for key in self.table1 + self.table2:
            if key is not None:
                index1 = hash(key) % new_size
                if new_table1[index1] is None:
                    new_table1[index1] = key
                    continue

                key, new_table1[index1] = new_table1[index1], key
                index2 = (hash(key) // new_size) % new_size
                if new_table2[index2] is None:
                    new_table2[index2] = key
                    continue

                key, new_table2[index2] = new_table2[index2], key

        self.size = new_size
        self.table1 = new_table1
        self.table2 = new_table2
