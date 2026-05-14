import os
os.system("sudo dd if=/dev/mmcblk1 of=current.img bs=4M status=progress")
