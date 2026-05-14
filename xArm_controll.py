# ps4_send_udp_both_100ms_debug.py

import socket
import time

print("Step 1: importing pygame...", flush=True)
import pygame

print("Step 2: pygame imported", flush=True)

TARGETS = [
    ("192.168.100.43", 50007),
    ("192.168.100.15", 50007),
    ("192.168.100.12", 50007),
]

PERIOD_S = 0.1

BUTTON_INDEXES = [0, 1, 2, 3, 7, 8, 9, 10, 11, 12, 13, 14, 4, 5, 6]
AXIS_COUNT = 6

PRINT_EVERY = 1

print("Step 3: pygame init start", flush=True)
pygame.init()
pygame.joystick.init()
print("Step 4: pygame init done", flush=True)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

joy = None
seq = 0


def connect_joystick():
    global joy

    pygame.event.pump()

    count = pygame.joystick.get_count()

    if count == 0:
        joy = None
        return False

    if joy is None or not joy.get_init():
        joy = pygame.joystick.Joystick(0)
        joy.init()

        print(
            f"Joystick ready: {joy.get_name()} "
            f"buttons={joy.get_numbuttons()} axes={joy.get_numaxes()}",
            flush=True,
        )

    return True


print("Step 5: main loop start", flush=True)

try:
    next_time = time.perf_counter()

    while True:
        loop_start = time.perf_counter()

        now = time.perf_counter()

        if now < next_time:
            time.sleep(next_time - now)

        actual_send_time = time.perf_counter()
        delay_from_schedule = actual_send_time - next_time

        next_time += PERIOD_S

        if delay_from_schedule > PERIOD_S:
            print(
                f"[WARN] loop schedule delay: {delay_from_schedule:.3f} s", flush=True
            )
            next_time = actual_send_time + PERIOD_S

        controller_ok = connect_joystick()

        if controller_ok:
            nb = joy.get_numbuttons()
            btn_bits = []

            for idx in BUTTON_INDEXES:
                v = joy.get_button(idx) if idx < nb else 0
                btn_bits.append("1" if v else "0")

            btn_str = "".join(btn_bits)

            na = joy.get_numaxes()
            axes = []

            for i in range(AXIS_COUNT):
                a = joy.get_axis(i) if i < na else 0.0
                axes.append(f"{a:.3f}")

        else:
            btn_str = "0" * len(BUTTON_INDEXES)
            axes = ["0.000"] * AXIS_COUNT

        payload_str = (
            f"BTN={btn_str};AX={','.join(axes)};SEQ={seq};T={actual_send_time:.6f}"
        )

        payload = payload_str.encode("ascii")

        for ip, port in TARGETS:
            sock.sendto(payload, (ip, port))

        loop_end = time.perf_counter()
        loop_dt = loop_end - loop_start

        if seq % PRINT_EVERY == 0:
            print(
                f"SEQ={seq:08d} | "
                f"send='{payload_str}' | "
                f"loop_dt={loop_dt:.4f}s | "
                f"delay={delay_from_schedule:.4f}s | "
                f"controller={'OK' if controller_ok else 'NG'}",
                flush=True,
            )

        seq += 1

except KeyboardInterrupt:
    print("\nStopped by user.", flush=True)

finally:
    if joy is not None:
        joy.quit()

    pygame.quit()
    sock.close()
    print("Closed.", flush=True)
