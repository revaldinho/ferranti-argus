        ;;
        ;; Program to generate pi using the Spigot Algorithm from
        ;;
        ;; http:web.archive.org/web/20110716080608/http: www.mathpropress.com/stan/bibliography/spigot.pdf
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
        EQU     CONOUT , 0x0010

        EQU     DIGITS,   31     ; Digits to be printed
        EQU     COLS,     1+DIGITS*10//3  ; Needs a few more columns than digits to avoid occasional errors in last digit or few

        ORG     0x1020          ; Place program in 1st block of core store above register locations

        ;; trivial banner + first digit and decimal point
        ld      r1, #ZERO
LBANNER:
	ld      r2, banner!r1
        jpz     r2, LINIT0
        out     r2, CONOUT
        add     r1,#1
        jpz     r0, LBANNER
LINIT0:
        ;; Fill all columns with const 2 - initial remainder
	ld      r3, #COLS-1
	ld      r2, #2
LINIT1:
	sto	r2, remain!r3
	sub	r3, #1
	jpge	r3, LINIT1
	;; main body
	;; r1 = tmp variable
	;; r2 = tmp variable
	;; r3 = i index/inner loop counter
	;; r4 = constant # 10
	;; r5 = digit outer loop counter
	;; r6 = q (and n)
        ;; r7 = c
	ld 	r7, #ZERO 	; c = 0
	ld 	r5, #DIGITS-1 	; outer loop counter
	ld 	r4, #10 	; constant
L0:				; OUTER LOOP
	ld 	r6, #0		; zero q
	ld 	r3, #COLS -1 	; start at far end of remainders

L1:				; INNER LOOP
	ld	r1, remain!r3	; tmp = remain[i]
	mul	r1, r4		; <r1,RQ> = r1 * 10
	add	r6, RQ		; add result LSW to q, q = q+remain[i]*10
	ld	r1, r3
	asl 	r1, 1		; tmp = i*2
	sub	r1, #1		; tmp = i*2-1
	sto	r6, RQ		; <R6,RQ>=<0,q>
	ld	r6, #ZERO
	div	r6, r1		;
	sto	r6, remain!r3 	; REM = q % ((i*2)-1)
	ld	r6, RQ      	; q = RQ = q//((i*2)-1)

	sub	r3, #1		; more columns?
	jpz	r3, L2		; Break out of loop if i=0 

        mul     r6, r3          ; multiply q * i
        ld      r6, RQ          ; get LSW only
        jpz     r0, L1		; Next i (END INNER LOOP)

L2:
	sto	r6, RQ		; setup q//10
	ld	r1, #ZERO
	div	r1, r4
	ld	r2, RQ
	add	r2, r7 		; result (new digit) = c+ Q//10
	ld	r7, r1  	; c = q % 10

	add	r2, #48		; make digit ASCII
	out	r2, CONOUT	; send it out (no error correction ... yet)

	sub	r5, #1		; more digits ?
	jpge	r5, L0		; END OUTER LOOP

	halt


        ORG     0x1100

banner: STRING "OK "                 ;; Banner and first digit and dp
        WORD 0
remain: WORD 2                         ;; Array space for remainder date
        WORD 2
