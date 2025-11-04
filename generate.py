import sys
import csv
import argparse
import enum
from race_harness.parser import RHParser
from race_harness.ir import RHContext
from race_harness.ir.transform import optimize_module_control_flow
from race_harness.ir.mutex import RHMutualInclusion, RHMutualExclusion
from race_harness.stir import STModule, STNodeID
from race_harness.stir.translator import RHSTTranslator
from race_harness.control_flow import CFConstructor
from race_harness.codegen.goblint import GoblintLBECodegen
from race_harness.codegen.executable import ExecutableLBECodegen
from race_harness.codegen.header import HeaderCodegen

class Encoding(enum.Enum):
    Executable = 'executable'
    Goblint = 'goblint'
    Header = 'header'

def main():
    argparser = argparse.ArgumentParser(sys.argv[0], description='Encoding generator for race harnesses')
    argparser.add_argument('--reachability', type=str, required=True, help='Pairwise reachability CSV')
    argparser.add_argument('--encoding', type=Encoding, default=Encoding.Executable, choices=list(Encoding), help='Target encoding')
    argparser.add_argument('rh_file')

    args = argparser.parse_args(sys.argv[1:])

    parser = RHParser()
    context = RHContext()
    with open(args.rh_file) as input_file:
        module = parser.parse(input_file.read(), context)
    optimize_module_control_flow(context, module)
    st_module = STModule()
    rhst_translator = RHSTTranslator(context, st_module)
    rhst_translator.translate_module(module)

    mutinc = RHMutualInclusion()
    mutex = RHMutualExclusion(context, mutinc)
    with open(args.reachability) as state_space_file:
        for entry in csv.reader(state_space_file):
            node1_id = STNodeID(int(entry[1]))
            node2_id = STNodeID(int(entry[3]))

            instance_block1_ref = rhst_translator.mapping.get_mapping(node1_id)
            instance_block2_ref = rhst_translator.mapping.get_mapping(node2_id)
            if instance_block1_ref and instance_block2_ref:
                mutinc.add_cooccuring_states(*instance_block1_ref, *instance_block2_ref)

    cf_constructor = CFConstructor(context, mutex)
    cf_module = cf_constructor.construct_module(module)

    if args.encoding == Encoding.Executable:
        codegen = ExecutableLBECodegen(sys.stdout)
    elif args.encoding == Encoding.Goblint:
        codegen = GoblintLBECodegen(sys.stdout)
    elif args.encoding == Encoding.Header:
        codegen = HeaderCodegen(sys.stdout)

    codegen.codegen_module(cf_module)

if __name__ == "__main__":
    main()
