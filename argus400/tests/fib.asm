

	;;  Standard definitions
	EQU	ZERO   , 0x0000	; all-zero's register at 0x0000 (use as literal or address)
	EQU	RROUND , 0x0001	; round register
	EQU	RQ     , 0x0002	; Q register
	EQU	RCARRY , 0x0003	; carry register
	EQU	RHANDSW, 0x0004	; hand switches
	EQU	RIN    , 0x1000 ; input register
	EQU	RLINK  , 0x1008 ; link register
	EQU	RINT   , 0x1010 ; 1st register of interrupt program


	ORG	0x1020		; Place program in 1st block of core store above register locations
START:
        ld	r1, #ZERO
	ld	r2, #1
	ld	r3, #5
	ld	r4, #1
LOOP:	
	add	r1, r2
	add 	r2, r1
	sub 	r3, r4
	jpz	r3, END
	jpz	r0, LOOP
END:	
	halt
