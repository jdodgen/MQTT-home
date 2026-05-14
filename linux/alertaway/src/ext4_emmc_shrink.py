import subprocess
import os

def shrink_image_file(img_path, buffer_mb=4000):
    try:
        print(f"--- Processing {img_path} ---")

        # 1. Force a filesystem check (Required before resizing)
        print("Checking filesystem...")
        subprocess.run(['e2fsck', '-fy', img_path], check=True)

        # 2. Shrink the ext4 filesystem to minimum size
        print("Shrinking filesystem to minimum...")
        subprocess.run(['resize2fs', '-M', img_path], check=True)

        # 3. Get exact block data from tune2fs
        print("Calculating new size...")
        output = subprocess.check_output(['tune2fs', '-l', img_path], text=True)
        
        block_count = 0
        block_size = 0
        for line in output.splitlines():
            if "Block count:" in line:
                block_count = int(line.split(":")[1].strip())
            if "Block size:" in line:
                block_size = int(line.split(":")[1].strip())

        # 4. Calculate size + Buffer
        fs_size = block_count * block_size
        buffer_bytes = buffer_mb * 1024 * 1024
        final_size = fs_size + buffer_bytes

        # 5. Truncate the file (The 'Simple' Part)
        print(f"Truncating file to {final_size / 1024**2:.2f} MB (includes buffer)...")
        with open(img_path, 'ab') as f:
            f.truncate(final_size)

        print("Done! Image is now shrunken and safe.")

    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    
    shrink_image_file("current.img")
