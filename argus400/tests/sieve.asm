        ;;
        ;; Sieve
        ;;
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
        # Max pos int is 2^23 = 8Million but limited here by the space available for the FLAGS
        EQU     TABLESZ,        8192
	EQU	MAXINTSZ, 	(TABLESZ-1)*48
        ORG     0x1020          ; Place program in 1st block of core store above register locations


        MACRO   PRINTNL( __rtmp__ )
        ldc      __rtmp__, 10
        out     __rtmp__, CONOUT
        ENDMACRO

        MACRO HALT()
        out r0, 0x0000
        ENDMACRO


        ;; Fill the flags table with zeroes, top to bottom
        ldc     r1, TABLESZ-1
fillloop:
        sto     r0, FLAGS!r1
        sbc     r1, 1
        jge     r1, fillloop

        ;;      Print first prime, 2
        ldc     r7,  2 + ord('0')
        out     r7, CONOUT
        PRINTNL (r1)

        ;; Iterate over numbers 3 .. MAXINT using r7 as loop counter, i
        ldc     r7, 3
        ldc     r6, 48         ; use r6 as a constant divisor= 48 for bit indexing
loop1:
        sto     r7, RQ          ; find word address and bit index for 'i' in flags
        ldx     r3, ZERO
        div     r3, r6          ; (r, q ) = <r3,Q>/48
        ldx     r1, RQ          ; get word address in r1 (before lsr which corrupts RQ!)
        srl     r3, 1          ; divide remainder by 2 (odd flags stored only)

        ldx     r2, FLAGS!r1    ; get flag word

        ldc     r1, 1          ; generate bit mask
        sla     r1, ZERO!r3     ; = 1 << (remainder//2)

        and     r2, r1          ; mask bit
        jnz     r2, nexti       ; flag is set so skip to next integer

                                ; Call print dec routine with r7=n
        ldc     r1, printnl    ; and return to set flags as multiples of this n
        sto     r1, RLINK
        jze     r0, printdec
printnl:
        PRINTNL( r1 )
        ;; now set all multiples of n in the table until we reach MAXINT
        ldx     r4, r7          ; r4 will be next multiple
        ldx     r5, r7          ; r5 is the increment, ie always move in multiples of 2n to avoid odd nums
        add     r5, r7
loop2:
        add     r4, r5          ; next n (odd ) + (even multiple)*n
        ldx     r1, r4
        sub     r1, MAXINT
        jge     r1, nexti       ; bail out if > MAXINT and look at next int
        sto     r4, RQ          ; (rem, quo) = (n%48,n//48)
        ldx     r3, ZERO
        div     r3, r6
        ldx     r1, RQ          ; check for out of bounds
        sbc     r1, TABLESZ
        jge     r1, nexti
        ldx     r2, RQ          ; r3 is rem//2, r2 is quotient (save Q before lsr corrupts it!)
        srl     r3, 1          ; divide remainder by 2 (only storing odds)
        ldc     r1, 1          ; generate bit mask
        sla     r1, ZERO!r3
        ldx     r3, FLAGS!r2    ; get FLAG word
        orf     r3, r1          ; set the mask bit
        sto     r3, FLAGS!r2    ; and write back
        jze     r0, loop2       ; set next flag
nexti:
        adc     r7, 2          ; increment loop counter by two (skip even nums)
        ldx     r1, r7
        sub     r1, MAXINT      ; less than MAXINT ?
        jlt     r1, loop1


        HALT()

;; printdec routine
;; r7 holds number to be printed (preserved)
;; r1,2,3,4 used as temporary stores
printdec:
        ldx     r4, r7          ; n
        ldc     r3, 1          ; suppress leading zeroes
        ldx     r2, MAXDIV      ; get first divisor into r2 = 1,000,000
pd_loop:
        ldx     r1, r2          ; ensure we always print the last digit in case
        sbc     r1, 1          ; n=0
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
FLAGS:  WORD	0
