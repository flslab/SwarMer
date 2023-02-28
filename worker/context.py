class WorkerContext:
    def __init__(self, count, fid, gtl, el):
        self.count = count
        self.fid = fid
        self.gtl = gtl
        self.el = el
        self.swarm_id = self.fid
        self.neighbors_id = []
        self.radio_range = 100
        self.size = 1
        self.anchor = None
        self.query_id = None

    def set_swarm_id(self, swarm_id):
        self.swarm_id = swarm_id

    def set_el(self, el):
        self.el = el

    def set_query_id(self, query_id):
        self.query_id = query_id

    def set_anchor(self, anchor):
        self.anchor = anchor

    def move(self, vector):
        self.set_el(self.el + vector)
