# MIT Licence copyright 2025 Jim dodgen
# a character lookup dictionary/hash
# 8x8 matrix tested on TM1640 driver
# thanks to xantorohara https://xantorohara.github.io/led-matrix-editor/#

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

class char8x8:
    global CHARS
    def __init__(self, invert=False):
        self.invert = invert

    def map(self, string):  # convert first char of a string to 8x8 matrix
        print("char8x8.map", string)
        try:
            item = CHARS[string] # might be a full word match like boot1
        except:
            try:
                item = CHARS[string[0]] # Just lookup the first char 
            except:
                print("char8x8 not found in CHARS", string)
                item = CHARS["?"]
        parts = [item[i:i+2] for i in range(0, 16, 2)]
        if self.invert:
            parts.reverse()
        int_parts = [int(part, 16) for part in parts]
        print("char8x8", string, int_parts)
        if self.invert:
            int_parts.reverse()
        return int_parts

# if __ name __ == '__ main __':
    # print(char8x8("x"))
    # print(char8x8("querty")
    # print(char8x8("*") # must be A-Z,a-z,0-9
