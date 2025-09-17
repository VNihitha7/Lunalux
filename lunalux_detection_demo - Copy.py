import cv2
import numpy as np
import matplotlib.pyplot as plt

# ---------- Load Images ----------
before = cv2.imread("crater_before.jpg")
after  = cv2.imread("crater_after.jpg")

if before is None or after is None:
    print("Error: Images not found. Please put crater_before.jpg and crater_after.jpg in the same folder.")
    exit()

# Resize to same dimensions
h = min(before.shape[0], after.shape[0])
w = min(before.shape[1], after.shape[1])
before = cv2.resize(before, (w, h))
after  = cv2.resize(after,  (w, h))

# Convert to grayscale
before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
after_gray  = cv2.cvtColor(after,  cv2.COLOR_BGR2GRAY)

# ---------- Enhance illuminated image ----------
clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
after_enhanced = clahe.apply(after_gray)

# ---------- Compute difference (what appeared after illumination) ----------
diff = cv2.subtract(after_enhanced, before_gray)
diff_norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

# Threshold to get bright regions
_, thresh = cv2.threshold(diff_norm, 40, 255, cv2.THRESH_BINARY)

# Clean noise
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

# ---------- Find contours (candidate objects) ----------
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

output = after.copy()

for cnt in contours:
    area = cv2.contourArea(cnt)
    if area < 80:  # ignore tiny noise
        continue
    x,y,wc,hc = cv2.boundingRect(cnt)
    roi = after_enhanced[y:y+hc, x:x+wc]
    mean_intensity = np.mean(roi)
    aspect_ratio = wc/float(hc)
    solidity = area / (wc*hc + 1e-5)

    # ---------- Simple rules to classify (Simulation Only) ----------
    # Brighter + smoother regions → ICE
    # Medium brightness + irregular → ROCK
    if mean_intensity > 160 and solidity > 0.4:
        label = "ICE"
        color = (255, 0, 0)  # Blue box
    else:
        label = "ROCK"
        color = (0, 255, 255)  # Yellow box

    cv2.rectangle(output, (x,y), (x+wc, y+hc), color, 2)
    cv2.putText(output, label, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

# ---------- Show results ----------
plt.figure(figsize=(12,6))

plt.subplot(1,3,1)
plt.title("Before (Dark)")
plt.axis("off")
plt.imshow(cv2.cvtColor(before, cv2.COLOR_BGR2RGB))

plt.subplot(1,3,2)
plt.title("After (Illuminated)")
plt.axis("off")
plt.imshow(cv2.cvtColor(after, cv2.COLOR_BGR2RGB))

plt.subplot(1,3,3)
plt.title("Detected Rocks & Ice")
plt.axis("off")
plt.imshow(cv2.cvtColor(output, cv2.COLOR_BGR2RGB))

plt.tight_layout()
plt.show()

cv2.imwrite("crater_detected.png", output)
print("✅ Result saved as crater_detected.png")
