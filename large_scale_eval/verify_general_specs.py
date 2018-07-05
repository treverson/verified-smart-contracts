from os import path
from os import listdir
from os.path import isfile, join
from subprocess import Popen, PIPE
import os
import json
from multiprocessing import Pool
import threading
import time


class Argument(object):
    def __init__(self, name, spec_type, spec_name, spec_path):
        self.name = name
        self.spec_type = spec_type
        self.spec_name = spec_name
        self.spec_path = spec_path


contracts_path = '/home/iustines/Workspace/general-specs/general_specs/contracts'
solidity_path = '/home/iustines/Solidity/{}/build/solc/solc'
kevm_path = '/home/iustines/Workspace/general-specs'
krpove = '/home/iustines/Workspace/new/kevm'
solidity_version = 'v0.4.16'
specs_path = '/home/iustines/Workspace/general-specs/tests/proofs'
erc20proofscpy = '/home/iustines/Workspace/general-specs/tests/proofs/erc20_cpy'
erc20proofs = '/home/iustines/Workspace/general-specs/tests/proofs/erc20'
specs_folders = ['ds-token', 'hobby', 'zeppelin', 'vyper']

erc20_specs_path = '/home/iustines/Workspace/general-specs/tests/proofs/specs/vyper-erc20'
erc20_files = ['totalSupply-spec.k', 'balanceOf-spec.k', 'allowance-spec.k', 'approve-spec.k', 'transfer-success-1-spec.k', 'transfer-success-2-spec.k', 'transfer-failure-1-spec.k',
             'transfer-failure-2-spec.k', 'transferFrom-success-1-spec.k', 'transferFrom-success-2-spec.k', 'transferFrom-failure-2-spec.k', 'transferFrom-failure-1-spec.k']
zeppelin_specs_path = '/home/iustines/Workspace/general-specs/tests/proofs/specs/zeppelin-erc20'
zeppelin_erc20_files = ['totalSupply-spec.k', 'balanceOf-spec.k', 'allowance-spec.k', 'approve-spec.k', 'transfer-success-1-spec.k',
                        'transfer-success-2-spec.k', 'transfer-failure-1-a-spec.k', 'transfer-failure-1-b-spec.k', 'transfer-failure-2-spec.k',
                        'transferFrom-success-1-spec.k', 'transferFrom-success-2-spec.k', 'transferFrom-failure-1-a-spec.k', 'transferFrom-failure-1-b-spec.k', 'transferFrom-failure-2-spec.k']
hobby_specs_path = '/home/iustines/Workspace/general-specs/tests/proofs/specs/hobby-erc20'
hobby_erc20_files = ['totalSupply-spec.k', 'balanceOf-spec.k', 'allowance-spec.k', 'approve-success-spec.k', 'approve-failure-spec.k',
                     'transfer-success-1-spec.k', 'transfer-success-2-spec.k', 'transfer-failure-1-spec.k', 'transfer-failure-2-spec.k',
                     'transferFrom-success-1-spec.k', 'transferFrom-success-2-spec.k', 'transferFrom-failure-1-spec.k', 'transferFrom-failure-2-spec.k']
ds_token_specs_path = '/home/iustines/Workspace/general-specs/tests/proofs/specs/ds-token-erc20'
ds_token_erc20_files = ['totalSupply-spec.k', 'balanceOf-spec.k', 'allowance-spec.k', 'approve-success-spec.k', 'approve-failure-spec.k',
                        'transfer-success-1-spec.k', 'transfer-success-2-spec.k', 'transfer-failure-1-a-spec.k', 'transfer-failure-1-b-spec.k ',
                        'transfer-failure-1-c-spec.k', 'transfer-failure-2-a-spec.k', 'transfer-failure-2-b-spec.k', 'transferFrom-success-1-spec.k',
                        'transferFrom-success-2-spec.k', 'transferFrom-failure-1-a-spec.k', 'transferFrom-failure-1-b-spec.k', 'transferFrom-failure-1-c-spec.k',
                        'transferFrom-failure-1-d-spec.k', 'transferFrom-failure-2-a-spec.k', 'transferFrom-failure-2-b-spec.k', 'transferFrom-failure-2-c-spec.k']

kprove = '/home/iustines/Workspace/general-specs/.build/k/k-distribution/bin/kprove'
java_build = '/home/iustines/Workspace/general-specs/.build/java'

g = open("result.csv", "w+")
g.write("ContractName, SpecType, Spec, Proved \n")
g.close()

def prove(spec_arg):
    print(spec_arg.spec_path)
    start = time.time()
    p = Popen([krpove, 'prove', spec_arg.spec_path], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate("")
    rc = p.returncode
    print(str(rc) + "    " + str(output) + "    " + str(err))
    f = open("result.csv", "a+")
    if rc == 0:
        f.write("{0}, {1}, {2}, {3} \n".format(spec_arg.name, spec_arg.spec_type, spec_arg.spec_name, "True"))
    else:
        f.write("{0}, {1}, {2}, {3} \n".format(spec_arg.name, spec_arg.spec_type, spec_arg.spec_name, str(err)))
    f.close()
    p.kill()
    print(spec_arg.spec_name + str( time.time() - start))


def generate_proofs(text):
    cwd = os.getcwd()
    os.system("rm -rf {}".format(erc20proofs))
    os.system("cp -R {0} {1}".format(erc20proofscpy, erc20proofs))
    for spec in specs_folders:
        file = path.join(erc20proofs, spec, '{}-erc20-spec.ini'.format(spec))
        with open(file, "a") as myfile:
            myfile.write(text)
    os.chdir(kevm_path)
    os.system('make split-proof-tests')
    os.chdir(cwd)


def compile_contract(sol_path, contract_path, contract_name):
    with open(contract_path, 'r') as f:
        read_data = f.read()
        if 'ERC20' not in read_data:
            return
    p = Popen([sol_path, '--bin-runtime', contract_path], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate(b"input data that is passed to subprocess' stdin")
    rc = p.returncode
    if rc == 0:
        state_variables = []
        contract_bin = ""
        lines = str(output).split("\\n")
        for index, line in enumerate(lines):
            if '{' in line:
                state_variables.append(line)
            if '{0}:{1}'.format(contract_path, contract_name) in line:
                contract_bin = lines[index + 2]
        variables = dict()
        for state_var in state_variables:
            obj = json.loads(state_var[state_var.find('{'):])
            variables[obj["var_name"]] = (obj["offset"], obj["byte_offset"])
        p.kill()
        pgmstring = """{0}
{1}
{2}
{3}
code:"0x{4}"        
        """
        totalsupply = ''
        balance = ''
        allowance = ''
        stopped = ''
        if variables.get("totalSupply"):
            totalsupply = '_totalsupply: ' + str(variables.get("totalSupply")[0])

        if variables.get("balance"):
            balance = '_balances: ' + str(variables.get("balance")[0])
        elif variables.get("balances"):
            balance = '_balances: ' + str(variables.get("balances")[0])

        if variables.get("allowed"):
            allowance = '_allowances: ' + str(variables.get("allowed")[0])
        elif variables.get("allowance"):
            allowance = '_allowances: ' + str(variables.get("allowance")[0])

        if variables.get("stopped"):
            stopped = '_stopped: ' + str(variables.get("stopped")[0])

        print(contract_name)
        text = pgmstring.format(totalsupply, balance, allowance, stopped, contract_bin)
        generate_proofs(text)
        specs = []
        for file in erc20_files:
            arg = Argument(contract_name, 'vyper', file, path.join(erc20_specs_path, file))
            specs.append(arg)
        for file in hobby_erc20_files:
            arg = Argument(contract_name, 'hobby', file, path.join(hobby_specs_path, file))
            specs.append(arg)
        for file in ds_token_erc20_files:
            arg = Argument(contract_name, 'ds_token', file, path.join(ds_token_specs_path, file))
            specs.append(arg)
        for file in zeppelin_erc20_files:
            arg = Argument(contract_name, 'zeppelin', file, path.join(zeppelin_specs_path, file))
            specs.append(arg)
        for spec in specs:
            prove(spec)




def compile_contracts(contract_path, solidity_v):
    contracts_dir = path.join(contract_path,solidity_v)
    all_files = [f for f in listdir(contracts_dir) if isfile(join(contracts_dir, f))]
    for file in all_files:
        contract = path.join(contracts_dir, file)
        compile_contract(solidity_path.format(solidity_v), contract, file.replace('.sol', ''))



compile_contracts(contracts_path,solidity_version)
