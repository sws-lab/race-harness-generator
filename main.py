import sys
from race_harness.parser import RHParser
from race_harness.ir import RHContext
from race_harness.ir.transform import optimize_module_control_flow

def main():
    parser = RHParser()
    context = RHContext()
    with open(sys.argv[1]) as input_file:
        module = parser.parse(input_file.read(), context)
        optimize_module_control_flow(context, module)
    print(context)

if __name__ == "__main__":
    main()
