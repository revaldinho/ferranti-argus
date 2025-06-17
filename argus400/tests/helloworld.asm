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

        MACRO HALT()
@L1:    jze r0, @L1
        ENDMACRO

        ORG     0x1020
main:
        ldc     r1, L1
        sto     r1, RLINK
        ldc     r7, banner
        jnz     r7, sprint

L1:
        HALT()

        ;; SPRINT
        ;; print packed byte string pointed to by r7
        ;; uses temporary registers r1,2,3,4
sprint:
        ldx     r3, r7
sprint1:
        ldc     r2, 3
        ldx     r4, 0!r3
sprint2:
        ldx     r1, r4
        and     r1, bytemask
        jze     r1, sprint_exit
        out     r1, CONOUT
        sra     r4, 8
        sbc     r2, 1
        jnz     r2, sprint2
        adc     r3, 1
        jze     r2, sprint1
sprint_exit:
        jcs     RLINK           ; return

banner: BSTRING "Hello, World!"
bytemask:
        WORD    0x00FF
