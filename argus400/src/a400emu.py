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

EXAMPLES :

  python3 a400asm.py -f test.hex

'''
from functools import reduce
import sys, re, getopt

def usage():
    print (__doc__);
    sys.exit(1)

def readhex( filename ) :
    with open(filename,"rt") as f:
        wordmem = [ (int(x,16) & 0xFFFFFF) for x in f.read().split() ]
    wordmem.extend( [0] * (16384  - len(wordmem) ))
    return wordmem


def emulate ( filename, nolisting ) :

    op = {
        "ld":0x0, "ldm":0x1, "add":0x2, "sub":0x3,
        "ldc":0x4, "ldmc":0x5, "addc":0x6, "subc":0x7,
        "sto":0x8, "stom":0x9, "madd":0x0A, "msub":0x0b,
        "swap":0xc, "and":0xd, "xor":0x0e, "or":0x0f,
        "jpz":0x10, "jpnz":0x11, "jpge":0x12, "jplt":0x13,
        "jpovr":0x14, "jpbusy":0x15, "out":0x16,"jp":0x17,
        "asr":0x18, "asl": 0x19, "lsr": 0x1a, "rol":0x1b,
        "halt":0x1c, "none1d":0x1d,
        "mul":0x1e, "div": 0x1f
    }
    dis = dict( [ (op[k],k) for k in [ x for x in op ]])
    reg = {"Z":0x0000, "R":0x0001, "Q":0x0002, "C":0x003, "HSW":0x0004,
           "INPUT":0x1000, "LINK":0x1008, "INT":0x1010}

    wordmem = readhex( filename )

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

        acc_adr = 0 if (acc==0 and opcode != op["jpbusy"] ) else 0x1000 + acc
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

        if opcode == op["halt"]:
            print("\nStopped on halt instruction at %04x after executing %d instructions"  % (pc, instr_count) )
            break

        elif opcode == op["ld"]:
            result = wordmem[operand]
            wordmem [ acc_adr ] = result & 0xFFFFFF
        elif opcode == op["ldm"]:
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
        elif opcode == op["ldmc"]:
            result = -operand
            wordmem [ acc_adr ] = result & 0xFFFFFF
            wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0
        elif opcode == op["addc"]:
            result = operand + wordmem [ acc_adr ]
            wordmem [ acc_adr ] = result & 0xFFFFFF
            wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0

            sign_op0 = (wordmem[acc_adr] >> 23) & 0x1
            sign_op1 = (operand >> 23) & 0x1
            sign_result = (result >> 23) & 0x1
            if ( sign_op0 == sign_op1 ) and sign_result != sign_op0:
                ovr = 1

        elif opcode == op["subc"]:
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
        elif opcode == op["stom"]:
            result = -wordmem [ acc_adr]
            wordmem [ operand ] = result & 0xFFFFFF
            wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0
        elif opcode == op["madd"]:
            result = wordmem[ operand ] + wordmem [ acc_adr ]
            wordmem [ operand ] = result & 0xFFFFFF
            wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0

            sign_op0 = (wordmem[acc_adr] >> 23) & 0x1
            sign_op1 = (wordmem[operand] >> 23) & 0x1
            sign_result = (result >> 23) & 0x1
            if ( sign_op0 == sign_op1 ) and sign_result != sign_op0:
                ovr = 1

        elif opcode == op["msub"]:
            result = wordmem [ acc_adr ]- wordmem[operand]
            wordmem [ operand ] = result & 0xFFFFFF
            wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0

            sign_op0 = (wordmem[acc_adr] >> 23) & 0x1
            sign_op1 = (wordmem[operand] >> 23) & 0x1
            sign_result = (result >> 23) & 0x1
            if ( sign_op0 != sign_op1 ) and sign_result != sign_op0:
                ovr = 1

        elif opcode == op["swap"]:
            tmp = wordmem[ operand ]
            wordmem [ operand ] = wordmem[ acc_adr ]
            wormem [acc_adr] = tmp
        elif opcode == op["and"]:
            wordmem [ acc_adr ] &= wordmem[ operand ]
        elif opcode == op["xor"]:
            wordmem [ acc_adr ] ^= wordmem[ operand ]
        elif opcode == op["or"]:
            wordmem [ acc_adr ] |= wordmem[ operand ]

        elif opcode == op["asr"]:
            # Create 32b sign extension
            signbit = 1 if (wordmem[acc_adr]&0x800000 >0) else 0
            sign_extension = reduce ( lambda x, y: x | y, [(2**i)*signbit for i in range (0,32)])
            double = sign_extension<<48 | wordmem[ acc_adr] << 24 | wordmem[reg["Q"]]
            result = double >> (operand & 0x01F)
            wordmem[reg["Q"]] = result & 0xFFFFFF
            wordmem[acc_adr] = (result >> 24) & 0xFFFFFF
        elif opcode == op["asl"]:
            result = (wordmem[acc_adr] << ( operand & 0x1F))
            wordmem[acc_adr] = result & 0xFFFFFF
        elif opcode == op["lsr"]:
            double = wordmem[ acc_adr] << 24 | wordmem[reg["Q"]]
            result = double >> (operand & 0x01F)
            wordmem[reg["Q"]] = result & 0xFFFFFF
            wordmem[acc_adr] = (result >> 24) & 0xFFFFFF
        elif opcode == op["rol"]:
            double = (wordmem[acc_adr]<<48) | (wordmem[acc_adr]<<24)  | (wordmem[acc_adr])
            # result in MS 24 bits so shift back
            result = ((double << operand & 0x1F) >> 48)
            wordmem[acc_adr] = result & 0xFFFFFF

        elif opcode == op["jpz"]:
            if wordmem[ acc_adr] == 0:
                pc = operand
        elif opcode == op["jpnz"]:
            if wordmem[ acc_adr] != 0:
                pc = operand
        elif opcode == op["jplt"]:
            if wordmem[ acc_adr] & 0x800000 == 0x800000:
                pc = operand
        elif opcode == op["jpge"]:
            if wordmem[ acc_adr] & 0x800000 == 0:
                pc = operand
        elif opcode == op["jpovr"]:
            if ovr != 0:
                pc = operand
                ovr = 0
        elif opcode == op["jpbusy"]:
            if (busy & (1<<operand)) != 0:
                pc = operand
        elif opcode == op["jp"]:
            pc = wordmem[operand]

        elif opcode == op["mul"]:
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
        else:
            print ("Error - unidentified opcode 0x%02x" % opcode)

    if not nolisting:
        print ( ("").join(conout) )


if __name__ == "__main__":
    """
    Command line option parsing.
    """
    filename = ""
    nolisting = False
    try:
        opts, args = getopt.getopt( sys.argv[1:], "f:nh", ["filename=","nolisting","help"])
    except getopt.GetoptError as  err:
        print(err)
        usage()

    for opt, arg in opts:
        if opt in ( "-f", "--filename" ) :
            filename = arg
        elif opt in ("-n", "--nolisting" ) :
            nolisting = True
        elif opt in ("-h", "--help" ) :
            usage()
        else:
            sys.exit(1)

    if filename != "":
        emulate( filename , nolisting)
    else:
        usage()
