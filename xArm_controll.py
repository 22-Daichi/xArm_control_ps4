# ps4_send_udp_both_100ms.py
import socket, time, pygame

# ★宛先を設定（ESP32 と 隣PC）
TARGETS = [
    ("192.168.100.15", 50007),  # ESP32
    ("192.168.100.12", 50007),  # 隣PC
]
PERIOD_S = 0.100  # 100ms

# 15ボタン固定の並び（インデックスはあなたの指定）
BUTTON_INDEXES = [0, 1, 2, 3, 7, 8, 9, 10, 11, 12, 13, 14, 4, 5, 6]
# ↑ 最後の 4,5,6 は未使用想定なら常に0になります（環境により使われるなら残してOK）

AXIS_COUNT = 6  # 0..5 を送る：LSx,LSy,RSx,RSy,L2,R2

pygame.init()
pygame.joystick.init()

# ジョイスティック待機（未接続でも動き続ける）
joy = None
def ensure_joystick():
    global joy
    if joy and joy.get_init():
        return True
    pygame.joystick.quit(); pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        return False
    joy = pygame.joystick.Joystick(0); joy.init()
    print(f"Joystick ready: {joy.get_name()}  buttons={joy.get_numbuttons()} axes={joy.get_numaxes()}")
    return True

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
seq = 0

try:
    while True:
        t0 = time.perf_counter()
        pygame.event.pump()

        if not ensure_joystick():
            print("waiting for PS4 controller...")
            time.sleep(0.5)
            continue

        # ボタン列（15桁の0/1文字列に整形）
        nb = joy.get_numbuttons()
        btn_bits = []
        for idx in BUTTON_INDEXES:
            v = joy.get_button(idx) if idx < nb else 0
            btn_bits.append('1' if v else '0')
        btn_str = "".join(btn_bits)

        # 軸（-1..1 の実数 → 小数3桁に丸めて送信）
        na = joy.get_numaxes()
        axes = []
        for i in range(AXIS_COUNT):
            a = joy.get_axis(i) if i < na else 0.0
            # 小数3桁に丸め（文字列短縮＆見やすさ）
            axes.append(f"{a:.3f}")

        payload = f"BTN={btn_str};AX={','.join(axes)};SEQ={seq}".encode("ascii")

        for ip, port in TARGETS:
            sock.sendto(payload, (ip, port))

        seq += 1
        dt = PERIOD_S - (time.perf_counter() - t0)
        if dt > 0:
            time.sleep(dt)
except KeyboardInterrupt:
    pass
finally:
    if joy: joy.quit()
    pygame.quit()
    sock.close()
