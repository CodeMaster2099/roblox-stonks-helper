from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

try:
    import winsound
except ImportError:  # pragma: no cover
    winsound = None


SCREENSHOT_PATH = Path(__file__).with_name("screen.png")
DEBUG_IMAGE_PATH = Path(__file__).with_name("stonks_debug.png")
SIGNAL_PATH = Path(__file__).with_name("stonks_signal.txt")

# Tuned for the current Roblox fullscreen screenshot layout at 1504x1003.
CHART_ROI = (560, 392, 1248, 724)


@dataclass
class Signal:
    label: str
    reason: str
    score: float
    short_move: float
    medium_move: float
    price_position: float
    recent_range: float


def smooth(values: np.ndarray, window: int = 9) -> np.ndarray:
    if len(values) < window:
        return values
    kernel = np.ones(window, dtype=float) / window
    padded = np.pad(values, (window // 2, window // 2), mode="edge")
    return np.convolve(padded, kernel, mode="valid")


def interpolate_missing(points: np.ndarray) -> np.ndarray:
    xs = np.arange(points.shape[0])
    mask = ~np.isnan(points)
    if mask.sum() < 25:
        raise ValueError("not enough chart pixels detected")
    return np.interp(xs, xs[mask], points[mask])


def extract_series(image: Image.Image) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    x1, y1, x2, y2 = CHART_ROI
    crop = np.array(image.crop((x1, y1, x2, y2)).convert("RGB"))

    # The price line is nearly white and low saturation.
    bright = crop.mean(axis=2) > 205
    neutral = (crop.max(axis=2) - crop.min(axis=2)) < 35
    mask = bright & neutral

    # Drop the lower timeline labels and most of the top row text.
    mask[:42, :] = False
    mask[-62:, :] = False
    mask[:, -42:] = False

    series = np.full(mask.shape[1], np.nan, dtype=float)
    for x in range(mask.shape[1]):
        ys = np.where(mask[:, x])[0]
        if ys.size:
            series[x] = float(np.median(ys))

    return smooth(interpolate_missing(series)), (x1, y1, x2, y2)


def classify(series: np.ndarray) -> Signal:
    last = float(series[-1])
    short_ago = float(series[-10])
    medium_ago = float(series[-35])
    recent = series[-90:]
    recent_peak = float(np.min(recent))
    recent_low = float(np.max(recent))
    recent_range = max(recent_low - recent_peak, 1.0)

    short_move = short_ago - last
    medium_move = medium_ago - last
    price_position = (recent_low - last) / recent_range
    score = (short_move * 0.55 + medium_move * 0.45) / recent_range

    if score >= 0.16 and 0.28 <= price_position <= 0.82:
        return Signal(
            "BUY",
            "uptrend is strengthening and it is not yet at the top of the recent range",
            score,
            short_move,
            medium_move,
            price_position,
            recent_range,
        )

    if score >= 0.10 and price_position > 0.82:
        return Signal(
            "WAIT",
            "price is pushing up, but it is already too close to the recent high to chase",
            score,
            short_move,
            medium_move,
            price_position,
            recent_range,
        )

    if score <= -0.12 and price_position > 0.55:
        return Signal(
            "SELL",
            "momentum is turning down from the upper half of the recent range",
            score,
            short_move,
            medium_move,
            price_position,
            recent_range,
        )

    if abs(score) < 0.05:
        return Signal(
            "HOLD",
            "movement is flat right now",
            score,
            short_move,
            medium_move,
            price_position,
            recent_range,
        )

    return Signal(
        "WAIT",
        "setup is mixed, so it is better to watch another tick",
        score,
        short_move,
        medium_move,
        price_position,
        recent_range,
    )


def maybe_beep(label: str) -> None:
    if winsound is None:
        return
    tones = {
        "BUY": (1200, 180),
        "SELL": (500, 220),
        "WAIT": (800, 120),
        "HOLD": (700, 120),
    }
    freq, duration = tones.get(label, (650, 120))
    winsound.Beep(freq, duration)


def write_debug_image(image: Image.Image, series: np.ndarray, roi: tuple[int, int, int, int]) -> None:
    debug = image.copy()
    draw = ImageDraw.Draw(debug)
    x1, y1, x2, y2 = roi
    draw.rectangle(roi, outline=(255, 0, 0), width=2)

    points = [(x1 + x, y1 + y) for x, y in enumerate(series)]
    if len(points) > 1:
        draw.line(points, fill=(0, 255, 0), width=2)

    debug.save(DEBUG_IMAGE_PATH)


def inspect_once(debug: bool) -> str:
    if not SCREENSHOT_PATH.exists():
        raise FileNotFoundError(f"{SCREENSHOT_PATH} is missing")

    image = Image.open(SCREENSHOT_PATH)
    series, roi = extract_series(image)
    signal = classify(series)

    if debug:
        write_debug_image(image, series, roi)

    timestamp = time.strftime("%H:%M:%S")
    metrics = (
        f"score={signal.score:.2f} "
        f"short={signal.short_move:.1f} "
        f"medium={signal.medium_move:.1f} "
        f"pos={signal.price_position:.2f} "
        f"range={signal.recent_range:.1f}"
    )
    return f"[{timestamp}] {signal.label}: {signal.reason} ({metrics})"


def monitor(interval: float, debug: bool, beep: bool) -> None:
    last_mtime = None
    last_label = None
    while True:
        try:
            mtime = SCREENSHOT_PATH.stat().st_mtime
        except FileNotFoundError:
            print("waiting for screen.png ...", flush=True)
            time.sleep(interval)
            continue

        if last_mtime is None or mtime != last_mtime:
            last_mtime = mtime
            try:
                message = inspect_once(debug=debug)
                SIGNAL_PATH.write_text(message + "\n", encoding="ascii", errors="ignore")
                print(message, flush=True)
                label = message.split("] ", 1)[1].split(":", 1)[0]
                if beep and label != last_label:
                    maybe_beep(label)
                last_label = label
            except Exception as exc:
                message = f"[{time.strftime('%H:%M:%S')}] WAIT: {exc}"
                SIGNAL_PATH.write_text(message + "\n", encoding="ascii", errors="ignore")
                print(message, flush=True)
                last_label = "WAIT"

        time.sleep(interval)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read Stonks screenshots and print simple trading signals.")
    parser.add_argument("--once", action="store_true", help="Inspect the current screenshot once and exit.")
    parser.add_argument("--interval", type=float, default=0.1, help="Polling interval in seconds.")
    parser.add_argument("--debug", action="store_true", help="Save an overlay image to stonks_debug.png.")
    parser.add_argument("--beep", action="store_true", help="Play a short tone when a new signal is printed.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.once:
        message = inspect_once(debug=args.debug)
        SIGNAL_PATH.write_text(message + "\n", encoding="ascii", errors="ignore")
        print(message)
        return
    monitor(interval=max(args.interval, 0.05), debug=args.debug, beep=args.beep)


if __name__ == "__main__":
    main()
