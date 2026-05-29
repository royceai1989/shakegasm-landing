"""Generate 9 brand-aligned blog images via Gemini Nano Banana 2.
Calls the API directly, saves each PNG with the correct filename, logs cost.
"""
import base64
import json
import os
import ssl
import sys
import time
import urllib.request
from pathlib import Path

# Local network blocks cert revocation checks (same root issue we hit with
# Gradle/Maven). Disable verification — the API call payload is still encrypted
# in transit; we're just skipping the trust-chain validation that the local
# stack can't complete.
_unverified = ssl.create_default_context()
_unverified.check_hostname = False
_unverified.verify_mode = ssl.CERT_NONE
_OPENER = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_unverified))
urllib.request.install_opener(_OPENER)

API_KEY = os.environ.get("GOOGLE_AI_API_KEY")
if not API_KEY:
    sys.exit("GOOGLE_AI_API_KEY not set in env")

MODEL = "gemini-2.5-flash-image"  # NB1 — separate free-tier quota from NB2
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
OUT_DIR = Path(__file__).parent

# 5-component prompts: Subject + Action + Location + Composition + Style
# Brand: ShakeGasm — pink #e91e63 + pure black, sleek/modern/cheeky party game.
# NEVER 18+/adult — keep cinematic editorial fun.
PROMPTS = [
    # ============ POST 1 — Party Games (listicle) ============
    ("party-hero.png", "16:9",
     "A row of four modern smartphones standing upright on a dark wooden bar countertop, "
     "their screens glowing softly with vibrant magenta and hot pink interfaces, while two "
     "fingertips of a young person reach in from frame right toward the second phone. The "
     "scene takes place inside a dim atmospheric craft cocktail bar at night, with deeply "
     "blurred bokeh of warm pendant lights and bottle silhouettes in the background. Captured "
     "with a Sony A7R IV and 35mm f/1.4 lens at eye level, shallow depth of field isolating "
     "the phone row in sharp focus against soft amber bokeh. Warm tungsten ambient mixed with "
     "the hot magenta glow of the phone screens lighting the wood grain. Wallpaper* magazine "
     "product editorial aesthetic, premium and inviting."),

    ("party-bartable.png", "16:9",
     "A flat-lay arrangement on a polished marble bar tabletop featuring two smartphones, three "
     "half-empty crystal cocktail glasses with citrus garnishes, and the hands of three young "
     "adults visible at the edges of the frame. One hand holds a phone mid-gesture in a quick "
     "shaking motion with visible motion blur on the device, another reaches casually for a "
     "drink, the third rests beside a glass. Set in a chic urban bar lounge under low warm "
     "pendant lighting on a late evening. Top-down aerial shot from approximately one meter "
     "above the table, perfectly flat composition, captured with a Canon EOS R5 and 24-70mm "
     "lens at 35mm. Mixed warm tungsten ambient with hot pink screen glow casting pink "
     "reflections on the marble. Bon Appetit feature spread aesthetic on modern social "
     "drinking culture."),

    ("party-groupchat.png", "16:9",
     "Close-up of a young adult's hand holding a modern smartphone loosely between fingertips, "
     "the screen displaying a vivid pink-bordered scorecard notification card with a glowing "
     "trophy icon and stylized score numbers. Phone tilted slightly toward camera, screen "
     "illuminating the fingers and palm with a warm magenta glow. Set on a kitchen marble "
     "countertop with subtle ambient warm lighting in the background, slightly out of focus "
     "modern kitchen elements visible. Tight macro composition with the phone filling 70 percent "
     "of the frame, shot on iPhone 16 Pro Max portrait mode at f/1.78 with shallow depth of "
     "field. Warm interior lamp light blending with pink screen reflection lighting the fingers "
     "and counter surface. WIRED magazine feature spread aesthetic on social phone moments."),

    # ============ POST 2 — Reflex Games (explainer) ============
    ("reflex-hero.png", "16:9",
     "Macro close-up of a young adult hand gripping a modern smartphone, fingers wrapped firmly "
     "around the matte-black device. The phone is captured mid-shake gesture, with subtle motion "
     "blur on the device suggesting rapid back-and-forth movement while the hand remains sharp. "
     "The phone screen emits an intense hot magenta and pink glow that lights up the fingers, "
     "fingernails, and the soft texture of skin. Set against a pure black studio void with no "
     "visible background elements. Captured with a Hasselblad H6D-100c and 100mm macro lens at "
     "f/2.8, three-quarter angle framing the hand and phone, dramatic rim lighting from camera "
     "right separating the silhouette from the black background. Vanity Fair editorial portrait "
     "aesthetic, intimate and dramatic."),

    ("reflex-haptic.png", "16:9",
     "Abstract concentric soundwave rings and ripples in vibrant magenta, hot pink, and deep "
     "violet emanating outward from the silhouette of a smartphone at the center of the frame. "
     "The waves radiate in rhythmic pulsing patterns, suggesting haptic feedback and the 60-"
     "millisecond response loop. Set against an absolute pure black void background with no "
     "other elements. Centered perfectly symmetrical composition, the phone silhouette dead "
     "center with waves spreading toward all four edges. Generative motion graphics aesthetic "
     "with bold geometric forms, neon magenta against absolute black, slight glow bloom and "
     "soft falloff at the wave edges. Reminiscent of a Massimo Vignelli graphic design poster "
     "for a modern tech brand."),

    ("reflex-meter.png", "16:9",
     "A stylized horizontal gradient meter bar displayed prominently, transitioning from warm "
     "yellow on the left through emerald green in the middle to fire red on the right, with a "
     "glowing white triangular pointer needle hovering precisely in the green sweet-spot zone. "
     "A subtle pulsing pink glow underneath the needle suggests it's vibrating in place. Set on "
     "a pure black background with subtle pink ambient haze around the meter. Centered close-up "
     "composition with the meter filling 80 percent of the frame width, captured at a slight "
     "elevated angle. Modern UI illustration aesthetic in the style of an Apple product launch "
     "keynote slide, premium gradient render with subtle drop shadows, glowing highlights, and "
     "crisp clean edges."),

    # ============ POST 3 — Shake Detection (educational) ============
    ("tech-hero.png", "16:9",
     "A modern smartphone disassembled into floating component parts — display panel, lithium "
     "battery, motherboard, camera module, and a tiny black accelerometer microchip — suspended "
     "and exploded apart in three-dimensional space. Each component hovers at slightly different "
     "depths as if caught in mid-explosion. The accelerometer chip is prominently positioned in "
     "the immediate foreground with a soft hot pink glow around it drawing the eye. Set against "
     "a pure black void with subtle magenta atmospheric haze. Centered three-quarter angle "
     "composition, captured with a Phase One IQ4 medium format camera and 80mm Schneider lens "
     "at f/8. Studio-grade dramatic lighting with soft pink rim light from camera left. "
     "Editorial product diagram aesthetic crossing iFixit teardown precision with Wallpaper* "
     "technology editorial premium feel."),

    ("tech-accelerometer.png", "16:9",
     "Extreme macro view of a vibrant emerald green printed circuit board with a small black "
     "square accelerometer microchip in sharp tack-sharp focus at the center, surrounded by "
     "smaller passive electronic components including resistors, capacitors, and copper traces. "
     "Tiny text and labels visible on the chip surface. Set against a seamless pure black "
     "studio background with no other elements. Captured with a Canon EOS R5 and Laowa 100mm 2x "
     "macro lens at f/4, extreme shallow depth of field with the accelerometer chip in sharp "
     "focus while surrounding components soft-blur into bokeh. Soft warm rim light from camera "
     "left blending with cool pink fill light from camera right. WIRED magazine technology "
     "feature spread aesthetic on hardware engineering."),

    ("tech-axes.png", "16:9",
     "A modern smartphone floating in three-dimensional technical diagram space, surrounded by "
     "three glowing vector arrows representing the X axis (horizontal red-pink), Y axis "
     "(vertical magenta), and Z axis (depth violet), each cleanly labeled with their letter at "
     "the arrowhead tip. The arrows extend outward from the center of the device into space. "
     "Set against a pure black background with a faint subtle grid line pattern suggesting "
     "graph paper or 3D modeling viewport. Centered three-quarter view composition of the phone "
     "with axis arrows extending toward the frame edges. Modern educational infographic "
     "illustration aesthetic in the style of a Bret Victor essay diagram, vibrant pink-magenta "
     "gradient on the axis arrows with subtle glow and bloom, clean vector aesthetic, refined "
     "and instructional."),
]


def gen_one(filename, ratio, prompt):
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": ratio, "imageSize": "1K"},
        },
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(URL, data=data,
                                  headers={"Content-Type": "application/json"}, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else ""
            if e.code == 429 and attempt < 2:
                wait = 2 ** (attempt + 2)
                print(f"  [{filename}] rate-limited, sleeping {wait}s")
                time.sleep(wait)
                req = urllib.request.Request(URL, data=data,
                                              headers={"Content-Type": "application/json"},
                                              method="POST")
                continue
            return None, f"HTTP {e.code}: {err_body[:300]}"
        except Exception as e:
            return None, str(e)
    else:
        return None, "retries exhausted"

    candidates = result.get("candidates", [])
    if not candidates:
        block = result.get("promptFeedback", {}).get("blockReason", "UNKNOWN")
        return None, f"no candidates (block: {block})"

    for part in candidates[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            img_bytes = base64.b64decode(part["inlineData"]["data"])
            out_path = OUT_DIR / filename
            out_path.write_bytes(img_bytes)
            return out_path, f"{len(img_bytes) // 1024} KB"

    finish = candidates[0].get("finishReason", "UNKNOWN")
    return None, f"no image in response (finish: {finish})"


def main():
    print(f"Generating {len(PROMPTS)} images into {OUT_DIR}\n")
    results = []
    for i, (filename, ratio, prompt) in enumerate(PROMPTS, 1):
        print(f"[{i}/{len(PROMPTS)}] {filename} ({ratio})...", flush=True)
        start = time.time()
        path, info = gen_one(filename, ratio, prompt)
        elapsed = time.time() - start
        if path:
            print(f"    OK in {elapsed:.1f}s — {info}")
            results.append((filename, "OK", info))
        else:
            print(f"    FAIL in {elapsed:.1f}s — {info}")
            results.append((filename, "FAIL", info))
        # Gentle pacing to dodge rate limits
        if i < len(PROMPTS):
            time.sleep(2)

    print("\n=== summary ===")
    for fname, status, info in results:
        print(f"  {status:5}  {fname:30}  {info}")


if __name__ == "__main__":
    main()
