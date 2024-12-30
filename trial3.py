class alist(list):
    def __init__(cls, *args):
        if len(args) == 1:
            return super().__init__(*args)
        else:
            return super().__init__(args)
    def __eq__(self, value):
        if not isinstance(value, list):
            return None
        elif len(self) != len(value):
            return None
        else:
            for i in range(len(self)):
                if self[i] != value[i]:
                    return False
            return True

class atuple(tuple):
    def __new__(cls, *args):
        if len(args) == 1 and isinstance(args[0], list):
            return super().__new__(cls, *args)
        else:
            return super().__new__(cls, args)

d = {tuple([1,2,3]):3}
print(d[atuple(1,2,3)])