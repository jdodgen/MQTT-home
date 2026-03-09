import os

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
        image = files[choice] 
    except:
        print("\nnumber out of range")
        exit()
os.system(f"xz -dc {image} | sudo dd of=/dev/mmcblk1 bs=1M status=progress")
