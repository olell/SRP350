"""Checks that the commands put the documented bytes into the buffer.

The printer is opened on a temporary file, so the tests need no hardware.
"""

import os

import pytest
from PIL import Image

import srp350


@pytest.fixture
def printer(tmp_path):
    """A printer that writes to a file instead of a device."""
    target = tmp_path / "printer.out"
    target.touch()
    p = srp350.SRP350(device=str(target))
    p.target = target
    yield p
    p.close()


def test_justification(printer):
    assert printer.select_justification(srp350.ALIGN_CENTER) == [0x1B, 0x61, 1]


def test_character_code_table(printer):
    assert printer.select_character_code_table(srp350.CODEPAGE_PC858) == [
        0x1B,
        0x74,
        19,
    ]


def test_cash_drawer(printer):
    assert printer.open_cash_drawer() == [0x1B, 0x70, 0, 25, 250]


def test_hri_font_uses_gs_f(printer):
    # It used to send GS w, which sets the bar code width instead.
    assert printer.select_hri_font(srp350.HRI_FONT_B) == [0x1D, 0x66, 49]


def test_barcode_system_a_is_null_terminated(printer):
    payload = printer.print_barcode(0, srp350.BARCODE_SYSTEM_A_EAN8, "41057759")
    assert payload[:3] == [0x1D, 0x6B, 3]
    assert payload[-1] == 0x00


def test_barcode_system_b_fills_in_the_length(printer):
    # Every example passed n=0 here, which printed an empty bar code.
    payload = printer.print_barcode(0, srp350.BARCODE_SYSTEM_B_CODE128, "ABC")
    assert payload == [0x1D, 0x6B, 73, 3, ord("A"), ord("B"), ord("C")]


def test_qr_code_stores_then_prints(printer):
    payload = printer.print_qr_code("hi")
    # The store command counts the data plus the three bytes of its header.
    assert [0x1D, 0x28, 0x6B, 5, 0, 0x31, 0x50, 0x30, ord("h"), ord("i")] == payload[
        -18:-8
    ]
    # The last command is print (fn 81).
    assert payload[-8:] == [0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x51, 0x30]


def test_feed_lines_keeps_stdout_clean(printer, capsys):
    printer.print_and_feed_lines(3)
    assert capsys.readouterr().out == ""


def test_unknown_characters_do_not_raise(printer):
    # An emoji in a news headline must not kill the caller.
    payload = printer.print("café \U0001f600")
    assert payload == list("café ?".encode("cp437"))


def test_umlauts_survive_cp437(printer):
    assert printer.println("äöüß") == list(
        "äöüß\n".encode("cp437")
    )


def test_image_data_reports_the_padded_width(printer):
    # 100 dots wide is not a multiple of 8. Pillow pads the rows to 13 bytes,
    # and the command has to say 13 or the image comes out skewed.
    image = Image.new("1", (100, 7))
    xL, xH, yL, yH, data = printer.generate_image_data(image, center=False)
    assert (xL, xH) == (13, 0)
    assert (yL, yH) == (7, 0)
    assert len(data) == 13 * 7


def test_image_data_scales_down_to_the_head_width(printer):
    image = Image.new("1", (1024, 200))
    xL, xH, yL, yH, data = printer.generate_image_data(image)
    assert xL * 8 == srp350.PRINT_WIDTH_DOTS
    assert yL == 100


def test_image_data_centers_a_narrow_image(printer):
    image = Image.new("1", (64, 4))
    xL, _, _, _, data = printer.generate_image_data(image, center=True)
    assert xL * 8 == srp350.PRINT_WIDTH_DOTS
    assert len(data) == 64 * 4


def test_send_writes_the_buffer_and_clears_it(printer):
    printer.println("x")
    printer.send()
    assert printer.data == []
    assert printer.target.read_bytes() == b"x\n"


def test_context_manager_closes(tmp_path):
    target = tmp_path / "printer.out"
    target.touch()
    with srp350.SRP350(device=str(target)) as p:
        p.println("x")
        p.send()
    with pytest.raises(OSError):
        os.write(p.fd, b"x")


def test_visual_debug_works_before_initialize(tmp_path, capsys):
    # The debug flags used to be set in initialize_printer() only.
    target = tmp_path / "printer.out"
    target.touch()
    p = srp350.SRP350(device=str(target), debug_mode=srp350.DEBUG_MODE_VISUAL)
    p.print("x")
    p.close()
    assert "x" in capsys.readouterr().out
