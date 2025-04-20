

	;;  Standard definitions
	EQU	ZERO   , 0x0000	; all-zero's register at 0x0000 (use as literal or address)
	EQU	RROUND , 0x0001	; round register
	EQU	RQ     , 0x0002	; Q register
	EQU	RCARRY , 0x0003	; carry register
	EQU	RHANDSW, 0x0004	; hand switches
	EQU	RIN    , 0x1000 ; input register
	EQU	RLINK  , 0x1008 ; link register
	EQU	RINT   , 0x1010 ; 1st register of interrupt program


	MACRO  NEG ( _R_ )
	# Negate register R by subtracting it from zero and writing back using
	# its memory location rather than register number
	       msub _R_ , ZERO
	ENDMACRO

	MACRO  ASL ( _R_ , _N_ )
		asl _R_, _N_
	ENDMACRO

        MACRO  DOUBLE ( _R_ )
                ASL ( _R_, 1 )
        ENDMACRO

	ORG	0x1020		; Place program in 1st block of core store above register locations
START:

        WORD    0x1, 0x2, 0x3, 0x4, 0x5
L1:     ld      r3, 0x1234!r1
        ld      r3, 0x123!r1
        add     r3, 1 + 2 *(9-4)
        sub     r3, START+4!r2
        or      r3, 0x1234!r1
        and     r1, DATA
        and     r1, DATA+1
        mul     r1, r2
        NEG     ( r4 )
        sto     0x453, r1
        DOUBLE  ( r5 )
        jp      END
        jplt    r4, END*2
        jpge    r4, END+END
        jpnz    r4, DATA+1
        ldc     r0, 0x33
        ld      r0, #0x33
        addc    r7, 0x55
        asr     r3, 0x12
        rol     r5, 0x23
DATA:   WORD    0x5, 0x6
        BYTE    0x1, 0x2, 0x3, 0x4, 0x5, 0x6
        PBSTRING "Hello, World"
        BSTRING "Hello, World"
END:
