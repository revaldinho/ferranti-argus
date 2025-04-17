
        MACRO  DOUBLE ( _R_ )
                add _R_, _R_
        ENDMACRO

START:

        WORD    0x1, 0x2, 0x3
L1:     ld      r3, 0x1234!r1
        ld      r3, 0x123!r1
        add     r3, 1 + 2 *(9-4)
        sub     r3, START+4!r2
        or      r3, 0x1234!r1
        and     r1, DATA
        and     r1, DATA+1

        mul     r1, r2

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
