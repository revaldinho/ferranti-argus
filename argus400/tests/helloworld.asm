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


        ORG     0x1020
main:
        ld      r1, #L1
        sto     r1, RLINK
        ld      r7, #banner
        jpnz    r7, sprint

L1:
        halt

        ;; SPRINT
        ;; print packed byte string pointed to by r7
        ;; uses temporary registers r1,2,3,4
sprint:
        ld      r3, r7
sprint1:
        ld      r2, #3
        ld      r4, 0!r3
sprint2:
        ld      r1, r4
        and     r1, bytemask
        jpz     r1, sprint_exit
        out     r1, CONOUT
        asr     r4, #8
        sub     r2, #1
        jpnz    r2, sprint2
        add     r3, #1
        jpz     r2, sprint1
sprint_exit:
        jp      RLINK           ; return

banner: BSTRING "Hello, World!"
bytemask:
        WORD    0x00FF
