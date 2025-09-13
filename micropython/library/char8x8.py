# MIT Licence copyright 2025 Jim dodgen
# a character lookup dictionary/hash
# 8x8 matrix tested on TM1640 driver
# thanks to xantorohara https://xantorohara.github.io/led-matrix-editor/#
# this mamming is not correct for the tm1640.py driver but used for ease
# of customization using xantorohara's tool
# 

CHARS = {
  "A": "6666667e66663c00",   # 66 66 66 7e 66 66 3c 00
  "B": "3e66663e66663e00",
  "C": "3c66060606663c00",
  "D": "3e66666666663e00",
  "E": "7e06063e06067e00",
  "F": "0606063e06067e00",
  "G": "3c66760606663c00",
  "H": "6666667e66666600",
  "I": "3c18181818183c00",
  "J": "1c36363030307800",
  "K": "66361e0e1e366600",
  "L": "7e06060606060600",
  "M": "c6c6c6d6feeec600",
  "N": "c6c6e6f6decec600",
  "O": "3c66666666663c00",
  "P": "06063e6666663e00",
  "Q": "603c766666663c00",
  "R": "66361e3e66663e00",
  "S": "3c66603c06663c00",
  "T": "18181818185a7e00",
  "U": "7c66666666666600",
  "V": "183c666666666600",
  "W": "c6eefed6c6c6c600",
  "X": "c6c66c386cc6c600",
  "Y": "1818183c66666600",
  "Z": "7e060c1830607e00",
  "all_off": "0000000000000000",
  "a": "7c667c603c000000",
  "b": "3e66663e06060600",
  "c": "3c6606663c000000",
  "d": "7c66667c60606000",
  "e": "3c067e663c000000",
  "f": "0c0c3e0c0c6c3800",
  "g": "3c607c66667c0000",
  "h": "6666663e06060600",
  "i": "3c18181800180000",
  "j": "1c36363030003000",
  "k": "66361e3666060600",
  "l": "1818181818181800",
  "m": "d6d6feeec6000000",
  "n": "6666667e3e000000",
  "o": "3c6666663c000000",
  "p": "06063e66663e0000",
  "q": "f0b03c36363c0000",
  "r": "060666663e000000",
  "s": "3e403c027c000000",
  "t": "1818187e18180000",
  "u": "7c66666666000000",
  "v": "183c666600000000",
  "w": "7cd6d6d6c6000000",
  "x": "663c183c66000000",
  "y": "3c607c6666000000",
  "z": "3c0c18303c000000",
  "1": "7e1818181c181800",
  "2": "7e060c3060663c00",
  "3": "3c66603860663c00",
  "4": "30307e3234383000",
  "5": "3c6660603e067e00",
  "6": "3c66663e06663c00",
  "7": "1818183030667e00",
  "8": "3c66663c66663c00",
  "9": "3c66607c66663c00",
  "0": "3c66666e76663c00",
  "wifi": "01012955554501ff",   # problem with wifi connection
  "broker": "39494939493901ff", # problem with broker connection
  "?": "1800183860663c00",
  "boot1": "0000001818000000",
  "boot2": "00003c24243c0000"

}

def reverse_bits_in_byte(byte_value):
    """Reverses the order of bits within a single byte."""
    reversed_byte = 0
    for i in range(8):
        if (byte_value >> i) & 1:  # Check if the i-th bit is set
            reversed_byte |= (1 << (7 - i))  # Set the corresponding bit in the reversed byte
    return reversed_byte


class char8x8:
    global CHARS
    def __init__(self, invert=False):
        self.invert = invert

    def map(self, string):  # convert first char of a string to 8x8 matrix
        try:
            item = CHARS[string] # might be a full word match like boot1
        except:
            try:
                item = CHARS[string[0]] # Just lookup the first char
            except:
                print("char8x8 not found in CHARS", string)
                item = CHARS["?"]
        #print("char8x8 item", string, item)
        parts = [item[i:i+2] for i in range(0, 16, 2)]
        #print("char8x8 parts", string, parts)
        #if self.invert:
            #parts.reverse()
        int_parts = []
        for part in parts:
            hex_part = int(part, 16)
            if self.invert:
                hex_part = reverse_bits_in_byte(hex_part)
            int_parts.append(hex_part)
        #print("char8x8 int_parts", string, int_parts)
        if self.invert:
            int_parts.reverse()
        #print("char8x8 reverse", string, int_parts)
        return int_parts

    def create_tm1640_dict(self):
        tm1620_chars =  {}
        for key in CHARS:
            #print("%s[%s]" % (key, CHARS[key]))
            tm1620_chars[key] = self.map(key)
        as_string = str(tm1620_chars)
        return as_string.replace(" ","")
            


     




#t=char8x8(invert=True)
#print(t.create_tm1640_dict())
# print("true", t.map("B"))
# f=char8x8(invert=False)
# print("false", f.map("B"))


# hex_byte_value = 0xAA  # Example: 10101010 in binary
# reversed_byte = reverse_bits_in_byte(hex_byte_value)

# print(f"Original byte (hex): {hex(hex_byte_value)}")
# print(f"Original byte (binary): {bin(hex_byte_value)}")
# print(f"Reversed byte (hex): {hex(reversed_byte)}")
# print(f"Reversed byte (binary): {bin(reversed_byte)}")
