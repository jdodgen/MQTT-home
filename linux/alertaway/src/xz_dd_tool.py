import os

# this is run in .bashrc and needs the following
# sudo visudo
# add this line: jim ALL=(ALL) NOPASSWD: /home/jim/xz_dd_tool.py
#
os.system("ip a")
choice = input("\nMount eMMc (/dev/mmcblk1p1) (y,N):")
if choice == "y":
    os.system("sudo mkdir /mnt/emmc")
    os.system("sudo mount /dev/mmcblk1p1 /mnt/emmc")

print("\nhome-broker eMMC imager\n")
files = [f for f in os.listdir('.') if f.endswith('.img.xz')]
if len(files) == 0:
    print("Nothing to do, no .img.gz files")
    exit()

if len(files) == 1:
    image = files[0]
else: # more that one
    i = 0
    for f in files:
        i += 1
        print(f"{i}){f}")
    choice = input("\nEnter the number of the file to flash: ")
    try:
        image = files[int(choice)-1] 
    except:
        print("\nnumber out of range")
        exit()
command = f"xz -dc {image} | sudo dd of=/dev/mmcblk1 bs=1M status=progress"
print(command)
os.system(command)
