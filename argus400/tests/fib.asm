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
        ldc     __rtmp__, 10
        out     __rtmp__, CONOUT
        ENDMACRO

        MACRO HALT()
        out r0, 0x0000
        ENDMACRO

        ORG     0x1020          ; Place program in 1st block of core store above register locations

START:
        ldc     r7, ZERO
        ldc     r6, 1
LOOP:
        ldc     r1, R1
        sto     r1, RLINK
        jze     r0, PRINTDEC    ; print r7 as a decimal
R1:     PRINTNL( r1 )
        exc     r6, r7
        add     r6, r7
        ldx     r1, r7
        sub     r1, MAXINT
        jlt     r1, LOOP
END:
        HALT()


;; printdec routine
;; r7 holds number to be printed (preserved)
;; r1,2,3,4 used as temporary stores
PRINTDEC:
        ldx     r4, r7          ; n
        ldc     r3, 1
pd_skip1:
        ldx     r2, MAXDIV      ; get first divisor into r2 = 1,000,000
pd_loop:
        ldx     r1, r2
        sbc     r1, 1
        jnz     r1, pd_notlast
        ldx     r3, ZERO
pd_notlast:
        sto     r4, RQ          ; initialize double word dividend as (0,r4)
        ldx     r4, ZERO
        div     r4, r2          ; (r,q) = (r4%r2, r4//r2)
        ldx     r1, RQ          ; get quotient in r1 , leave remainder in r4
        jnz     r1, printdec1   ; print if non-zero
        jnz     r3, pd_skip     ; skip if zero and leading flag is set
printdec1:
        adc     r1, ord('0')
        out     r1, CONOUT
        ldx     r3, ZERO        ; reset leading zero flag after first digit printed
pd_skip:
        ldc     r1, 10         ; divide the divisor by 10
        sto     r2, RQ
        ldx     r2, ZERO
        div     r2, r1
        ldx     r2, RQ
        jnz     r2, pd_loop

        jcs     RLINK

MAXDIV: WORD    1000000
MAXINT: WORD    MAXINTSZ
