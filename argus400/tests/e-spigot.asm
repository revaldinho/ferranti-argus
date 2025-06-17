        ;;
        ;; Program to generate E using the Spigot Algorithm from
        ;;
        ;; http//web.archive.org/web/20110716080608/http//www.mathpropress.com/stan/bibliography/spigot.pdf
        ;;
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

        EQU     DIGITS,   256      ; Digits to be printed
        EQU     COLS,     DIGITS+2 ; Needs a few more columns than digits to avoid occasional errors in last digit or few

        MACRO HALT()
          out r0, 0x0000
        ENDMACRO



        ORG     0x1020          ; Place program in 1st block of core store above register locations
start:
        ;; trivial banner + first digit and decimal point
        ldc     r1, ZERO
L0:     ldx     r7, banner!r1
        jze     r7, L7
        out     r7, CONOUT
        adc     r1,1
        jze     r0, L0

L7:                             ; Initialise remainder array
        ldc     r2, 1          ; r2=const 1
        ldc     r3, COLS-1     ; loop counter i starts at index = RHS
L1:     sto     r2, remain!r3   ; store remainder value to pointer
        sbc     r3, 1          ; decrement loop counter
        jnz     r3, L1          ; loop again if not zero
        ldc     r1, ZERO
        sto     r1, remain      ; write 0 into first entry

        ldc     r7, DIGITS
L2:     ldc     r3, COLS       ; set up r3=i=COLS
        ldc     r6, 0          ; zero Q to start with

L3:     ldx     r1, remain!r3   ; r1 = remain[r3]
        ldx     r2, r3
        adc     r2, 1          ; r2= (i+1)
        ldc     r4, 10
        mpy     r1, r4          ; <r1,RQ> = remain[i]*10
        add     r6, RQ          ; use r6 temporarily as N = Q + remain[i]*10 (taking LSW from result, discarding MSW)
        sto     r6, RQ          ; put result back into LSW of dividend
        ldc     r1, ZERO       ; zero MSW of divident
        div     r1, r2          ; divide by (i+1)
        sto     r1, remain!r3   ; store new remainder
        ldx     r6, RQ          ; get new quotient

        sbc     r3, 1
        jge     r3, L3

        ldx     r1, r6          ; print Q as ASCII digit
        adc     r1, 48
        out     r1, CONOUT

        sbc     r7, 1
        jnz     r7, L2

        HALT()

banner: STRING "OK 2."                 ;; Banner and first digit and dp
        WORD 0
remain: WORD 2                         ;; Array space for remainder date
