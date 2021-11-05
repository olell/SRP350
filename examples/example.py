from PIL import Image
import srp350

p = srp350.SRP350("/dev/usb/lp0")

# not required but resets printer to default values
p.initialize_printer()

# print simple text
p.println("Hello World, this is a test :)")

# underline mode
p.underline_mode(srp350.UNDERLINE_SINGLE_DOT)
p.println("Underlined single dot")
p.underline_mode(srp350.UNDERLINE_DOUBLE_DOT)
p.println("Underlines double dot")
p.underline_mode(srp350.UNDERLINE_OFF)

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

# image printing
p.print_raster_bit_image(srp350.BIT_IMAGE_MODE_NORMAL, *p.generate_image_data(Image.open("monalisa.jpg")))

# barcode priting
p.set_barcode_width(1)
p.set_barcode_height(100)
p.select_hri_printing_position(srp350.HRI_POS_BELOW)
p.print_barcode(0, srp350.BARCODE_SYSTEM_A_EAN13, "4388860567386")

p.print_and_feed_lines(3)

p.print_barcode(0, srp350.BARCODE_SYSTEM_A_EAN8, "41057759")

p.inverse_printing_mode(1)
p.select_character_size(p.gen_character_size(7, 7))
p.println("ROFL!")
p.select_character_font(srp350.CHAR_FONT_B)
p.println("YOLO!")
p.inverse_printing_mode(0)
p.select_character_font(srp350.CHAR_FONT_A)

# paper cutting
p.cut_paper(srp350.CUT_MODE_FEED_AND_CUT, 40)

p.send()
p.close()