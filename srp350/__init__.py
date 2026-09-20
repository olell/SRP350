__version__ = "0.2.0"
__author__ = "Ole Lange"

import os
import select
import socket
import sys

from PIL import Image, ImageOps

IMAGE_MODE_8DOT_SINGLE = 0
IMAGE_MODE_8DOT_DOUBLE = 1
IMAGE_MODE_24DOT_SINGLE = 32
IMAGE_MODE_24DOT_DOUBLE = 33

UNDERLINE_OFF = 48
UNDERLINE_SINGLE_DOT = 49
UNDERLINE_DOUBLE_DOT = 50

CHAR_FONT_A = 48
CHAR_FONT_B = 49

CHARSET_USA = 0
CHARSET_FRANCE = 1
CHARSET_GERMANY = 2
CHARSET_UK = 3
CHARSET_DENMARK_1 = 4
CHARSET_SWEDEN = 5
CHARSET_ITALY = 6
CHARSET_SPAIN = 7
CHARSET_NORWAY = 8
CHARSET_DENMARK_2 = 10

PRINT_DIRECTION_LEFT_TO_RIGHT = 48
PRINT_DIRECTION_BOTTOM_TO_TOP = 49
PRINT_DIRECTION_RIGHT_TO_LEFT = 50
PRINT_DIRECTION_TOP_TO_BOTTOM = 51

CLOCKWISE_ROTATION_MODE_OFF = 48
CLOCKWISE_ROTATION_MODE_ON = 49

BIT_IMAGE_MODE_NORMAL = 48
BIT_IMAGE_MODE_DOUBLE_WIDTH = 49
BIT_IMAGE_MODE_DOUBLE_HEIGHT = 50
BIT_IMAGE_MODE_QUADRUPLE = 51

HRI_POS_NOT_PRINTED = 48
HRI_POS_ABOVE = 49
HRI_POS_BELOW = 50
HRI_POS_ABOVE_AND_BELOW = 51

CUT_MODE_DEFAULT = 49
CUT_MODE_FEED_AND_CUT = 66

HRI_FONT_A = 48
HRI_FONT_B = 49

BARCODE_SYSTEM_A_UPC_A = 0
BARCODE_SYSTEM_A_UPC_E = 1
BARCODE_SYSTEM_A_JAN13 = BARCODE_SYSTEM_A_EAN13 = 2
BARCODE_SYSTEM_A_JAN8 = BARCODE_SYSTEM_A_EAN8 = 3
BARCODE_SYSTEM_A_CODE39 = 4
BARCODE_SYSTEM_A_ITF = 5
BARCODE_SYSTEM_A_CODABAR = 6
BARCODE_SYSTEM_B_UPC_A = 65
BARCODE_SYSTEM_B_UPC_E = 66
BARCODE_SYSTEM_B_JAN13 = BARCODE_SYSTEM_B_EAN13 = 67
BARCODE_SYSTEM_B_JAN8 = BARCODE_SYSTEM_B_EAN8 = 68
BARCODE_SYSTEM_B_CODE39 = 69
BARCODE_SYSTEM_B_ITF = 70
BARCODE_SYSTEM_B_CODABAR = 71
BARCODE_SYSTEM_B_CODE93 = 72
BARCODE_SYSTEM_B_CODE128 = 73

DEBUG_MODE_OFF = 0
DEBUG_MODE_HEXDUMP = 1
DEBUG_MODE_VISUAL = 2

ALIGN_LEFT = 0
ALIGN_CENTER = 1
ALIGN_RIGHT = 2

CODEPAGE_PC437 = 0
CODEPAGE_KATAKANA = 1
CODEPAGE_PC850 = 2
CODEPAGE_PC860 = 3
CODEPAGE_PC863 = 4
CODEPAGE_PC865 = 5
CODEPAGE_WPC1252 = 16
CODEPAGE_PC866 = 17
CODEPAGE_PC852 = 18
CODEPAGE_PC858 = 19

QR_MODEL_1 = 49
QR_MODEL_2 = 50
QR_EC_LOW = 48
QR_EC_MEDIUM = 49
QR_EC_QUARTILE = 50
QR_EC_HIGH = 51

STATUS_PRINTER = 1
STATUS_OFFLINE = 2
STATUS_ERROR = 3
STATUS_PAPER_ROLL = 4

# The print head is 512 dots wide. Font A is 12 dots per character, font B is 9.
PRINT_WIDTH_DOTS = 512
CHARS_PER_LINE_FONT_A = 42
CHARS_PER_LINE_FONT_B = 56


class SRP350:
    def __init__(
        self,
        device=None,
        debug_mode=DEBUG_MODE_OFF,
        ip=None,
        port=9100,
        timeout=10.0,
    ):
        """Opens a connection to the printer.

        Give `device` to write to a device file, for example /dev/usb/lp0.
        Give `ip` (and `port`, default 9100) to write to a network printer over TCP.
        `timeout` is the socket timeout in seconds. Give None to block forever.
        """
        if (device is None) == (ip is None):
            raise ValueError("Give either device or ip, not both and not none")

        self.device = device
        self.ip = ip
        self.port = port
        self.debug_mode = debug_mode
        self.timeout = timeout

        # Visual debug mode reads these before initialize_printer() runs.
        self._debug_emphasize_mode = False
        self._debug_underline = False

        if ip is not None:
            self.socket = socket.create_connection((ip, port), timeout=timeout)
            self.socket.settimeout(timeout)
            self.fd = None
        else:
            self.socket = None
            self.fd = os.open(device, os.O_RDWR)

        self.data = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def send(self):
        """Sends the current buffer (self.data) and clears it"""
        payload = bytearray(self.data)
        if self.socket is not None:
            self.socket.sendall(payload)
        else:
            os.write(self.fd, payload)
        self.data = []

    def close(self):
        """Closes connection to the device"""
        if self.socket is not None:
            self.socket.close()
        else:
            os.close(self.fd)

    def read_status(self, n, timeout=1.0):
        """Asks the printer for a status byte and reads the answer.

        n selects the status, see `real_time_status_transmission`.
        The buffer goes out first, because the printer answers in order.
        Returns the status byte, or None if the printer stays quiet.
        """
        self.real_time_status_transmission(n)
        self.send()

        if self.socket is not None:
            old_timeout = self.socket.gettimeout()
            self.socket.settimeout(timeout)
            try:
                answer = self.socket.recv(1)
            except OSError:
                return None
            finally:
                self.socket.settimeout(old_timeout)
            return answer[0] if answer else None

        # os.read on a device file blocks, so wait for data first.
        readable, _, _ = select.select([self.fd], [], [], timeout)
        if not readable:
            return None
        answer = os.read(self.fd, 1)
        return answer[0] if answer else None

    def paper_status(self, timeout=1.0):
        """Reads the paper roll sensor.

        Returns a dict with `near_end` and `out_of_paper`, or None if the
        printer does not answer.
        """
        status = self.read_status(STATUS_PAPER_ROLL, timeout=timeout)
        if status is None:
            return None
        return {
            "near_end": bool(status & 0b00001100),
            "out_of_paper": bool(status & 0b01100000),
        }

    def printer_online(self, timeout=1.0):
        """Returns True if the printer is on-line, or None if it does not answer.

        The printer goes off-line when the cover is open or the paper runs out.
        """
        status = self.read_status(STATUS_OFFLINE, timeout=timeout)
        if status is None:
            return None
        return not bool(status & 0b00001000)

    def _handle_payload(self, payload):
        """Handles the given payload"""
        if self.debug_mode == DEBUG_MODE_HEXDUMP:
            debug_str = ""
            ll = 0
            for d in payload:
                if d < 0 or d > 255:
                    debug_str += f"{d:02x}!"
                else:
                    debug_str += f"{d:02x} "
                ll += 3
                if ll >= 189:
                    debug_str += "\n"
                    ll = 0
            print(debug_str)
        self.data.extend(payload)
        return payload

    def print(self, text, encoding="cp437", errors="replace"):
        """Prints text. Characters the codepage does not hold become '?'."""
        if self.debug_mode == DEBUG_MODE_VISUAL:
            if self._debug_underline:
                sys.stdout.write("\u001b[4m")
            if self._debug_emphasize_mode:
                sys.stdout.write("\u001b[1m")
            sys.stdout.write(text + "\u001b[0m")
        return self._handle_payload(list(text.encode(encoding, errors)))

    def println(self, text, encoding="cp437", errors="replace"):
        return self.print(text + "\n", encoding=encoding, errors=errors)

    ## commands refering to https://www.jarltech.com/ger_new/new/support/cd/srp350-esc_commands.pdf

    def horizontal_tab(self):
        """HT
        Horizontal Tab
        Moves the print position to the next horizontal tab position."""
        if self.debug_mode == DEBUG_MODE_VISUAL:
            sys.stdout.write("\t")
        payload = [0x09]
        return self._handle_payload(payload)

    def line_feed(self):
        """LF
        Print and line feed
        Prints the data in the print buffer and feeds one line based on the currentline spacing."""
        if self.debug_mode == DEBUG_MODE_VISUAL:
            sys.stdout.write("\n")
        payload = [0x0A]
        return self._handle_payload(payload)

    def print_and_return_to_standard_mode(self):
        """FF
        Print and return to standard mode in page mode
        Prints the data in the print buffer collectively and returns to standard mode."""
        payload = [0x0C]
        return self._handle_payload(payload)

    def carriage_return(self):
        """CR
        Print and carriage return
        When automatic line feed is enabled, this command functions the same as LF;when automatic line feed is
        disabled, this command is ignored."""
        if self.debug_mode == DEBUG_MODE_VISUAL:
            sys.stdout.write("\r")
        payload = [0x0D]
        return self._handle_payload(payload)

    def cancel_print_data(self):
        """CAN
        Cancel print data in page mode.
        In page mode, deletes all the print data in the current printable area."""
        payload = [0x18]
        return self._handle_payload(payload)

    def real_time_status_transmission(self, n):
        """OLE EOT n
        Real-time status transmission
        Transmits the selected printer status specified by n in real time, according to the following parameters:

        n = 1 : Transmit printer status.
        n = 2 : Transmit off-line status.
        n = 3 : Transmit error status.
        n = 4 : Transmit paper roll sensor status."""
        payload = [0x10, 0x04, n]
        return self._handle_payload(payload)

    def real_time_request(self, n):
        """DLE ENQ n
        Real-time request to printer.
        Recover from an error and restart printing from the line where the error occurred

        1 <= n <= 2"""
        payload = [0x10, 0x05, n]
        return self._handle_payload(payload)

    def print_data_in_page_mode(self):
        """ESC FF
        Print data in page mode.
        In page mode, prints all buffered data in the printing area collectively."""
        payload = [0x1B, 0x0C]
        return self._handle_payload(payload)

    def set_right_side_character_spacing(self, n):
        """ESC SP n
        Set right-side character spacing
        Sets the character spacing for the right side of the character to[n x horizontal or vertical motion units].

        0 <= n <= 255"""
        payload = [0x1B, 0x20, n]
        return self._handle_payload(payload)

    def select_print_mode(self, n):
        """ESC ! n
        Select print modes.
        Selects print mode(s) using n as follows:
        (or generate using `gen_print_mode`)

        | bit | on/off | function              |
        |-----|--------|-----------------------|
        |   0 | off    | Char font A (12 x 24) |
        |   0 | on     | Char font B (9 x 17)  |
        |   1 | on/off | Undefined             |
        |   2 | on/off | Undefined             |
        |   3 | on/off | Emphasized mode       |
        |   4 | on/off | Double height mode    |
        |   5 | on/off | Double width mode     |
        |   6 | on/off | Undefined             |
        |   7 | on/off | Underline mode        |"""
        payload = [0x1B, 0x21, n]
        return self._handle_payload(payload)

    def set_absolute_print_position(self, nL, nH):
        """ESC $ nL nH
        Set the distance from the beginning of the line to the position at whichsubsequent characters are to be printed.
        x   The distance from the beginning of the line to the print position is
            [(nL + nH x 256) x (vertical or horizontal motion unit)] inches."""
        payload = [0x1B, 0x24, nL, nH]
        return self._handle_payload(payload)

    def select_cancel_user_defined_character_set(self, n):
        """ESC % n
        Selects or cancels the user-defined character set.
        x  When the LSB of n is 0, the user-defined character set is canceled.
        x  When the LSB of n is 1, the user-defined character set is selected."""
        payload = [0x1B, 0x25, n]
        return self._handle_payload(payload)

    def define_user_defined_characters(self, *args):
        """ESC & y c1 c2 [x1 d1...d(y x x1)]...[xk d1 ...d(y x xk)]
        Define user-defined characters"""
        # TODO!
        raise NotImplementedError("This command is not implemented yet")

    def select_bit_image_mode(self, m, nL, nH, d):
        """ESC *  m  nL  nH  d1...dk
        Select bit-image mode.
        Selects a bit-image mode using m for the number of dots specified by nL and nH, as follows:

        | m  | mode                 | v dots | v dot densitiy | h dot density | h num of data       |
        |----|----------------------|--------|----------------|---------------|---------------------|
        |  0 | 8 dot single density |      8 | 60 DPI         | 90 DPI        | nL + nH x 256       |
        |  1 | 8 dot double density |      8 | 60 DPI         | 180 DPI       | nL + nH x 256       |
        | 32 | 24dot single density |     24 | 180 DPI        | 90 DPI        | (nL + nH x 256) x 3 |
        | 33 | 24dot double density |     24 | 180 DPI        | 180 DPI       | (nL + nH x 256) x 3 |"""
        payload = [0x1B, 0x2A, m, nL, nH] + d
        self._handle_payload(payload)

    def underline_mode(self, n):
        """ESC - n
        Turn underline mode on/off.
        Turns underline mode on or off, based on the following values of n:

        |   n | dec | function     |
        |-----|-----|--------------|
        | '0' |  48 | turns off    |
        | '1' |  49 | 1 dot thick  |
        | '2' |  50 | 2 dots thick |"""
        self._debug_underline = n != UNDERLINE_OFF
        payload = [0x1B, 0x2D, n]
        return self._handle_payload(payload)

    def select_default_line_spacing(self):
        """ESC 2
        Selects 1/6-inch line (approximately 4.23mm) spacing."""
        payload = [0x1B, 0x32]
        return self._handle_payload(payload)

    def set_line_spacing(self, n):
        """ESC 3 n
        Set line spacing.
        Sets the line  spacing to [n x vertical or horizontal motion unit] inches."""
        payload = [0x1B, 0x33, n]
        return self._handle_payload(payload)

    def set_peripheral_device(self, n):
        """ESC = n
        Set peripheral device.
        Selects device to which host computer sends data, using n as follows:
        x    n = 0 -> printer disabled
        x    n = 1 -> printer enabled"""
        payload = [0x1B, 0x3D, n]
        return self._handle_payload(payload)

    def cancel_user_defined_characters(self, n):
        """ESC ? n
        Cancel user-defined characters.
        32 < n < 126"""
        payload = [0x1B, 0x3F, n]
        return self._handle_payload(payload)

    def initialize_printer(self):
        """ESC @
        Initialize printer.
        Clears the data in the print buffer and resets the printer mode to the mode that was in effect when the power
        was turned on"""
        self._debug_emphasize_mode = False
        self._debug_underline = False
        payload = [0x1B, 0x40]
        return self._handle_payload(payload)

    def set_horizontal_tab_position(self, *n):
        """ESC D n1...nk NUL
        Set horizontal tab positions.
        Sets horizontal tab position.
        * n specifies the column number for setting a horizontal tab position from thebeginning of the line.
        * k indicates the total number of horizontal tab positions to be set."""
        payload = [0x1B, 0x44, *n, 0x00]
        return self._handle_payload(payload)

    def emphasize_mode(self, n):
        """ESC E n
        Turn emphasized mode on/off.
        Turns emphasized mode on or off.When the LSB is 0, emphasized mode is turned off."""
        self._debug_emphasize_mode = n == 1
        payload = [0x1B, 0x45, n]
        return self._handle_payload(payload)

    def double_strike_mode(self, n):
        """ESC G n
        Turn on/off double-strike mode.
        Turns double-strike mode on or off.
        *  When the LSB is 0, double-strike mode is turned off.
        *  When the LSB is 1, double-strike mode is turned on."""
        self._debug_emphasize_mode = n == 1
        payload = [0x1B, 0x47, n]
        return self._handle_payload(payload)

    def print_and_feed_paper(self, n):
        """ESC J n
        Print and feed paper.
        Prints the data in the print buffer and feeds the paper [n x vertical or horizontal motion unit] inches, unit.
        0 <= n <= 255"""
        payload = [0x1B, 0x4A, n]
        return self._handle_payload(payload)

    def select_page_mode(self):
        """ESC L
        Select page mode
        Switches from standard mode to page mode"""
        payload = [0x1B, 0x4C]
        return self._handle_payload(payload)

    def select_character_font(self, n):
        """ESC M n
        Select character font"""
        payload = [0x1B, 0x4D, n]
        return self._handle_payload(payload)

    def select_international_charset(self, n):
        """ESC R n
        Select an international character set"""
        payload = [0x1B, 0x52, n]
        return self._handle_payload(payload)

    def select_standard_mode(self):
        """ESC S
        Select standard mode
        Switches from page mode to standard mode"""
        payload = [0x1B, 0x53]
        return self._handle_payload(payload)

    def select_print_direction(self, n):
        """ESC T n
        Select print direction in page mode
        Selects the print direction and starting position in page mode.
        n specifies the print direction and starting position as follows:

        | n | dec | print direction | starting position |
        |---|-----|-----------------|-------------------|
        | 0 |  48 | Left to right   | Upper left        |
        | 1 |  49 | Bottom to top   | Lower left        |
        | 2 |  50 | Right to left   | Lower right       |
        | 3 |  51 | Top to bottom   | Upper right       |"""
        payload = [0x1B, 0x54, n]
        return self._handle_payload(payload)

    def clockwise_rotation_mode(self, n):
        """ESC V n
        Turn 90° clockwise rotation mode on/off"""
        payload = [0x1B, 0x56, n]
        return self._handle_payload(payload)

    def set_printing_area(self, xL, xH, yL, yH, dxL, dxH, dyL, dyH):
        """ESC W xL xH yL yH dxL dxH dyL dyH"""
        # TODO
        raise NotImplementedError("This command is not implemented yet")

    def set_relative_print_position(self, nL, nH):
        r"""ESC \ nL nH
        Set relative print position
        Set the print starting position based on the current position by using the horizontal or
        vertical motion unit.
        * This command sets the distance from the current position to [(nL + nH x 256) x horizontal or vertical motion unit]"""
        payload = [0x1B, 0x5C, nL, nH]
        return self._handle_payload(payload)

    def select_justification(self, n):
        """ESC a n
        Select justification
        Aligns the following lines. Only works at the start of a line.

        n = 0: left, n = 1: center, n = 2: right"""
        payload = [0x1B, 0x61, n]
        return self._handle_payload(payload)

    # (8-11)
    # TODO ESC c 3 n
    # TODO ESC c 4 n

    # (8-12)
    # TODO ESC c 5 n

    def print_and_feed_lines(self, n):
        """ESC d n
        Print and feed n lines
        Prints the data in the print buffer and feeds n lines."""
        if self.debug_mode == DEBUG_MODE_VISUAL:
            sys.stdout.write("\n" * n)
        payload = [0x1B, 0x64, n]
        return self._handle_payload(payload)

    def open_cash_drawer(self, m=0, t1=25, t2=250):
        """ESC p m t1 t2
        Generate pulse
        Sends a pulse to the drawer kick connector, m selects the pin.
        t1 is the on time and t2 the off time, both in 2 ms steps."""
        payload = [0x1B, 0x70, m, t1, t2]
        return self._handle_payload(payload)

    def select_character_code_table(self, n):
        """ESC t n
        Select character code table
        Tells the printer which codepage the following bytes use. It must match
        the `encoding` given to `print`, or the text prints as the wrong glyphs.

        See the CODEPAGE_* constants."""
        payload = [0x1B, 0x74, n]
        return self._handle_payload(payload)

    # (8-13)
    # TODO ESC { n
    # TODO FS p n m

    def define_nv_bit_image(self, n, d):
        """FS q n [xL xH yLyH d1 ...dk]1 ...[xL xH yL yH d1...dk]n
        Define NV bit image
        Define the NV bit image specified by n.
        * n specifies the number of the defined NV bit image.
        * xL, xH specifies (xL + xH x 256) x 8 dots in the horizontal direction for the NV bit image you are defining.
        * yL, yH specifies (yL + yH x 256) x 8 dots in the vertical direction for the NV bit image you are defining
        """
        payload = [0x1C, 0x71, n] + d
        return self._handle_payload(payload)

    def select_character_size(self, n):
        """GS ! n
        Select character size.
        Selects the character height using bits 0 to 2 and selects the character width using bits 4 to 7"""
        payload = [0x1D, 0x21, n]
        return self._handle_payload(payload)

    # (8-14)
    # TODO GS $ nL nH
    def define_downloaded_bit_image(self, x, y, d):
        """GS * x y d1...d(x x y x 8)
        Define downloaded bit image
        Defines a downloaded bit image using the dots specified by x and y.
        * x: width
        * y: height
        1 <= x <= 255
        1 <= y <= 48
        x x y <= 1536
        0 <= d <= 255"""
        payload = [0x1D, 0x2A, x, y] + d
        self._handle_payload(payload)

    # (8-15)
    def print_downloaded_bit_image(self, m):
        """GS / m
        Print downloaded bit image
        Prints a downloaded bit image using the mode specified by m"""
        payload = [0x1D, 0x2F, m]
        self._handle_payload(payload)

    # TODO GS :

    def inverse_printing_mode(self, n):
        """GS R n (TYPO: it's GS B n)
        Turn white/black reverse printing mode on/off"""
        payload = [0x1D, 0x42, n]
        return self._handle_payload(payload)

    def select_hri_printing_position(self, n):
        """GS H n
        Select printing position of HRI characters"""
        payload = [0x1D, 0x48, n]
        return self._handle_payload(payload)

    # (8-16)
    # TODO GS I n
    # TODO GS L nL nH
    # TODO GS P x y

    def cut_paper(self, m, n=None):
        """1) GS V m , 2) GS V m n
        Select cut mode and cut paper
        Selects a mode for cutting paper and executes paper cutting.
        The value of m selects the mode.

        m == 66: Feeds paper (cutting position + [n x (vertical motion unit)]), and cuts the paper"""
        if self.debug_mode == DEBUG_MODE_VISUAL:
            sys.stdout.write("\nCUTCUTCUTCUTCUTCUTCUTCUTCUTCUTCUTCUTCUTCUT\n")
        payload = [0x1D, 0x56, m]
        if n is not None:
            payload.append(n)
        return self._handle_payload(payload)

    # (8-17)
    # TODO GS W nL nH
    # TODO GS \ nL nH

    # (8-18)
    # TODO GS ^ r t m
    # TODO GS a n

    def smoothing_mode(self, n):
        """GS b n
        Turns smoothing mode on/off"""
        payload = [0x1D, 0x62, n]
        return self._handle_payload(payload)

    def select_hri_font(self, n):
        """GS f n
        Select font for Human Readable Interpretation (HRI) characters."""
        payload = [0x1D, 0x66, n]
        return self._handle_payload(payload)

    def set_barcode_height(self, n):
        """GS h n
        Set barcode height
        Set the height of the bar code
        n specifies the number of dots in the vertical direction."""
        payload = [0x1D, 0x68, n]
        return self._handle_payload(payload)

    # TODO: BARCODE SYSTEMS > 65 (page 8-20)
    def print_barcode(self, n, m, data):
        """1) GS k m dl...dk NUL 2) GS k m n dl...dk
        Print bar code
        Selects a bar code system and prints the bar-code, m select a bar code system"""
        if self.debug_mode == DEBUG_MODE_VISUAL:
            sys.stdout.write("\nBARCODEBARCODEBARCODEBARCODEBARCODEBARCODE\n")
            sys.stdout.write(f"\n{data}\n")
        d = data.encode("ASCII")
        if m <= BARCODE_SYSTEM_A_CODABAR:
            payload = [0x1D, 0x6B, m] + list(d) + [0x00]
            return self._handle_payload(payload)

        # System B needs the data length. Callers passed 0 and got an empty
        # bar code, so fall back to the real length.
        if not n:
            n = len(d)
        payload = [0x1D, 0x6B, m, n] + list(d)
        return self._handle_payload(payload)

    # (8-20)
    # TODO GS r n

    # (8-21)
    def print_raster_bit_image(self, m, xL, xH, yL, yH, d):
        """GS v 0 m xL xH yL yH d1...dk
        Print raster bit image
        Selects Raster bit-image mode. The value of m selects the mode, as follows:
        """
        if self.debug_mode == DEBUG_MODE_VISUAL:
            sys.stdout.write("\n IMAGEIMAGEIMAGEIMAGEIMAGEIMAGEIMAGEIMAGE \n")
        payload = [0x1D, 0x76, 0x30, m, xL, xH, yL, yH] + d
        return self._handle_payload(payload)

    def set_barcode_width(self, n):
        """GS w n
        Set bar code width
        Set the horizontal size of the bar code, n specifies the bar code width as follows:"""
        payload = [0x1D, 0x77, n]
        return self._handle_payload(payload)

    def print_qr_code(
        self,
        data,
        module_size=6,
        error_correction=QR_EC_MEDIUM,
        model=QR_MODEL_2,
    ):
        """GS ( k
        Store a QR code and print it.

        Older firmware ignores these commands. Print a rendered QR image with
        `print_raster_bit_image` if nothing comes out.

        module_size is the dot size of one QR module, 1 to 16."""
        if isinstance(data, str):
            d = list(data.encode("utf-8"))
        else:
            d = list(data)

        # The store command counts the three bytes after pL pH as well.
        length = len(d) + 3

        payload = [0x1D, 0x28, 0x6B, 0x04, 0x00, 0x31, 0x41, model, 0x00]
        payload += [0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x43, module_size]
        payload += [0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x45, error_correction]
        payload += [
            0x1D,
            0x28,
            0x6B,
            length % 256,
            length // 256,
            0x31,
            0x50,
            0x30,
        ] + d
        payload += [0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x51, 0x30]
        return self._handle_payload(payload)

    # n generators

    def generate_image_data(self, image, center=True, max_width=PRINT_WIDTH_DOTS):
        """generates data for `print_raster_bit_image`
        image must be a pil image object. The given image will be scaled to fit the printer
        """

        width, height = image.size
        if width > max_width:
            ratio = width / max_width
            width = max_width
            height = int(height / ratio)
            image = image.resize((width, height), Image.Resampling.LANCZOS)

        img_original = image.convert("RGBA")
        im = Image.new("RGB", img_original.size, (255, 255, 255))
        im.paste(img_original, mask=img_original.split()[3])
        # Convert down to greyscale
        im = im.convert("L")
        # Invert: Only works on 'L' images
        im = ImageOps.invert(im)
        # Pure black and white
        im = im.convert("1")

        if center and width < max_width:
            new_im = Image.new("1", (max_width, height))
            new_im.paste(im, ((max_width - width) // 2, 0))
            im = new_im
            width = max_width

        # Pillow pads every row to a full byte, so the command must use the
        # padded width. A width that is not a multiple of 8 skewed the image.
        row_bytes = (width + 7) // 8
        xL = row_bytes % 256
        xH = row_bytes // 256
        yH = height // 256
        yL = height - (yH * 256)
        d = list(im.tobytes())
        return [xL, xH, yL, yH, d]

    def gen_print_mode(
        self,
        char_font,
        emphasized_mode,
        double_height_mode,
        double_width_mode,
        underline_mode,
    ):

        n = 0
        n |= 1 if char_font else 0
        n |= (1 if emphasized_mode else 0) << 3
        n |= (1 if double_height_mode else 0) << 4
        n |= (1 if double_width_mode else 0) << 5
        n |= (1 if underline_mode else 0) << 7

        return n

    def gen_character_size(self, width, height):
        return (width << 4) | height

    def generate_nv_image_data(self, width, height, data):
        return [width, 0, height, 0] + data
