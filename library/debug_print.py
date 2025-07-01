#
# conditional formatted print replacement
# Use mostly during micropython debugging
# MIT License Copyright Jim Dodgen 2025
# if first string starts with a "." then the first word of the string is appended to the print_tag
# typically identifying the routine or class
# tipical print statement:  "print(".internal_name hellow world, 2025)
# typical print output: "[file_name.internal_name] hello world 2025"
# this needs to be pasted into your .py
#
print_tag = "run" # The python file name
do_prints = True  # Set to False in production
#
def turn_on_prints(flag):  # true or false
    global do_prints
    do_prints=flag
raw_print = print # copy print
def print(first, *args, **kwargs): # replace print
    global do_prints
    if do_prints:
        f=None
        if isinstance(first, str) and first[0] == ".":
            f = first.split(" ",1)
        else:
            f = ["",first]
        try:
            if len(f) > 1:
                raw_print("["+print_tag+f[0]+"]", f[1], *args, **kwargs) # the copied real print
            else:
                raw_print("["+print_tag+f[0]+"]", *args, **kwargs) # the copied real print
        except:
            raise ValueError("xprint problem ["+print_tag+"]")
# end of conditional formatted print replacement 2025
#
