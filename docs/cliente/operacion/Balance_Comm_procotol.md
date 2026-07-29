# Balance Communication Protocol

**Balanza Brand: DINI ARGEO**

**Balanza Model: DFWLI-2**

Se requiere que la balanza este configurada en modo RS-485 con direccion "00".


## 6. COMMUNICATION STRINGS

---
### Short string

**01ST,GS, 0.0,kg<CR><LF>**

where

 - 01:		Code 485 of the instrument (2 characters), only if communication mode 485 is enabled
 - ST:		Scale status (2 characters):
	-	US - Weight unstable
	-	ST - Weight stable
	-	OL - Weight overload (out of range)
	-	UL -1 Weight underload (out of range)
	-	TL - Scale not level (inclinometer active)
 - ,:		ASCII 044 character
 - GS:		Type of weight data (2 characters)
 - ,:		ASCII 044 character
 - 0.0:	Weight (8 characters including the decimal point)
 - ,:		ASCII 044 character
 - kg:		Unit of measurement (2 characters)
 - <CR1><LF>: Transmission terminator, characters ASCII 013 and ASCII 010

---
### Extended string

**01ST,1, 0.0,PT 20.8, 0,kg<CR><LF>**

where

 - 01:		Code 485 of the instrument (2 characters), only if communication mode 485 is enabled
 - ST:		Scale status (2 characters):
	-	US - Weight unstable
	-	ST - Weight stable
	-	OL - Weight overload (out of range)
	-	UL - Weight underload (out of range)
	-	TL - Scale not level (inclinometer active)
 - ,:		ASCII 044 character
 - 1:		ASCII 049 character
 - ,:		ASCII 044 character
 - 0.0:	Net weight (10 characters including the decimal point)
 - ,:		ASCII 044 character
 - PT:		Indication of pre-set manual tare (2 characters)
 - 20.8:	Tare weight (10 characters including the decimal point)
 - ,:		ASCII 044 character
 - 0:		Number of pieces (10 characters)
 - ,:		ASCII 044 character
 - kg:		Unit of measurement (2 characters)
 - <CR><LF>: Transmission terminator, characters ASCII 013 and ASCII 010

---

## 7. COMMUNICATION CONTROLS

Premise:

in the serial controls and in the relative responses
nn Address 485 of the instrument (2 characters) (only if communication mode RS485 is activated)
<CR> Terminator character ASCII 13 (0D) (1 character)
<LF> Terminator character ASCII 10 (0A) (1 character)


**Reading of simple weight**
```
Control:	nnREAD<CR><LF>
Response:	Short string (see ##6)
```

**Reading of complete weight**
```
Control:	nnREXT<CR><LF>
Response:	Extended string (see ##6)
```

**Execution of a semi-automatic tare**
```
Control:	nnTARE<CR><LF>
Response:	OK<CR><LF> indicates that the control was received correctly
```

**Setting of the tare value (PT)**
```
Control:	nnTMANtttttttt<CR><LF>  /*Where t...t is the tare, with decimal points, max 8 characters.*/
Response:	OK<CR><LF>			/*indicates that the control was received correctly*/
Examples:
 - TMAN1.56<CR><LF>				/* set a tare of 1.56 */
 - TMAN100<CR><LF>				/* set a tare of 100 */
```

**Deleting the tare in memory**
```
Control:	nnCLEAR<CR><LF>
Response:	OK<CR><LF>
```

**Scale reset (function of the ZERO key)**
```
Control:	nnZERO<CR><LF>
Response:	OK<CR><LF>
```

