#!/usr/bin/env python3
## ============================================================================
## a400asm.py - word oriented assembler for the Argus 400 CPU
##
## This file is part of the Ferranti Argus project: http://revaldinho.github.io/argus
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

EXAMPLES :

  python3 a400asm.py test.hex

'''


import sys, re

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

with open(sys.argv[1],"rb") as f:
    wordmem = [ (int(x,16) & 0xFFFFFF) for x in f.read().split() ]
wordmem.extend( [0] * (16384  - len(wordmem) ))

(ovr, busy, pc) = (0, 0, 0x1020) # initialise machine state inc PC
stdout=""
print ("PC   : Mem    : Instr  Reg Adr   (Mod) : C O :   R1     R2     R3     R4     R5     R6     R7")
while True:

    instr_word = wordmem[pc] &  0xFFFFFF
    N = (instr_word >> 10 ) & 0x03FFF
    opcode = (instr_word >> 5) & 0x1F
    acc = ((instr_word >> 2) & 0x7)
    mod = (instr_word) & 0x3

    acc_adr = 0x1000 + acc
    if mod > 0 :
        operand = wordmem[ 0x1000 + mod ] + N
    else:
        operand = N

    instr_str = "%-6s" % (dis[opcode])
    opreg_str = "r%d, %06x %s" % ( acc, N, ("(r%d)"% mod) if mod>0 else "    " )
    mem_str = " %06x " % (instr_word)
    reg_str = " ".join([ "%06x" % (wordmem[i]%0xFFFFFF) for i in range( 0x1001, 0x1000+8) ] )
    if operand == acc_adr:
        raise Exception ("Error - X and N cannot have the same value in %04x : %s %s" % (pc, instr_str, opreg_str ))

    print ("%04x :%s: %s %s : %d %d : %s" % (pc, mem_str, instr_str, opreg_str, wordmem[reg["C"]], ovr, reg_str ))

    pc += 1

    if opcode == op["halt"]:
        print("Stopped on halt instruction at %04x"  % pc )
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
    elif opcode == op["sub"]:
        result = wordmem [ acc_adr ]- wordmem[operand]
        wordmem [ acc_adr ] = result & 0xFFFFFF
        wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0

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
    elif opcode == op["subc"]:
        result = wordmem [ acc_adr ]- operand
        wordmem [ acc_adr ] = result & 0xFFFFFF
        wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0

    elif opcode == op["sto"]:
        result = wordmem [ acc_adr]
        wordmem [ operand ] = result & 0xFFFFFF        
    elif opcode == op["stom"]:
        result = -wordmem [ acc_adr]
        wordmem [ operand ] = result & 0xFFFFFF
        wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0                
    elif opcode == op["madd"]:
        result = operand + wordmem [ acc_adr ]
        wordmem [ operand ] = result & 0xFFFFFF
        wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0
    elif opcode == op["msub"]:
        result = wordmem [ acc_adr ]- wordmem[operand]        
        wordmem [ operand ] = result & 0xFFFFFF
        wordmem [reg["C"]]  = 1 if ( result & 0x1000000 != 0 ) else 0

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

    elif opcode == op["jpz"]:
        if wordmem[ acc_adr] == 0:
            pc = operand
    elif opcode == op["jpnz"]:
        if wordmem[ acc_adr] != 0:
            pc = operand
    elif opcode == op["jplt"]:
        if wordmem[ acc_adr] < 0:
            pc = operand
    elif opcode == op["jpge"]:
        if wordmem[ acc_adr] >= 0:
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
        wordmem[reg["Q"]] = result & 0x7FFFFF        # LS 23 bits
        wordmem[operand ] = (result >>23) & 0xFFFFFF # MS 24 bits
    elif opcode == op["div"]:
        dividend = (wordmem[acc_adr] << 23) + wordmem[Q]  # Bit 23 of MSB is zero always
        divisor = wordmem[operand]
        (quotient, remainder ) = ( dividend//divisor, dividend % divisor ) 
    else:
        print ("Error - unidentified opcode 0x%02x" % opcode)

## if len(sys.argv) > 2:  # Dump memory for inspection if required
##     with open(sys.argv[2],"w" ) as f:
##         for i in range(0, len(wordmem), 16):
##             f.write( '%s\n' %  ' '.join("%04x"%n for n in wordmem[i:i+16]))
