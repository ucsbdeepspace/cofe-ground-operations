'''

This module, originally concieved of and written by Connor Wolf, provides an 
easy way to parse the data record sent by the Galil microcontroller while 
polling. Here is an edited version of Connor's original description of the 
data record that we need to parse:

First, the labeling convention for the relevant bits (no pun intended) of data
in each 'block' is as follows (remember, one byte is eight bits): 
UB = Unsigned byte			# 1 Byte
UW = Unsigned Word			# 2 Bytes
SW = Signed Word			# 2 Bytes
SL = Signed Long Word		# 4 Bytes

The first four bytes of the data record are a header
UB	1 st byte of header				Header
UB	2 nd byte of header				Header
UB	3 rd byte of header				Header
UB	4 rth byte of header			Header

The next 24 bytes are the "I" block:
UW	sample number					I block 		2 Bytes
UB	general input 0					I block 		1 Byte
UB	general input 1					I block 		1 Byte
UB	general input 2					I block 		1 Byte
UB	general input 3					I block 		1 Byte
UB	general input 4					I block 		1 Byte
UB	general input 5					I block 		1 Byte
UB	general input 6					I block 		1 Byte
UB	general input 7					I block 		1 Byte
UB	general input 8					I block 		1 Byte
UB	general input 9					I block 		1 Byte
UB	general output 0				I block 		1 Byte
UB	general output 1				I block 		1 Byte
UB	general output 2				I block 		1 Byte
UB	general output 3				I block 		1 Byte
UB	general output 4				I block 		1 Byte
UB	general output 5				I block 		1 Byte
UB	general output 6				I block 		1 Byte
UB	general output 7				I block 		1 Byte
UB	general output 8				I block 		1 Byte
UB	general output 9				I block 		1 Byte
UB	error code						I block 		1 Byte
UB	general status					I block 		1 Byte

the 24 Bytes total for I Block are accessed using this string with the struct
module:
str = <HBBBBBBBBBBBBBBBBBBBBBB

The next 16 bytes are the S and T 'blocks'. each is 8 bytes long. First is the
S block, but the T block is identical:
UW	segment count of coordinated move for S plane				S block		2 Bytes
UW	coordinated move status for S plane							S block		2 Bytes
SL	distance traveled in coordinated move for S plane			S block		4 Bytes

8 Bytes per block for S and T blocks, each block is accessed using this string:
str = <HHl

The next 28*8 bytes are the blocks for the Galil's axes (A - H). Like the S
and T blocks, each of the axes blocks is formatted similarly to one another.
The following gives an example of the structure of the axes blocks:

UW	a axis status					A block		2 Bytes
UB	a axis switches					A block		1 Byte
UB	a axis stop code				A block		1 Byte
SL	a axis reference position		A block		4 Bytes
SL	a axis motor position			A block		4 Bytes
SL	a axis position error			A block		4 Bytes
SL	a axis auxiliary position		A block		4 Bytes
SL	a axis velocity					A block		4 Bytes
SW	a axis torque					A block		2 Bytes
SW	a axis analog					A block		2 Bytes

Each axis block is 28 bytes long (We think?). The string for accessing this
data is this:
str = <HBBlllllhh

Also, incase you are uncertain or haven't figured it out by now, H stands for
UW, B stands for UB, l stands for SL, and h stands for SW. You can refer to
the section on Connors naming conventions at the top for more help.

'''

import struct

#The first 50 ish lines just set up constants that will be used in the parsing

NAMES = ("header", "I", "S", "T") + tuple(chr(i) for i in range(65,73))

PARSE_STRINGS = (
	"<HH", #header
	"<HBBBBBBBBBBBBBBBBBBBBBB", #I
	"<HHl", #S and T
	"<HBBlllllhh" #A - H
	)

PARSE_STRINGS = PARSE_STRINGS[:2] + PARSE_STRINGS[2]*2 + PARSE_STRINGS[3]*8

LENGTHS = tuple(struct.calcsize(ps) for ps in PARSE_STRINGS)

HEADER_FIELD = ("flags", "length")
I_FIELD = ("sample number")
I_FIELD = I_FIELD + tuple("general input {}".format(i) for i in range(10))
I_FIELD = I_FIELD + tuple("general output {}".format(i) for i in range(10))
I_FIELD = I_FIELD + ("error code", "general status")
ST_FIELD = (
	"segment count",
	"coordinated move status",
	"distance traveled"
	)
AXIS_FIELD = (
	"status", "switches", 
	"stop code", "reference position", 
	"motor position", "position error",
	"auxiliary position", "velocity",
	"torque", "analog"
	)

FIELDS = (HEADER_FIELD, I_FIELD) + (ST_FIELD,)*2 + (AXIS_FIELD,)*8

PARSERS = []
for parse_string, length, field in zip(PARSE_STRINGS, LENGTHS, FIELDS):
	def parser(data_string, parse_string=parse_string, 
			   data_length=data_length, data_field=data_field):

		if len(data_string) != data_length:
			raise ValueError("Invalid passed string length!")
		vals = struct.unpack(parse_string, data_string)
		if len(data_field) != len(vals):
			err = "Amount of field names is unequal to amount of values!"
			raise ValueError(err)
		return dict(zip(data_field, vals))

	PARSERS.append(parser)

MASKS = (None,) + tuple(1 << x for x in ([10, 8, 9] + range(8)))

META_DATA = zip(NAMES, MASKS, LENGTHS, PARSERS)

def parse_data(data_string):

	header_name, _, header_length, header_parser = META_DATA[0]
	header = header_parser(data_string[:header_length])
	if header["length"] != len(data_string):
		raise ValueError("Invalid data string length!")
 
	data_string = data_string[header_length:]

	#The flags field of the header needs to be fiddled with...
	#It is a 2 byte integer, and it needs its bytes swapped.
	#The data in the flags fields is a bunch of bits, each one signalling
	#whether or not a specific block is included in the data string.
	#
	#So, first I swap the bytes.
	byte_mask = 2**8 - 1
	flags = header["flags"]
	flags = header["flags"] = (flags >> 8) | ((flags & byte_mask) << 8)

	result = {header_name:header}
	for name, mask, length, parser in META_DATA[1:]:
		if flags&mask:
			result[name] = parser(data_string[:length])
		else:
			length = 0
		data_string = data_string[length:]

	return result
