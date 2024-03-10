class Query(object):
    def __init__(self, inst, arg=None):
        self.inst = inst
        self.arg = arg


class Response(object):
    def __init__(self, inst, res, data=None):
        self.inst = inst
        self.result = res
        self.data = data
