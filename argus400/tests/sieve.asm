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
        ld      __rtmp__, #10
        out     __rtmp__, CONOUT
        ENDMACRO



        ;; Fill the flags table with zeroes, top to bottom
        ld      r1, #TABLESZ-1
fillloop:
        sto     r0, FLAGS!r1
        sub     r1, #1
        jpge    r1, fillloop

        ;;      Print first prime, 2
        ld      r7,  #2 + ord('0')
        out     r7, CONOUT
        PRINTNL (r1)

        ;; Iterate over numbers 3 .. MAXINT using r7 as loop counter, i
        ld      r7, #3
loop1:
        sto     r7, RQ          ; find word address and bit index for 'i' in flags
        ld      r3, ZERO
        ld      r1, #48         ; eff. 48 flags per word (only flag odd numbers)
        div     r3, r1          ; (r, q ) = <r3,Q>/r1
        ld      r1, RQ          ; get word address in r1 (before lsr which corrupts RQ!)
        lsr     r3, #1          ; divide remainder by 2 (odd flags stored only)

        ld      r2, FLAGS!r1    ; get flag word

        ld      r1, #1          ; generate bit mask
        asl     r1, ZERO!r3     ; = 1 << (remainder//2)

        and     r2, r1          ; mask bit
        jpnz    r2, nexti       ; flag is set so skip to next integer

                                ; Call print dec routine with r7=n
        ld      r1, #printnl    ; and return to set flags as multiples of this n
        sto     r1, RLINK
        jpz     r0, printdec
printnl:
        PRINTNL( r1 )
        ;; now set all multiples of n in the table until we reach MAXINT
        ld      r6, r7
        ld      r5, #1          ; constant 1 for checking even/odd
loop2:
        add     r6, r7          ; next multiple
        ld      r1, r6
        and     r1, r5
        jpz     r1, loop2

        ld      r1, r6
        sub     r1, MAXINT
        jpge    r1, nexti       ; bail out if > MAXINT and look at next int
        sto     r6, RQ          ; (rem, quo) = (n%48,n//48)
        ld      r3, ZERO
        ld      r1, #48
        div     r3, r1
        ld      r2, RQ          ; r3 is rem//2, r2 is quotient (save Q before lsr corrupts it!)
        ld      r1, r2          ; check for out of bounds
        sub     r1, #TABLESZ
        jpge    r1, nexti
        lsr     r3, #1          ; divide remainder by 2 (only storing odds)
        ld      r1, FLAGS!r2    ; get FLAG word
        ld      r4, #1          ; generate bit mask
        asl     r4, ZERO!r3
        or      r1, r4          ; set the mask bit
        sto     r1, FLAGS!r2    ; and write back
        jpz     r0, loop2       ; set next flag

nexti:
        add     r7, #2          ; increment loop counter by two (skip even nums)
        ld      r1, r7
        sub     r1, MAXINT      ; less than MAXINT ?
        jplt    r1, loop1


        halt

;; printdec routine
;; r7 holds number to be printed (preserved)
;; r1,2,3,4 used as temporary stores
printdec:
        ld      r4, r7          ; n
        ld      r3, #1          ; suppress leading zeroes
        ld      r2, MAXDIV      ; get first divisor into r2 = 1,000,000
pd_loop:
        ld      r1, r2          ; ensure we always print the last digit in case
        sub     r1, #1          ; n=0
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
FLAGS:  WORD	0
