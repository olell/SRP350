import srp350

printer = srp350.SRP350("/dev/usb/lp0")
printer.initialize_printer()

printer.emphasize_mode(1)
printer.underline_mode(srp350.UNDERLINE_DOUBLE_DOT)
printer.select_character_size(printer.gen_character_size(1, 1))
printer.println("Codepage dump\n")
printer.select_character_size(printer.gen_character_size(0, 0))
printer.underline_mode(0)
printer.println("  0 1 2 3 4 5 6 7 8 9 A B C D E F")
printer.emphasize_mode(0)

for i in range(0x00, 0x10):
    printer.emphasize_mode(1)
    printer._handle_payload([0x0a, ord(hex(i)[-1].upper()), 0x20])
    printer.emphasize_mode(0)
    output = []
    for j in range(0x00, 0x10):

        chr = (i << 4) | j
        if (chr < 0x20): chr = ord(".")

        output.extend([chr, ord(" ")])
        printer._handle_payload(output)
        output = []

printer.println("   ")

printer.cut_paper(srp350.CUT_MODE_FEED_AND_CUT, 40)
printer.send()
printer.close()