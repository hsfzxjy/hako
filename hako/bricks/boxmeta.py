class BoxBaseMeta(type):
    def __truediv__(self, rhs):
        return self[None] / rhs

    def __rtruediv__(self, lhs):
        return lhs / self[None]

    def __sub__(self, rhs):
        return self[None] - rhs

    def __rsub__(self, lhs):
        return lhs - self[None]
