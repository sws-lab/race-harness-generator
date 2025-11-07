#!/usr/bin/env -S uv run
import sys
import os
import enum
import argparse
import pathlib
import io
import tempfile
import subprocess
import csv
from typing import Optional, Iterable
from race_harness.parser import RHParser
from race_harness.ir import RHContext
from race_harness.ir.mutex import RHMutualExclusion, RHMutualInclusion
from race_harness.ir.transform import optimize_module_control_flow
from race_harness.stir import STModule, STNodeID
from race_harness.stir.translator import RHSTTranslator
from race_harness.stir.serialize import STSerialize
from race_harness.control_flow import CFConstructor
from race_harness.codegen.goblint import GoblintLBECodegen
from race_harness.codegen.executable import ExecutableLBECodegen
from race_harness.codegen.header import HeaderCodegen
from race_harness.codegen.state_transition import ExecutableStirCodegen

class RaceHarnessEncoding(enum.Enum):
    Executable = 'executable'
    Goblint = 'goblint'
    GoblintKernel = 'goblint-kernel'
    Header = 'header'
    Rhir = 'rhir'
    Stir = 'stir'
    StateSpace = 'state_space'
    ExecutableStir = 'executable-stir'

class RaceHarnessDriver:
    def __init__(self, *, ltsmin: Optional[pathlib.Path], pins_stir: Optional[pathlib.Path], quiet: bool = False):
        self._ltsmin = ltsmin
        self._pins_stir = pins_stir
        self._quiet = quiet
        self._parser = RHParser()

    def run(self, model: io.TextIOBase, *, output: io.TextIOBase, encoding: RaceHarnessEncoding, embed_header: bool = False, state_space: Optional[pathlib.Path]):
        rh_context = RHContext()
        rh_module = self._parser.parse(model.read(), rh_context)
        optimize_module_control_flow(rh_context, rh_module)

        if encoding == RaceHarnessEncoding.Rhir:
            print(rh_context, file=output)
        else:
            st_module = STModule()
            rhst_translator = RHSTTranslator(rh_context, st_module)
            rhst_translator.translate_module(rh_module)

            if encoding == RaceHarnessEncoding.Stir:
                serializer = STSerialize(output)
                serializer.serialize_module(st_module)
            elif encoding == RaceHarnessEncoding.ExecutableStir:
                codegen = ExecutableStirCodegen(output)
                codegen.codegen_module(st_module)
            elif encoding == RaceHarnessEncoding.StateSpace:
                for line in self._model_check(st_module):
                    output.write(line)
            else:
                mutinc = RHMutualInclusion()
                mutex = RHMutualExclusion(rh_context, mutinc)
                def process_csv_line(line):
                    st_node1 = STNodeID(int(line[1]))
                    st_node2 = STNodeID(int(line[3]))
                    instance_block1_ref = rhst_translator.mapping.get_mapping(st_node1)
                    instance_block2_ref = rhst_translator.mapping.get_mapping(st_node2)
                    if instance_block1_ref and instance_block2_ref:
                        mutinc.add_cooccuring_states(*instance_block1_ref, *instance_block2_ref)

                if state_space is None:
                    for line in self._model_check(st_module):
                        for line in csv.reader((line,)):
                            process_csv_line(line)
                else:
                    with open(state_space) as state_space_file:
                        for line in csv.reader(state_space_file):
                            process_csv_line(line)

                cf_constructor = CFConstructor(rh_context, mutex)
                cf_module = cf_constructor.construct_module(rh_module)
                
                if embed_header and encoding != RaceHarnessEncoding.Header:
                    codegen = HeaderCodegen(output)
                    codegen.codegen_module(cf_module)

                if encoding == RaceHarnessEncoding.Executable:
                    codegen = ExecutableLBECodegen(output)
                elif encoding == RaceHarnessEncoding.Goblint:
                    codegen = GoblintLBECodegen(output, userspace=True)
                elif encoding == RaceHarnessEncoding.GoblintKernel:
                    codegen = GoblintLBECodegen(output, userspace=False)
                elif encoding == RaceHarnessEncoding.Header:
                    codegen = HeaderCodegen(output)
                else:
                    raise RuntimeError(f'Unexpected encoding: {encoding.value}')
                codegen.codegen_module(cf_module)

    def _model_check(self, st_module: STModule) -> Iterable[str]:
        if self._ltsmin is None:
            raise RuntimeError('Expected LTSmin installation directory to be provided for C code generation')
        if self._pins_stir is None:
            raise RuntimeError('Expected PINS-STIR plugin directory to be provided for C code generation')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            stir_filepath = pathlib.Path(tmpdir) / 'module.stir'
            state_space_bin_filepath = pathlib.Path(tmpdir) / 'state_space.bin'
            state_space_csv_filepath = pathlib.Path(tmpdir) / 'state_space.csv'
            with open(stir_filepath, 'w') as stir_file:
                serializer = STSerialize(stir_file)
                serializer.serialize_module(st_module)

            pins2lts_seq_filepath = str((self._ltsmin / 'bin/pins2lts-seq').resolve())
            libpins_stir_filepath = str((self._pins_stir / 'libpins-stir.so').resolve())
            stir_bin_export_filepath = str((self._pins_stir / 'stir-bin-export').resolve())
            pins2lts_seq_proc = subprocess.Popen(
                args=[
                    pins2lts_seq_filepath,
                    libpins_stir_filepath
                ],
                executable=pins2lts_seq_filepath,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL if self._quiet else sys.stderr,
                stderr=subprocess.DEVNULL if self._quiet else sys.stderr,
                shell=False,
                env={
                    **os.environ,
                    'PINS_STIR_MODEL': str(stir_filepath),
                    'PINS_STIR_OUTPUT': str(state_space_bin_filepath)
                }
            )
            pins2lts_seq_proc.wait()

            with open(state_space_csv_filepath, 'w') as state_space_csv_file:
                stir_bin_export = subprocess.Popen(
                    args=[
                        stir_bin_export_filepath,
                        stir_filepath,
                        str(state_space_bin_filepath)
                    ],
                    executable=stir_bin_export_filepath,
                    stdout=state_space_csv_file,
                    shell=False
                )
                stir_bin_export.wait()

            with open(state_space_csv_filepath) as state_space_file:
                yield from state_space_file

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(prog=sys.argv[0], description='Race harness generator')
    argparser.add_argument('--ltsmin', type=str, required=False, help='LTSmin installation directory')
    argparser.add_argument('--pins-stir', type=str, required=False, help='PINS-STIR plugin directory')
    argparser.add_argument('--encoding', type=str, default=RaceHarnessEncoding.Executable.value, choices=[enc.value for enc in RaceHarnessEncoding], help='Generated race harness encoding')
    argparser.add_argument('--embed-header', default=False, action='store_true', help='Embed header into the generated harness')
    argparser.add_argument('--state-space', type=str, required=False, help='Precomputed state space CSV file')
    argparser.add_argument('--output', type=str, default=None, required=False, help='Output file')
    argparser.add_argument('--quiet', default=False, action='store_true', help='Suppress tool output')
    argparser.add_argument('model', type=str, help='Race harness model')
    args = argparser.parse_args(sys.argv[1:])
    
    driver = RaceHarnessDriver(
        ltsmin=pathlib.Path(args.ltsmin) if args.ltsmin else None,
        pins_stir=pathlib.Path(args.pins_stir) if args.pins_stir else None,
        quiet=args.quiet
    )
    with open(args.model) as model_file:
        output = sys.stdout
        try:
            if args.output:
                output = open(args.output, 'w')
            driver.run(
                model_file,
                output=output,
                encoding=RaceHarnessEncoding(args.encoding),
                embed_header=args.embed_header,
                state_space=pathlib.Path(args.state_space) if args.state_space else None
            )
        finally:
            if output != sys.stdout:
                output.close()
