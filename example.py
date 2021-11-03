from srp350 import Printer

p = Printer("/dev/usb/lp0")

# not required but resets printer to default values
p.initialize_printer()

p.define_downloaded_bit_image(20, 20, [49, 50] * (20 * 20))
p.print_downloaded_bit_image(p.BIT_IMAGE_MODE_QUADRUPLE)

exit(0)
# print simple text
p.println("Hello World, this is a test :)")

# underline mode
p.underline_mode(p.UNDERLINE_SINGLE_DOT)
p.println("Underlined single dot")
p.underline_mode(p.UNDERLINE_DOUBLE_DOT)
p.println("Underlines double dot")
p.underline_mode(p.UNDERLINE_OFF)

# emphasize mode
p.emphasize_mode(1)
p.println("Emphasize mode on")
p.emphasize_mode(0)

# double strike mode
p.double_strike_mode(1)
p.println("Double strike mode")
p.double_strike_mode(0)

# double width/height mode
p.select_print_mode(p.gen_print_mode(0, 0, 1, 0, 0))
p.println("Double height mode")
p.select_print_mode(p.gen_print_mode(0, 0, 0, 1, 0))
p.println("Double width mode")
p.select_print_mode(p.gen_print_mode(0, 0, 1, 1, 0))
p.println("Double hg+wd mode")
p.select_print_mode(p.gen_print_mode(0, 0, 0, 0, 0))

# barcode priting
p.set_barcode_width(1)
p.set_barcode_height(100)
p.select_hri_printing_position(p.HRI_POS_BELOW)
p.print_barcode(0, p.BARCODE_SYSTEM_EAN13, *list("4388860567386".encode("ASCII")))

p.print_and_feed_lines(5)

p.print_barcode(0, p.BARCODE_SYSTEM_EAN8, *list("41057759".encode("ASCII")))
p.print_barcode(0, p.BARCODE_SYSTEM_EAN8, *list("41057759".encode("ASCII")))

p.println("\nlol")

# paper cutting
p.cut_paper(p.CUT_MODE_FEED_AND_CUT, 40)

p.send()
p.close()