class Query(object):
    """ Query protocol definition """
    def __init__(self, inst, arg=None):
        self.inst = inst
        self.arg = arg


class Response(object):
    """ Response protocol definition """
    def __init__(self, inst, res, data=None):
        self.inst = inst
        self.result = res
        self.data = data
