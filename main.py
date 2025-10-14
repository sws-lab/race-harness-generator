import sys
from race_harness.parser import RHParser
from race_harness.ir import RHContext

def main():
    parser = RHParser()
    context = RHContext()
    with open(sys.argv[1]) as input_file:
        module = parser.parse(input_file.read(), context)
    print(context)

if __name__ == "__main__":
    main()
