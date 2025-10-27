import sys
import csv
from race_harness.parser import RHParser
from race_harness.ir import RHContext
from race_harness.ir.transform import optimize_module_control_flow
from race_harness.stir import STModule, STNodeID
from race_harness.stir.translator import RHSTTranslator

def main():
    parser = RHParser()
    context = RHContext()
    with open(sys.argv[1]) as input_file:
        module = parser.parse(input_file.read(), context)
    optimize_module_control_flow(context, module)
    st_module = STModule()
    rhst_translator = RHSTTranslator(context, st_module)
    rhst_translator.translate_module(module)

    with open(sys.argv[2]) as state_space_file:
        for entry in csv.reader(state_space_file):
            node1_id = STNodeID(int(entry[1]))
            node2_id = STNodeID(int(entry[3]))

            block1_ref = rhst_translator.mapping.get_mapping(node1_id)
            block2_ref = rhst_translator.mapping.get_mapping(node2_id)
            if block1_ref and block2_ref:
                print(block1_ref, block2_ref)

    print(context)
    print(st_module)

if __name__ == "__main__":
    main()
