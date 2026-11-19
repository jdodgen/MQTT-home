import asyncio
import struct
from machine import Pin, I2C
import tm1640
import time

# 1. Hardware Setup (Wemos S2 Mini + Triple Base)
i2c = I2C(0, scl=Pin(35), sda=Pin(33), freq=400000)
MPU_ADDR = 0x68
i2c.writeto_mem(MPU_ADDR, 0x6B, b'\x00')  # Wake MPU-6050
i2c.writeto_mem(MPU_ADDR, 0x1A, b'\x03')  # ~44Hz Digital Low-Pass Filter

tm = tm1640.TM1640(clk=Pin(7), dio=Pin(11))
tm.brightness(0)

reset_btn = Pin(0, Pin.IN, Pin.PULL_UP)  # Onboard BOOT button (active-low)

FONT_3X5 = {
    0: (0b111, 0b101, 0b101, 0b101, 0b111),
    1: (0b010, 0b110, 0b010, 0b010, 0b111),
    2: (0b111, 0b001, 0b111, 0b100, 0b111),
    3: (0b111, 0b001, 0b111, 0b001, 0b111),
    4: (0b101, 0b101, 0b111, 0b001, 0b001),
    5: (0b111, 0b100, 0b111, 0b001, 0b111),
    6: (0b111, 0b100, 0b111, 0b101, 0b111),
    7: (0b111, 0b001, 0b001, 0b010, 0b010),
    8: (0b111, 0b101, 0b111, 0b101, 0b111),
    9: (0b111, 0b101, 0b111, 0b001, 0b111),
}

inst_heave_cm = 0.0
current_wave_cm = 0.0
max_wave_cm = 0.0
reset_requested = False


def set_pixel(buf, x, y):
    if 0 <= x < 8 and 0 <= y < 8:
        buf[y] |= (1 << (7 -x))


def draw_digit(buf, digit, x_offset):
    rows = FONT_3X5[digit]
    for y in range(5):
        row_bits = rows[y]
        for x in range(3):
            if row_bits & (1 << (2 - x)):
                set_pixel(buf, x_offset + x, y)


def draw_two_digits(buf, val):
    val = max(0, min(99, int(round(val))))
    tens = val // 10
    ones = val % 10
    if tens > 0:
        draw_digit(buf, tens, 0)
    draw_digit(buf, ones, 4)


def read_accel_g():
    data = i2c.readfrom_mem(MPU_ADDR, 0x3B, 6)
    rx, ry, rz = struct.unpack('>hhh', data)
    return rx / 16384.0, ry / 16384.0, rz / 16384.0


async def imu_heave_task():
    global inst_heave_cm, current_wave_cm, max_wave_cm, reset_requested

    alpha = 0.991

    # 1. Let sensor settle after waking up
    for _ in range(25):
        read_accel_g()
        await asyncio.sleep_ms(10)

    # 2. Calibrate initial resting Z-axis gravity baseline
    z_sum = 0.0
    for _ in range(100):
        _, _, az = read_accel_g()
        z_sum += az
        await asyncio.sleep_ms(10)
    z_base = z_sum / 100.0

    vel = 0.0
    pos_m = 0.0
    prev_acc = 0.0
    crest_env = 0.0
    trough_env = 0.0
    warmup_ticks = 150  # Ignore first ~3s while filter centers

    print_counter = 0
    last_ms = time.ticks_ms()

    while True:
        now_ms = time.ticks_ms()
        dt = time.ticks_diff(now_ms, last_ms) / 1000.0
        last_ms = now_ms

        if dt <= 0 or dt > 0.1:
            dt = 0.02

        if reset_btn.value() == 0 or reset_requested:
            reset_requested = False
            max_wave_cm = 0.0
            current_wave_cm = 0.0
            vel = 0.0
            pos_m = 0.0
            crest_env = 0.0
            trough_env = 0.0
            warmup_ticks = 150


        _, _, az = read_accel_g()

        # Slowly track temperature/DC drift in gravity baseline
        z_base = 0.999 * z_base + 0.001 * az

        acc = (az - z_base) * 9.80665
        if abs(acc) < 0.04:  # Ignore stationary bench/sensor noise (< 0.004g)
            acc = 0.0


        # 1. Integrate acceleration -> velocity
        dv = 0.5 * (acc + prev_acc) * dt
        vel = alpha * (vel + dv)
        prev_acc = acc

        # 2. Integrate velocity -> position
        pos_m = alpha * (pos_m + vel * dt)
        inst_heave_cm = pos_m * 100.0

        # 3. Track crest and trough envelopes (~13s decay holds full wave height)
        if inst_heave_cm > crest_env:
            crest_env = inst_heave_cm
        else:
            crest_env *= 0.9985

        if inst_heave_cm < trough_env:
            trough_env = inst_heave_cm
        else:
            trough_env *= 0.9985

        wave_height_cm = crest_env - trough_env
        if warmup_ticks > 0:
            warmup_ticks -= 1
            current_wave_cm = 0.0
        elif wave_height_cm >= 1.5:
            current_wave_cm = wave_height_cm
            if wave_height_cm > max_wave_cm:
                max_wave_cm = wave_height_cm
        else:
            current_wave_cm = 0.0

        print_counter += 1
        if print_counter >= 10:
            print(
                f"heave: {inst_heave_cm:6.2f} cm | max: {max_wave_cm:6.2f} cm ({round(max_wave_cm / 2.54)} in)"
            )
            print_counter = 0

        await asyncio.sleep_ms(15)


async def display_task():
    global reset_requested
    MAX_BAR_IN = 24.0  # Full bar deflection at ±24 inches (2 feet)

    while True:
        # Flash all LEDs briefly when reset button (BOOT / GPIO 0) is held
        if reset_btn.value() == 0:
            reset_requested = True
            tm.write(bytearray([0xFF] * 8))
            await asyncio.sleep_ms(100)
            continue

        buf = bytearray(8)

        # Convert max wave height from cm to rounded whole inches (clamped 0–99)
        max_in = min(99, int(round(max_wave_cm / 2.54)))
        draw_two_digits(buf, max_in)

        # Live heave dot along bottom row (row 7) scaled in inches
        heave_in = inst_heave_cm / 2.54
        norm = max(-1.0, min(1.0, heave_in / MAX_BAR_IN))
        cursor_x = int(round(3.5 + (norm * 3.5)))
        set_pixel(buf, cursor_x, 7)

        # Center zero-reference markers on row 6
        set_pixel(buf, 3, 6)
        set_pixel(buf, 4, 6)

        tm.write(buf)
        await asyncio.sleep_ms(50)


async def main():
    await asyncio.gather(
        imu_heave_task(),
        display_task()
    )


asyncio.run(main())
