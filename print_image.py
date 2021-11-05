import srp350
from PIL import Image
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--printer", default="/dev/usb/lp0", help="Printer device file")
parser.add_argument("--no-cut", action="store_true")
parser.add_argument("image", help="Path to image")
args = parser.parse_args()

printer = srp350.SRP350(args.printer)
printer.initialize_printer()

printer.print_raster_bit_image(srp350.BIT_IMAGE_MODE_NORMAL, *printer.generate_image_data(Image.open(args.image)))

if(not args.no_cut):
    printer.cut_paper(srp350.CUT_MODE_FEED_AND_CUT, 10)

printer.send()

printer.close()