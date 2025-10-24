import sys
from race_harness.parser import RHParser
from race_harness.ir import RHContext
from race_harness.ir.transform import optimize_module_control_flow
from race_harness.stir import STModule
from race_harness.stir.translator import RHSTTranslator
from race_harness.stir.serialize import STSerialize

def main():
    parser = RHParser()
    context = RHContext()
    with open(sys.argv[1]) as input_file:
        module = parser.parse(input_file.read(), context)
    optimize_module_control_flow(context, module)
    st_module = STModule()
    rhst_translator = RHSTTranslator(context, st_module)
    rhst_translator.translate_module(module)
    serializer = STSerialize(sys.stdout)
    serializer.serialize_module(st_module)

if __name__ == "__main__":
    main()
