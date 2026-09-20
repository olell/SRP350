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
