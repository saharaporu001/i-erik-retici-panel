
import argparse, random, math, os
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

def load_logo(path, max_w=160, max_h=160):
    img = Image.open(path).convert("RGBA")
    # keep aspect ratio
    w, h = img.size
    scale = min(max_w / w, max_h / h, 1.0)
    if scale != 1.0:
        img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    return img

def paste_rgba(frame, pil_img, x, y):
    fw, fh = frame.shape[1], frame.shape[0]
    w, h = pil_img.size
    if x+w <=0 or y+h <=0 or x >= fw or y >= fh:
        return frame
    # Convert PIL to numpy with alpha
    rgba = np.array(pil_img)
    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3:] / 255.0
    sx1, sx2 = max(0, -x), min(w, fw - x)
    sy1, sy2 = max(0, -y), min(h, fh - y)
    tx1, tx2 = max(0, x), min(fw, x + w)
    ty1, ty2 = max(0, y), min(fh, y + h)
    roi = frame[ty1:ty2, tx1:tx2]
    part_rgb = rgb[sy1:sy2, sx1:sx2]
    part_alpha = alpha[sy1:sy2, sx1:sx2]
    roi[:] = (part_rgb * part_alpha + roi * (1 - part_alpha)).astype(np.uint8)
    return frame

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--duration", type=int, default=90)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--logo", action="append", required=True)
    ap.add_argument("--min-goals", type=int, default=2)
    ap.add_argument("--max-goals", type=int, default=5)
    args = ap.parse_args()

    W, H, FPS = args.width, args.height, args.fps
    frames_total = args.duration * FPS
    field_color = (20, 60, 20)
    writer = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))

    logos = [load_logo(p) for p in args.logo]
    n = len(logos)
    rng = random.Random()

    # Initialize moving objects
    objs = []
    for i in range(n):
        w, h = logos[i].size
        x = rng.randint(0, W - w)
        y = rng.randint(0, H - h)
        sp = rng.uniform(4, 9)
        ang = rng.uniform(0, 2*math.pi)
        vx, vy = sp*math.cos(ang), sp*math.sin(ang)
        objs.append({"x": x, "y": y, "vx": vx, "vy": vy, "img": logos[i]})

    # Define simple goals at left/right
    goal_w, goal_h = 60, 220
    goal_top = (H - goal_h) // 2
    left_goal = (0, goal_top, goal_w, goal_h)
    right_goal = (W - goal_w, goal_top, goal_w, goal_h)

    # Goals logic
    target_goals = rng.randint(max(1,args.min_goals), max(args.min_goals, args.max_goals))
    goals = 0
    goal_flash = 0

    for f in range(frames_total):
        frame = np.zeros((H, W, 3), dtype=np.uint8)
        frame[:] = field_color

        # draw midline
        cv2.line(frame, (W//2, 0), (W//2, H), (200,200,200), 2)
        # draw goals
        for gx, gy, gw, gh in [left_goal, right_goal]:
            cv2.rectangle(frame, (gx, gy), (gx+gw, gy+gh), (230,230,230), 3)

        # move & bounce
        for o in objs:
            w, h = o["img"].size
            o["x"] += o["vx"]
            o["y"] += o["vy"]
            if o["x"] < 0 or o["x"] + w > W:
                o["vx"] *= -1
            if o["y"] < 0 or o["y"] + h > H:
                o["vy"] *= -1

        # goal detection (if logo center enters goal area)
        for o in objs:
            w, h = o["img"].size
            cx, cy = int(o["x"] + w/2), int(o["y"] + h/2)
            for side, (gx, gy, gw, gh) in enumerate([left_goal, right_goal]):
                if gx <= cx <= gx+gw and gy <= cy <= gy+gh:
                    if goals < target_goals:
                        goals += 1
                        goal_flash = 15  # frames
                        # kick ball back
                        if side == 0 and o["vx"] < 0: o["vx"] *= -1
                        if side == 1 and o["vx"] > 0: o["vx"] *= -1

        # draw logos
        for o in objs:
            frame = paste_rgba(frame, o["img"], int(o["x"]), int(o["y"]))

        # goal flash
        if goal_flash > 0:
            alpha = min(1.0, goal_flash/15.0)
            overlay = frame.copy()
            cv2.putText(overlay, f"GOOOL! ({goals})", (W//2-140, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (255,255,255), 3, cv2.LINE_AA)
            cv2.addWeighted(overlay, 0.7*alpha, frame, 1-0.7*alpha, 0, frame)
            goal_flash -= 1

        # scoreboard
        cv2.putText(frame, f"SURE: {f//FPS:02d}:{f%FPS:02d}  GOL: {goals}/{target_goals}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (240,240,240), 2, cv2.LINE_AA)

        writer.write(frame)

    writer.release()

if __name__ == "__main__":
    main()
