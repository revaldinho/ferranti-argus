#!/usr/bin/env python3
## ============================================================================
## a400emu.py - instruction set level emulator for the Ferranti Argus 400 computer
##
## This file is part of the Ferranti Argus project: http://revaldinho.github.io/ferranti-argus
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## See  <http://www.gnu.org/licenses/> for a copy of the GNU Lesser General
## Public License
## ============================================================================
'''
USAGE:

  a400emu is an instruction set level emulator for the Ferranti Argus 400 computer

REQUIRED SWITCHES ::

  -f --filename  <filename>      specify the assembler source file

OPTIONAL SWITCHES ::

  -n --nolisting                 turn off the debug trace output

  -1 --100                       emulate only Argus 100/400 instructions

  -4 --400                       emulate only Argus 100/400 instructions

  -5 --500                       emulate Argus 500 instructions and print an instruction
                                 timing summary at the end of emulation (default)

  -h --help                      print this help message

EXAMPLES :

  python3 a400asm.py -f test.hex

'''
from functools import reduce
from operator import add

import sys, re, getopt
import datetime

op = {
    "ldx":0x0, "nlx":0x1, "add":0x2, "sub":0x3,
    "ldc":0x4, "lmc":0x5, "adc":0x6, "sbc":0x7,
    "sto":0x8, "stn":0x9, "ads":0x0A, "ssb":0x0b,
    "exc":0xc, "and":0xd, "neq":0x0e, "orf":0x0f,
    "jze":0x10, "jnz":0x11, "jge":0x12, "jlt":0x13,
    "ovr":0x14, "jbs":0x15, "out":0x16, "jcs":0x17,
    "sra":0x18, "sla": 0x19, "srl": 0x1a, "slc":0x1b,
    "sll":0x1c, "slv":0x1d,
    "mpy":0x1e, "div": 0x1f
}

model_id = ("Argus 400", "Argus 500 Series 1, Model 1", "Argus 500 Series 2, Model 2", "Argus 500 Series 3, Model 1", "Argus 500 Series 4, Model 2")
# A500 Instruction times per model taken from Argus 500 training manual
# A400 instruction timings are not available yet, so for now these are taken from Argus 500 S1M1 machine (which should share the same 4Mhz clock) and then
#      - add 24*0.25us (4MHz) cycles for each operation using the ALU including comparison and address modification
#      - shifts are treated the same as in the Argus 500 (although this makes no sense for the 4MHz cycle, but use this for now until we find some more
#        documentation on both machines - e.g. possibly the Argus 500 used in the training course was actually a 2.5MHz machine ?))
#                            :  A400   S1M1 S2M2 S3M1 S4M2
base_timing_us = { op["ldx"] : ( 6.0,  6.0, 3.6, 6.0, 3.2 ),
                   op["nlx"] : ( 6.0,  6.0, 3.6, 6.0, 3.2 ),
                   op["add"] : ( 6.0,  6.0, 3.6, 6.0, 3.2 ),
                   op["sub"] : ( 6.0,  6.0, 3.6, 6.0, 3.2 ),
                   op["ldc"] : ( 4.7,  4.7, 3.1, 4.7, 2.8 ),
                   op["lmc"] : ( 4.7,  4.7, 3.1, 4.7, 2.8 ),
                   op["adc"] : ( 4.7,  4.7, 3.1, 4.7, 2.8 ),
                   op["sbc"] : ( 4.7,  4.7, 3.1, 4.7, 2.8 ),
                   op["sto"] : ( 6.0,  6.0, 3.6, 6.0, 3.2 ),
                   op["stn"] : ( 6.0,  6.0, 3.6, 6.0, 3.2 ),
                   op["ads"] : ( 6.4,  6.4, 4.0, 6.4, 3.6 ),
                   op["ssb"] : ( 6.4,  6.4, 4.0, 6.4, 3.6 ),
                   op["exc"] : ( 6.0,  6.0, 3.6, 6.0, 3.2 ),
                   op["and"] : ( 6.0,  6.0, 3.6, 6.0, 3.2 ),
                   op["neq"] : ( 6.0,  6.0, 3.6, 6.0, 3.2 ),
                   op["orf"] : ( 6.0,  6.0, 3.6, 6.0, 3.2 ),
                   op["jze"] : ( 4.0,  4.0, 2.4, 4.0, 2.2 ),
                   op["jnz"] : ( 4.0,  4.0, 2.4, 4.0, 2.2 ),
                   op["jge"] : ( 4.0,  4.0, 2.4, 4.0, 2.2 ),
                   op["jlt"] : ( 4.0,  4.0, 2.4, 4.0, 2.2 ),
                   op["ovr"] : ( 2.7,  2.7, 1.9, 3.4, 1.9 ),
                   op["jbs"] : ( 2.7,  2.7, 1.9, 3.4, 1.9 ),
                   op["out"] : ( 6.0,  6.0, 3.6, 6.0, 3.2 ),
                   op["jcs"] : ( 6.0,  6.0, 3.6, 6.0, 3.2 ),
                   op["sra"] : ( 4.4,  4.4, 2.8, 4.4, 2.6 ),
                   op["sla"] : ( 4.4,  4.4, 2.8, 4.4, 2.6 ),
                   op["srl"] : ( 4.4,  4.4, 2.8, 4.4, 2.6 ),
                   op["slc"] : ( 4.4,  4.4, 2.8, 4.4, 2.6 ),
                   op["sll"] : ( 4.4,  4.4, 2.8, 4.4, 2.6 ),
                   op["slv"] : ( 6.4,  6.4, 4.0, 6.4, 3.6 ),
                   op["mpy"] : ( 13.4, 13.4, 11.5, 13.4, 11.1),
                   op["div"] : ( 15.0, 15.0, 13.1, 15.0, 12.7)
                  }
## Add to basic timing for reading from IO space
IO_inc_timing_us   = ( 2.0, 2.0, 1.2, 2.0, 1.1 )
## Add to basic timing for modified address operations (ie modifier != 0 )
modifier_timing_us = ( 2.0, 2.0, 1.2, 2.0, 1.1 )
# Add this factor * N for multiplace shift operations
perbit_shift_timing_us  = (0.4, 0.4, 0.4, 0.4, 0.4 )
perbit_alu_timing_us  = (0.25, 0.0, 0.0, 0.0, 0.0 )

def exec_time_us ( opcode, operand, modifier, io_low, io_high, memstore ) :
    t_us = [0]* 5
    # NB operand has already been modified as required for computing the shift distance or determining IO address
    for i in range (0, 5):
        t_us[i] = base_timing_us[opcode][i]
        t_us[i] += IO_inc_timing_us[i] if ( io_low <= operand <= io_high ) else 0
        t_us[i] += modifier_timing_us[i] if ( modifier > 0 ) else 0
        t_us[i] += (perbit_shift_timing_us[i] * (operand % 32)) if (op["sra"] <= opcode <= op["slv"]) else 0
        if i == 0 : # Argus 400
            if opcode in (
                    op["nlx"], op["add"],  op["sub"],
                    op["lmc"], op["adc"],  op["sbc"],
                    op["stn"], op["ads"],  op["ssb"],
                    op["and"], op["neq"],  op["orf"],
                    op["jze"], op["jnz"], op["jge"],  op["jlt"],
                    op["jbs"], op["jcs"] ):
                t_us[i] += perbit_alu_timing_us[i] * 24
            elif opcode == op["mpy"] or op == op["div"]:
                # surely many more times around the ALU ?
                t_us[i] += perbit_alu_timing_us[i] * 24 * 24
    return t_us

def print_exec_time ( t ) :
    print ( "Nominal execution times for different Argus models")
    series = 0
    model = 0
    for i in t:
        if ( i > 1000000 ) :
            print ( "- %-32s : %10.3f s  %s" % ( model_id[series], i/1000000, "[1]" if series >0 else "[2]" ))
        else:
            print ( "- %-32s : %10f ms  %s" % ( model_id[series], i/1000, "[1]" if series >0 else "[2]" ))
        series+=1

    print ( "[1] Argus 500 times taken from Argus 500 training manual")
    print ( "[2] Argus 400 times taken by combining Argus 500 Series 1 times, with additional 4Mhz cycles for use of bit-serial ALU")




def usage():
    print (__doc__);
    sys.exit(1)

def readhex( filename ) :
    try:
        with open(filename,"rt") as f:
            wordmem = [ (int(x,16) & 0xFFFFFF) for x in f.read().split() ]
            wordmem.extend( [0] * (16384  - len(wordmem) ))
        return wordmem
    except:
        print ( "Error reading %s" % filename )
        sys.exit(1)

def emulate ( filename, nolisting, machine ) :

    dis = dict( [ (op[k],k) for k in [ x for x in op ]])
    reg = {"Z":0x0000, "R":0x0001, "Q":0x0002, "C":0x003, "HSW":0x0004,
           "INPUT":0x1000, "LINK":0x1008, "INT":0x1010}

    wordmem = readhex( filename )

    timers = [0.0,0.0,0.0,0.0,0.0]
    conout = []
    (ovr, busy, pc, instr_count) = (0, 0, 0x1020, 0) # initialise machine state inc PC

    if not nolisting:
        print ("PC   : Mem    : Instr  Reg Adr   (Mod) : C O :   R1     R2     R3     R4     R5     R6     R7   :    Q")

    while True:
        instr_count += 1
        instr_word = wordmem[pc] &  0xFFFFFF
        N = (instr_word >> 10 ) & 0x03FFF
        opcode = (instr_word >> 5) & 0x1F
        acc = ((instr_word >> 2) & 0x7)
        mod = (instr_word) & 0x3

        acc_adr = 0 if (acc==0 and opcode != op["jbs"] ) else 0x1000 + acc
        if mod > 0 :
            operand = wordmem[ 0x1000 + mod ] + N
        else:
            operand = N

        instr_str = "%-6s" % (dis[opcode])
        opreg_str = "r%d, %06x %s" % ( acc, N, ("(r%d)"% mod) if mod>0 else "    " )
        mem_str = " %06x " % (instr_word)
        qreg_str = "%06x" % (wordmem[reg["Q"]])
        reg_str = " ".join([ "%06x" % (wordmem[i]&0xFFFFFF) for i in range( 0x1001, 0x1000+8) ] )
        if (operand == acc_adr) and (operand != 0):
            raise Exception ("\nError - X and N cannot have the same value in %04x : %s %s" % (pc, instr_str, opreg_str ))

        if not nolisting:
            print ("%04x :%s: %s %s : %d %d : %s : %s" % (pc, mem_str, instr_str, opreg_str, wordmem[reg["C"]], ovr, reg_str, qreg_str ))
            # print ( "MEM: " + " ".join( [ "%06x" % (wordmem[i]&0xFFFFFF) for i in range ( 0x1100, 0x1110)]))

        pc += 1

        if machine == 500:
            timers = [ sum(i) for i in zip(timers, exec_time_us( opcode, operand, mod, 0x010, 0x1000, wordmem ) ) ]

        if opcode == op["ldx"]:
            result = wordmem[operand]
            wordmem [ acc_adr ] = result & 0xFFFFFF
        elif opcode == op["nlx"]:
            result = -wordmem[operand]
            wordmem [ acc_adr ] = result & 0xFFFFFF
            wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0
        elif opcode == op["add"]:
            result = wordmem[operand] + wordmem [ acc_adr ]
            wordmem [ acc_adr ] = result & 0xFFFFFF
            wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0

            sign_op0 = (wordmem[acc_adr] >> 23) & 0x1
            sign_op1 = (wordmem[operand] >> 23) & 0x1
            sign_result = (result >> 23) & 0x1
            if ( sign_op0 == sign_op1 ) and sign_result != sign_op0:
                ovr = 1

        elif opcode == op["sub"]:
            result = wordmem [ acc_adr ]- wordmem[operand]
            wordmem [ acc_adr ] = result & 0xFFFFFF
            wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0

            sign_op0 = (wordmem[acc_adr] >> 23) & 0x1
            sign_op1 = (wordmem[operand] >> 23) & 0x1
            sign_result = (result >> 23) & 0x1
            if ( sign_op0 != sign_op1 ) and sign_result != sign_op0:
                ovr = 1

        elif opcode == op["ldc"]:
            result = operand
            wordmem [ acc_adr ] = result & 0xFFFFFF
        elif opcode == op["lmc"]:
            result = -operand
            wordmem [ acc_adr ] = result & 0xFFFFFF
            wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0
        elif opcode == op["adc"]:
            result = operand + wordmem [ acc_adr ]
            wordmem [ acc_adr ] = result & 0xFFFFFF
            wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0

            sign_op0 = (wordmem[acc_adr] >> 23) & 0x1
            sign_op1 = (operand >> 23) & 0x1
            sign_result = (result >> 23) & 0x1
            if ( sign_op0 == sign_op1 ) and sign_result != sign_op0:
                ovr = 1

        elif opcode == op["sbc"]:
            result = wordmem [ acc_adr ] - operand
            wordmem [ acc_adr ] = result & 0xFFFFFF
            wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0

            sign_op0 = (wordmem[acc_adr] >> 23) & 0x1
            sign_op1 = (operand >> 23) & 0x1
            sign_result = (result >> 23) & 0x1
            if ( sign_op0 != sign_op1 ) and sign_result != sign_op0:
                ovr = 1

        elif opcode == op["sto"]:
            result = wordmem [ acc_adr]
            wordmem [ operand ] = result & 0xFFFFFF
        elif opcode == op["stn"]:
            result = -wordmem [ acc_adr]
            wordmem [ operand ] = result & 0xFFFFFF
            wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0
        elif opcode == op["ads"]:
            result = wordmem[ operand ] + wordmem [ acc_adr ]
            wordmem [ operand ] = result & 0xFFFFFF
            wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0

            sign_op0 = (wordmem[acc_adr] >> 23) & 0x1
            sign_op1 = (wordmem[operand] >> 23) & 0x1
            sign_result = (result >> 23) & 0x1
            if ( sign_op0 == sign_op1 ) and sign_result != sign_op0:
                ovr = 1

        elif opcode == op["ssb"]:
            result = wordmem [ acc_adr ]- wordmem[operand]
            wordmem [ operand ] = result & 0xFFFFFF
            wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0

            sign_op0 = (wordmem[acc_adr] >> 23) & 0x1
            sign_op1 = (wordmem[operand] >> 23) & 0x1
            sign_result = (result >> 23) & 0x1
            if ( sign_op0 != sign_op1 ) and sign_result != sign_op0:
                ovr = 1

        elif opcode == op["exc"]:
            tmp = wordmem[ operand ]
            wordmem [ operand ] = wordmem[ acc_adr ]
            wordmem [acc_adr] = tmp
        elif opcode == op["and"]:
            wordmem [ acc_adr ] &= wordmem[ operand ]
        elif opcode == op["neq"]:
            wordmem [ acc_adr ] ^= wordmem[ operand ]
        elif opcode == op["orf"]:
            wordmem [ acc_adr ] |= wordmem[ operand ]

        elif opcode == op["sra"]:
            # Create 32b sign extension
            signbit = 1 if (wordmem[acc_adr]&0x800000 >0) else 0
            sign_extension = reduce ( lambda x, y: x | y, [(2**i)*signbit for i in range (0,32)])
            double = sign_extension<<48 | wordmem[ acc_adr] << 24 | wordmem[reg["Q"]]
            result = double >> (operand & 0x01F)
            wordmem[reg["Q"]] = result & 0xFFFFFF
            wordmem[acc_adr] = (result >> 24) & 0xFFFFFF
        elif opcode == op["sla"]:
            result = (wordmem[acc_adr] << ( operand & 0x1F))
            wordmem[acc_adr] = result & 0xFFFFFF
        elif opcode == op["srl"]:
            double = wordmem[ acc_adr] << 24 | wordmem[reg["Q"]]
            result = double >> (operand & 0x01F)
            wordmem[reg["Q"]] = result & 0xFFFFFF
            wordmem[acc_adr] = (result >> 24) & 0xFFFFFF
        elif opcode == op["slc"]:
            double = (wordmem[acc_adr]<<48) | (wordmem[acc_adr]<<24)  | (wordmem[acc_adr])
            # result in MS 24 bits so shift back
            result = ((double << operand & 0x1F) >> 48)
            wordmem[acc_adr] = result & 0xFFFFFF
        elif opcode == op["sll"]:
            if machine == 500:
                # FIXME - A500 only
                pass
            else:
                print("Error - opcode %d is not implemented in Argus 100 or 400 machines, SLL in Argus 500")
                sys.exit(1)
        elif opcode == op["slv"]:
            if machine == 500:
                # FIXME - A500 only
                pass
            else:
                print("Error - opcode %d is not implemented in Argus 100 or 400 machines, SLV in Argus 500")
                sys.exit(1)
        elif opcode == op["jze"]:
            if wordmem[ acc_adr] == 0:
                if operand == pc -1:
                    # Effective HALT instruction
                    print("\nStopped on halt instruction at 0x%04x after executing %d instructions"  % (pc, instr_count) )
                    break
                else:
                    pc = operand
        elif opcode == op["jnz"]:
            if wordmem[ acc_adr] != 0:
                pc = operand
        elif opcode == op["jlt"]:
            if wordmem[ acc_adr] & 0x800000 == 0x800000:
                pc = operand
        elif opcode == op["jge"]:
            if wordmem[ acc_adr] & 0x800000 == 0:
                pc = operand
        elif opcode == op["ovr"]:
            if ovr != 0:
                pc = operand
                ovr = 0
        elif opcode == op["jbs"]:
            if (busy & (1<<operand)) != 0:
                pc = operand
        elif opcode == op["jcs"]:
            pc = wordmem[operand]

        elif opcode == op["mpy"]:
            result = wordmem[operand ] * wordmem[acc_adr]

            # print ( "MUL %d * %d = %d" % ( wordmem[acc_adr] , wordmem[operand], result))
            wordmem[reg["Q"]] = result & 0x7FFFFF        # LS 23 bits
            wordmem[acc_adr] = (result >>23) & 0xFFFFFF # MS 24 bits

            sign_op0 = (wordmem[acc_adr] >> 23) & 0x1
            sign_op1 = (wordmem[operand] >> 23) & 0x1
            sign_result = (result >> 23) & 0x1
            if ( sign_op0 == sign_op1 ) and sign_result != 0:  # like signed operands always produce a positive result
                ovr = 1
            elif ( sign_op0 != sign_op1 ) and sign_result !=1 : # unlike signed operands always produce a negative result
                ovr = 1

        elif opcode == op["div"]:
            dividend = (wordmem[acc_adr] << 23) + wordmem[reg["Q"]]  # Bit 23 of MSB is zero always
            divisor = wordmem[operand]
            (quotient, remainder ) = ( dividend//divisor, dividend % divisor )
            wordmem[reg["Q"]] = quotient & 0xFFFFFF
            wordmem[acc_adr] = remainder
            # print ( "DIV %d / %d = %d REM %d" % ( dividend, divisor, quotient, remainder))

        elif opcode == op["out"]:
            if operand == 0x0010: # CONOUT for now
                if nolisting:
                    sys.stdout.write("%c" % (wordmem[acc_adr]%127))
                    sys.stdout.flush()
                else:
                    conout.append ( "%c" % (wordmem[acc_adr]%127))
            elif operand == 0x0000 and acc_adr == 0x0000:
                print("\nStopped on halt instruction at 0x%04x after executing %d instructions"  % (pc, instr_count) )
                break
        else:
            print ("Error - unidentified opcode 0x%02x" % opcode)

    if machine == 500 :
        print_exec_time(timers)
    if not nolisting:
        print ( ("").join(conout) )

if __name__ == "__main__":
    """
    Command line option parsing.
    """
    filename = ""
    nolisting = False
    machine = 500
    try:
        opts, args = getopt.getopt( sys.argv[1:], "f:1:4:5:nh", ["filename=","100","400","500","nolisting","help"])
    except getopt.GetoptError as  err:
        print(err)
        usage()

    for opt, arg in opts:
        if opt in ( "-f", "--filename" ) :
            filename = arg
        elif opt in ("-n", "--nolisting" ) :
            nolisting = True
        elif opt in ("-1", "--100" ) :
            machine = 100
        elif opt in ("-4", "--400" ) :
            machine = 400
        elif opt in ("-4", "--500" ) :
            machine = 500
        elif opt in ("-h", "--help" ) :
            usage()
        else:
            sys.exit(1)

    if filename != "":
        emulate( filename , nolisting, machine)
    else:
        usage()
