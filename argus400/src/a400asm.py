#!/usr/bin/env python3
## ============================================================================
## a400asm.py - word oriented assembler for the Argus 400 CPU
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

  a400asm is an assembler for the Ferranti Argus 400 CPU

REQUIRED SWITCHES ::

  -f --filename  <filename>      specify the assembler source file

OPTIONAL SWITCHES ::

  -o --output    <filename>      specify file name for assembled code

  -g --format    <bin|hex>       set the file format for the assembled code
                                 - default is hex

  -n --nolisting                 suppress the listing to stdout while the
                                 program runs

  -s, --start_adr                sets the number of the first byte to be written
                                 out (must be even)

  -z, --size                     sets the number of bytes to be written out (must
                                 be even)

  -h --help                      print this help message

  If no output filename is provided the assembler just produces the normal
  listing output to stdout.

EXAMPLES ::

  python3 a400asm.py -f test.s -o test.bin -g bin
'''

header_text = '''
-------------------------------------------------------------------------
 A r g u s 4 0 0  *  A S S E M B L E R

-------------------------------------------------------------------------
 ADDR : CODE                 : SOURCE
------:----------------------:-------------------------------------------'''

import sys, re, codecs, getopt

# globals
(errors, warnings, nextmnum) = ( [],[],0)

def usage():
    print (__doc__);
    sys.exit(1)

def expand_macro(line, macro, mnum):  # recursively expand macros, passing on instances not (yet) defined
    global nextmnum
    (text,mobj)=([line],re.match("^(?P<label>\w*\:)?\s*(?P<name>\w+)\s*?\((?P<params>.*?)\)",line))
    if mobj and mobj.groupdict()["name"] in macro:
        (label,instname,paramstr)= (mobj.groupdict()["label"],mobj.groupdict()["name"],mobj.groupdict()["params"])
        (text, instparams,mnum,nextmnum) = (["; MACRO %s" % line.strip()], [x.strip() for x in paramstr.split(",")],nextmnum,nextmnum+1)
        if label:
            text.append("%s%s"% (label, ":" if (label != "" and label != "None" and not (label.endswith(":"))) else ""))
        for newline in macro[instname][1]:
            for (s,r) in zip( macro[instname][0], instparams):
                newline = (newline.replace(s,r) if s else newline).replace('@','%s_%s' % (instname,mnum))
            text.extend(expand_macro(newline, macro, nextmnum))
        text.append("; ENDMACRO")
    return(text)

def preprocess( filename ) :
    # Pass 0 - read file, expand all macros and return a new text file
    global errors, warnings, nextmnum
    (newtext,macro,macroname,mnum)=([],dict(),None,0)
    for line in open(filename, "r").readlines():
        mobj =  re.match("\s*?MACRO\s*(?P<name>\w*)\s*?\((?P<params>.*)\)", line, re.IGNORECASE)
        if mobj:
            (macroname,macro[macroname])=(mobj.groupdict()["name"],([x.strip() for x in (mobj.groupdict()["params"]).split(",")],[]))
        elif re.match("\s*?ENDMACRO.*", line, re.IGNORECASE):
            (macroname, line) = (None, '; '+line.strip())
        elif macroname:
            macro[macroname][1].append(line)
        newtext.extend(expand_macro(('' if not macroname else '; ') + line.strip(), macro, mnum))
    return newtext

def assemble( filename, listingon=True):
    global errors, warnings, nextmnum

    op = "ld ldm add sub ldc ldmc addc subc sto stom madd msub swap and xor or jpz jpnz jpge jplt jpovr jpbusy out jp asr asl lsr rol halt none1d mul div".split()
    symtab = dict( [ ("r%d"%d,(0x1000 if d>0 else 0) +d) for d in range(0,8)])
    (wordmem,wcount)=([0x0000]*16384,0)
    (gd,field_dict) = ({},{})
    newtext = preprocess(filename)

    for iteration in range (0,2): # Two pass assembly
        (wcount,nextmem) = (0,0)
        for line in newtext:
            mobj = re.match('^((?P<label>\w+):)?\s*(?P<inst>\w+)?\s*(?P<operands>.*)',re.sub(";.*","",line))
            (label, inst,operands) = [ mobj.groupdict()[item] for item in ("label", "inst","operands")]
            (opfields,words, memptr) = ([ x.strip() for x in operands.split(",")],[], nextmem)
            if (iteration==0 and (label and label != "None") or (inst=="EQU")):
                errors = (errors + ["Error: Symbol %16s redefined in ...\n         %s" % (label,line.strip())]) if label in symtab else errors
                try:
                    exec ("%s= int(%s)" % ((label,str(nextmem)) if label!= None else (opfields[0], opfields[1])), globals(), symtab )
                except:
                    errors += [ "Syntax error on:\n  %s" % line.strip() ]
                    continue
            if (inst in("WORD","BYTE") or inst in op) and iteration < 1:
                if inst=="WORD":
                    nextmem += len(opfields)
                elif inst == "BYTE":
                    nextmem += (len(opfields)+2)//3
                else:
                    nextmem += 1
            elif inst in op or inst in ("BYTE","WORD","STRING","BSTRING","PBSTRING"):
                if  inst in("STRING","BSTRING","PBSTRING"):
                    strings = re.match('.*STRING\s*\"(.*?)\"(?:\s*?,\s*?\"(.*?)\")?(?:\s*?,\s*?\"(.*?)\")?(?:\s*?,\s*?\"(.*?)\")?.*?', line.rstrip())
                    string_data = codecs.decode(''.join([ x for x in strings.groups() if x != None]),  'unicode_escape')
                    string_len = chr(len( string_data ) & 0xFF) if inst=="PBSTRING" else ''    # limit string length to 255 for PBSTRINGS
                    if inst in ("BSTRING","PBSTRING") :
                        wordstr =  string_len + string_data + chr(0) + chr(0) + chr(0)
                        words = [(ord(wordstr[i])|(ord(wordstr[i+1])<<8)|(ord(wordstr[i+2])<<16)) for  i in range(0,len(wordstr)-2,3) ]
                    else:
                        wordstr = string_len + string_data
                        words = [ord(wordstr[i]) for  i in range(0,len(wordstr))]
                else:
                    try:
                        exec("PC=%d+1" % nextmem, globals(), symtab) # calculate PC as it will be in EXEC state
                        if inst == "BYTE":
                            words = [int(eval( f,globals(), symtab)) for f in opfields ] + [0]*2
                            words = ([(words[i+2]&0xFF)<<16|(words[i+1]&0xFF)<<8|(words[i]&0xFF) for i in range(0,len(words)-2,3)])
                        elif inst == "WORD":
                            words = [int(eval( f,globals(), symtab)) for f in opfields ]
                        elif inst in op:
                            reg_field = 0
                            if (inst in "jp jpovr".split()) and len(opfields)==1:
                                # <instr> <expr[!r0-3]>
                                gd = (re.match("(?P<operand>[0-9a-zA-Z_\'\"\+\-\)\(\*\&\^\%\|\s]*)(\!)?(?P<modifier>r[0-7])?\s*?", opfields[0])).groupdict()
                            elif inst == "halt":
                                gd = { "operand":"00", "modifier":"00"}
                            elif len(opfields)==2 :
                                # <instr> <reg>[ , expr[!r0-3]]
                                if re.match("r[0-7]", opfields[0]):
                                    reg_field = int(opfields[0][1])
                                else:
                                    raise Exception ("Register numbers can only be in the range 0-7")
                                if (inst in ("ld ldm add sub".split())) and opfields[1].strip()[0]=="#":
                                    operand = opfields[1].strip()[1:]
                                    inst = inst+"c"
                                else:
                                    operand = opfields[1].strip()
                                gd = (re.match("(?P<operand>[0-9a-zA-Z_\'\"\+\-\)\(\*\&\^\%\|\s]*)(\!)?(?P<modifier>r[0-7])?\s*?", operand)).groupdict()
                            else:
                                raise Exception ( "Wrong number of arguments")
                            field_dict = { "inst": op.index(inst), "adr":eval(gd["operand"],globals(),symtab), "reg":reg_field, "mod":0 if not gd["modifier"] else int(gd["modifier"][1])}
                            words = [ field_dict["adr"] << 10 | field_dict["inst"] << 5 | field_dict["reg"]<<2 | field_dict["mod"]]
                    except (ValueError, NameError, TypeError,SyntaxError, Exception ):
                        (words,errors)=([0],errors+["Error:%d: illegal or undefined register name or expression in ...\n         %s" % (iteration,line.strip()) ])
                (wordmem[nextmem:nextmem+len(words)], nextmem,wcount )  = (words, nextmem+len(words),wcount+len(words))
            elif inst == "ORG":
                nextmem = eval(operands,globals(),symtab)
            elif inst and (inst != "EQU") and iteration>0 :
                errors.append("Error: unrecognized instruction or macro %s in ...\n         %s" % (inst,line.strip()))

            if iteration > 0 and listingon==True:
                l = line.strip()
                idx = 0
                label = ""
                code = l
                if not l.startswith(";"):
                    (label, code ) = ("", l) if not ':' in line else (l).split(':')
                    if label != "":
                        label+=':'
                        idx = 0
                while len(words)-idx > 3:
                    print(" %04x : %-21s: "%(memptr,' '.join([("%06x" % i) for i in words[idx:idx+3]])))
                    idx +=3
                    memptr +=3
                print(" %04x : %-21s: %-10s%s"%(memptr,' '.join([("%06x" % i) for i in words[idx:]]),label,code.strip()))

    print ("\nSymbol Table:\n\n%s\n" % ('\n'.join(["%-28s 0x%06X (%08d)" % (k,v,v) for k,v in sorted(symtab.items()) if not re.match("r\d|r\d\d|pc|psr",k)])))
    print ("\nAssembled %d words of code with %d error%s and %d warning%s." % (wcount,len(errors),'' if len(errors)==1 else 's',len(warnings),'' if len(warnings)==1 else 's'))
    print ("\n%s\n%s" % ('\n'.join(errors),'\n'.join(warnings)))
    return wordmem


if __name__ == "__main__":
    """
    Command line option parsing.
    """
    filename = ""
    hexfile = ""
    output_filename = ""
    output_format = "hex"
    listingon = True
    start_adr = 0
    size = 0
    try:
        opts, args = getopt.getopt( sys.argv[1:], "f:o:g:s:z:hn", ["filename=","output=","format=","start_adr=","size=","help","nolisting"])
    except getopt.GetoptError as  err:
        print(err)
        usage()

    if len(args)>=1:
        filename = args[0]
    if len(args)>1:
        output_filename = args[1]
        output_format = "hex"

    for opt, arg in opts:
        if opt in ( "-f", "--filename" ) :
            filename = arg
        elif opt in ( "-o", "--output" ) :
            output_filename = arg
        elif opt in ( "-s", "--start_adr" ) :
            start_adr = int(arg,0)
        elif opt in ( "-z", "--size" ) :
            size = int(arg,0)
        elif opt in ( "-g", "--format" ) :
            if (arg in ("hex", "bin")):
                output_format = arg
            else:
                usage()
        elif opt in ("-n", "--nolisting"):
            listingon = False
        elif opt in ("-h", "--help" ) :
            usage()
        else:
            sys.exit(1)

    if filename != "":
        if size==0:
            size = 16384 - start_adr
        print(header_text)
        wordmem = assemble(filename, listingon)[start_adr:start_adr+size]
        if len(errors)==0 and output_filename != "":
            if output_format == "hex":
                with open(output_filename,"w" ) as f:
                    f.write( '\n'.join([''.join("%06x " % d for d in wordmem[j:j+12]) for j in [i for i in range(0,len(wordmem),12)]]))
            else:
                with open(output_filename,"wb" ) as f:
                    # Write binary in little endian order
                    for w in wordmem:
                        bytes = bytearray()
                        bytes.append( w & 0xFF)
                        bytes.append( (w>>8) & 0xFF)
                        bytes.append( (w>>16) & 0xFF)
                        f.write(bytes)
    else:
        usage()
    sys.exit( len(errors)>0)
