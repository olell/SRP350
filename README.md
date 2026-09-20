# SRP350
Python driver for bixolon SRP350 thermal printer

## Connecting

Write to a device file:

```python
p = srp350.SRP350("/dev/usb/lp0")
```

Write to a network printer over TCP:

```python
p = srp350.SRP350(ip="192.168.1.50", port=9100)
```

`port` defaults to 9100. Give either `device` or `ip`, not both.

The connection stays open until you call `close()`. `SRP350` is also a context
manager:

```python
with srp350.SRP350(ip="192.168.1.50", timeout=10) as p:
    p.println("hello")
    p.send()
```

Nothing goes to the printer until `send()` runs. `timeout` is the socket
timeout in seconds and defaults to 10.

## Text

Text is encoded to CP437 by default, which is the factory codepage of the
SRP-350 and holds the German umlauts. Characters that the codepage does not
hold become `?` instead of raising an error.

Tell the printer to switch codepage with `select_character_code_table`, and use
the matching `encoding`. CP858 adds the Euro sign:

```python
p.select_character_code_table(srp350.CODEPAGE_PC858)
p.println("12,50 EUR", encoding="cp858")
```

Align a line with `select_justification(srp350.ALIGN_CENTER)`. Set it back to
`ALIGN_LEFT` afterwards.

## Status

The printer answers status requests on the same connection:

```python
p.paper_status()     # {"near_end": False, "out_of_paper": False}, or None
p.printer_online()   # False while the cover is open
```

Both return None if the printer stays quiet before the timeout.

## Bar codes and QR codes

```python
p.set_barcode_height(100)
p.select_hri_printing_position(srp350.HRI_POS_BELOW)
p.print_barcode(0, srp350.BARCODE_SYSTEM_A_EAN13, "4388860567386")
p.print_qr_code("https://example.com", module_size=6)
```

`print_barcode` fills in the data length for the CODE93 and CODE128 systems, so
the first argument can stay 0.

`print_qr_code` needs firmware that knows the GS ( k commands. If nothing comes
out, render the QR code to a PIL image and print it with
`print_raster_bit_image` instead.

## Tests

```
python -m pytest tests/
```

The tests open the printer on a temporary file, so they need no hardware.
