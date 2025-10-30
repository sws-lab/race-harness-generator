class RHRef:
    def __init__(self, uid: int, context: 'RHContext'):
        self._uid = uid
        self._top_level_context = context

    @property
    def uid(self) -> int:
        return self._uid
    
    @property
    def top_level_context(self) -> 'RHContext':
        return self._top_level_context
    
    def __hash__(self):
        return hash(self._uid)
    
    def __eq__(self, value):
        return isinstance(value, RHRef) and self.uid == value.uid
    
    def __lt__(self, value):
        if isinstance(value, RHRef):
            return True if self.uid < value.uid else False
        else:
            return True
    
    def __str__(self):
        return f'%{self.uid}'
    
    def __repr__(self):
        return str(self)
