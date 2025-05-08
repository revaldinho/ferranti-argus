        ;;  Standard definitions
        EQU     ZERO   , 0x0000 ; all-zero's register at 0x0000 (use as literal or address)
        EQU     RROUND , 0x0001 ; round register
        EQU     RQ     , 0x0002 ; Q register
        EQU     RCARRY , 0x0003 ; carry register
        EQU     RHANDSW, 0x0004 ; hand switches
        EQU     RIN    , 0x1000 ; input register
        EQU     RLINK  , 0x1008 ; link register
        EQU     RINT   , 0x1010 ; 1st register of interrupt program

        ;;  Magic Console output for emulator
        EQU     CONOUT ,        0x0010

        ;;  Max size for Fib sequence
        EQU     MAXINTSZ , 8000000

        MACRO   PRINTNL( __rtmp__ )
        ld      __rtmp__, #10
        out     __rtmp__, CONOUT
        ENDMACRO

        ORG     0x1020          ; Place program in 1st block of core store above register locations

START:
        ld      r7, #ZERO
        ld      r6, #1
LOOP:
        ld      r1, #R1
        sto     r1, RLINK
        jpz     r0, PRINTDEC    ; print r7 as a decimal
R1:     PRINTNL( r1 )
        swap    r6, r7
        add     r6, r7
        ld      r1, r7
        sub     r1, MAXINT
        jplt    r1, LOOP
END:
        halt


;; printdec routine
;; r7 holds number to be printed (preserved)
;; r1,2,3,4 used as temporary stores
PRINTDEC:
        ld      r4, r7          ; n
        ld      r3, #1
pd_skip1:
        ld      r2, MAXDIV      ; get first divisor into r2 = 1,000,000
pd_loop:
        ld      r1, r2
        sub     r1, #1
        jpnz    r1, pd_notlast
        ld      r3, ZERO
pd_notlast:
        sto     r4, RQ          ; initialize double word dividend as (0,r4)
        ld      r4, ZERO
        div     r4, r2          ; (r,q) = (r4%r2, r4//r2)
        ld      r1, RQ          ; get quotient in r1 , leave remainder in r4
        jpnz    r1, printdec1   ; print if non-zero
        jpnz    r3, pd_skip     ; skip if zero and leading flag is set
printdec1:
        add     r1, #ord('0')
        out     r1, CONOUT
        ld      r3, ZERO        ; reset leading zero flag after first digit printed
pd_skip:
        ld      r1, #10         ; divide the divisor by 10
        sto     r2, RQ
        ld      r2, ZERO
        div     r2, r1
        ld      r2, RQ
        jpnz    r2, pd_loop

        jp      RLINK

MAXDIV: WORD    1000000
MAXINT: WORD    MAXINTSZ
