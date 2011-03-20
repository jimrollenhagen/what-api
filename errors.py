class AuthError(Exception):
	pass

# when a barcode is not 12 (UPC) or 13 (EAN) characters
class InvalidBarcodeError(Exception):
	pass
