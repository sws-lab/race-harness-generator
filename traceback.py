import sys
import struct
import os
import dataclasses
from typing import List, Dict

@dataclasses.dataclass
class Chunk:
    content: List[int]

    def __hash__(self):
        res = 0
        for elt in self.content:
            res = 31 * res + elt
        return res
    
    def __eq__(self, value):
        if not isinstance(value, Chunk):
            return False
        if len(self.content) != len(value.content):
            return False
        
        for elt, other_elt in zip(self.content, value.content):
            if elt != other_elt:
                return False
        return True
    
    @staticmethod
    def read(input, size):
        chunk = list()
        for _ in range(size):
            chunk.append(struct.unpack('i', input.read(4))[0])
        return Chunk(content=chunk)
    
def traverse(preds: Dict[Chunk, Chunk], target: Chunk, source: Chunk):
    queue = [
        [target, pred]
        for pred in preds.get(target, ())
    ]
    while queue:
        chain = queue.pop()
        if chain[-1] == source:
            return chain
        
        print(len(queue), chain)
        
        for pred in preds.get(chain[-1], ()):
            if pred not in chain:
                if pred == source:
                    return [*chain, pred]
                queue.insert(0, [*chain, pred])

if __name__ == '__main__':
    filepath = sys.argv[1]
    state_length = int(sys.argv[2])
    init = None
    look_for = None
    preds = dict()
    with open(filepath, 'rb') as bin_input:
        for i in range(os.path.getsize(filepath) // (state_length * 4) // 2):
            pred = Chunk.read(bin_input, state_length)
            succ = Chunk.read(bin_input, state_length)
            def assign_pred_chain(chain):
                if succ not in preds or len(preds[succ]) > len(chain):
                    preds[succ] = chain
            if init is None:
                init = pred
                assign_pred_chain([init, succ])
            else:
                assign_pred_chain([*preds[pred], succ])

            if succ.content[0] == 14 and succ.content[1] == 21:
                look_for = succ

    for idx, elt in enumerate(preds[look_for]):
        print(idx, elt)