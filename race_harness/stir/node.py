class STNodeID:
    def __init__(self, node_id: int):
        self._node_id = node_id

    @property
    def node_id(self) -> int:
        return self._node_id
    
    def __eq__(self, value):
        return isinstance(value, STNodeID) and self.node_id == value.node_id
    
    def __hash__(self):
        return hash(self.node_id)
    
    def __str__(self):
        return f'&{self.node_id}'