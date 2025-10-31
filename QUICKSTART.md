# HVATP - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Prerequisites

1. **Python 3.8 or higher**
2. **Webcam** (for testing receiver mode)
3. **Basic Python knowledge**

### Installation

```bash
# Clone or download the repository
cd datatransfer

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import numpy, cv2, reedsolo; print('✅ All dependencies installed!')"
```

---

## 📝 Usage Examples

### Example 1: Send a File (Display Mode)

```python
from implementation.example_transfer import HVATPSender
from implementation.visual_encoder import EncodingMode

# Create sender
sender = HVATPSender(
    visual_mode=EncodingMode.BALANCED,
    display_scale=3
)

# Send file (displays QR codes on screen)
sender.send_file("myfile.pdf")
```

**What happens:**
- File is encoded into multi-color QR codes
- Codes display on screen at 30 fps
- Receiver can scan with camera to receive

---

### Example 2: Receive a File (Camera Mode)

```python
from implementation.example_transfer import HVATPReceiver

# Create receiver
receiver = HVATPReceiver(visual_mode_colors=4)

# Start receiving (point camera at sender's screen)
receiver.receive_from_camera(
    camera_id=0,
    output_file="received_file.pdf"
)
```

**What happens:**
- Opens camera feed
- Detects and decodes QR codes
- Reconstructs original file
- Saves to `received_file.pdf`

---

### Example 3: Generate Visual Frame

```python
from implementation.visual_encoder import VisualEncoder, EncodingMode
import cv2

# Create encoder
encoder = VisualEncoder(
    mode=EncodingMode.BALANCED,
    module_count=200,
    error_correction_level=0.35
)

# Encode data
data = b"Hello, HVATP!" * 10
frame = encoder.encode_frame(data, frame_id=0, total_frames=1)

# Display
display_frame = encoder.render_for_display(frame, scale=4)
cv2.imshow("QR Frame", display_frame)
cv2.waitKey(0)
```

---

### Example 4: Generate Audio Packet

```python
from implementation.audio_encoder import AudioEncoder, ModulationType
from scipy.io import wavfile
import numpy as np

# Create encoder
encoder = AudioEncoder(
    sample_rate=48000,
    num_subcarriers=48,
    modulation=ModulationType.QPSK
)

# Encode packet
payload = b"Sync and metadata"
audio = encoder.encode_packet(payload, frame_id=0, packet_seq=0)

# Save as WAV
wavfile.write("audio_packet.wav", 48000, (audio * 32767).astype(np.int16))
print("✅ Audio packet saved to audio_packet.wav")
```

---

## 🎮 Interactive Demo

Run the interactive demo:

```bash
cd implementation
python example_transfer.py
```

**Menu options:**
1. **Send file** - Display QR codes on screen
2. **Receive file** - Capture from camera
3. **Full simulation** - Demo without camera
4. **Exit**

---

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=implementation tests/

# Run specific test file
pytest tests/test_visual_encoder.py
```

### Performance Benchmark

```python
from implementation.visual_encoder import VisualEncoder, EncodingMode
import time

encoder = VisualEncoder(mode=EncodingMode.BALANCED)

# Benchmark encoding
data = b"X" * 5000  # 5 KB
start = time.time()

for i in range(100):
    frame = encoder.encode_frame(data, frame_id=i, total_frames=100)

elapsed = time.time() - start
fps = 100 / elapsed

print(f"Encoding speed: {fps:.1f} fps")
print(f"Throughput: {5000 * fps / 1024:.1f} KB/s")
```

---

## ⚙️ Configuration

### Visual Encoding Modes

```python
from implementation.visual_encoder import EncodingMode

# High throughput (best conditions)
mode = EncodingMode.HIGH_DENSITY  # 8 colors, 3 bits/module

# Balanced (normal conditions)
mode = EncodingMode.BALANCED  # 4 colors, 2 bits/module

# Robust (poor conditions)
mode = EncodingMode.ROBUST  # 2 colors, 1 bit/module
```

### Audio Modulation Schemes

```python
from implementation.audio_encoder import ModulationType

# Robust (noisy environments)
modulation = ModulationType.BPSK  # 1 bit/symbol

# Balanced (normal conditions)
modulation = ModulationType.QPSK  # 2 bits/symbol

# High throughput (quiet environments)
modulation = ModulationType.QAM16  # 4 bits/symbol
```

### Error Correction Levels

```python
# Less redundancy = higher throughput, lower reliability
ecc_level = 0.25  # 25% parity

# Balanced
ecc_level = 0.35  # 35% parity (recommended)

# More redundancy = lower throughput, higher reliability
ecc_level = 0.50  # 50% parity
```

---

## 🐛 Troubleshooting

### Issue: "Camera not detected"

**Solution:**
```python
# List available cameras
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i}: Available")
        cap.release()
    else:
        print(f"Camera {i}: Not available")
```

### Issue: "Decoding fails frequently"

**Solutions:**
1. Increase error correction level (0.35 → 0.50)
2. Switch to more robust mode (BALANCED → ROBUST)
3. Improve lighting conditions
4. Reduce distance between sender and receiver
5. Stabilize camera (use tripod or stand)

### Issue: "Low throughput"

**Solutions:**
1. Increase frame rate (30 fps → 60 fps)
2. Use higher density mode (BALANCED → HIGH_DENSITY)
3. Optimize lighting (500+ lux recommended)
4. Use higher quality camera/display
5. Reduce distance (optimal: 0.5-2 meters)

### Issue: "Audio packets not working"

**Note:** Audio decoder is not yet implemented in current version. Only visual channel is functional.

---

## 📊 Performance Tips

### Maximize Throughput

```python
# Use highest mode your conditions support
encoder = VisualEncoder(
    mode=EncodingMode.HIGH_DENSITY,  # 8 colors
    module_count=250,                # More modules
    error_correction_level=0.25      # Less ECC
)

# Increase frame rate
# Display at 60 fps instead of 30 fps
cv2.waitKey(16)  # 16ms = ~60 fps
```

### Maximize Reliability

```python
# Use most robust settings
encoder = VisualEncoder(
    mode=EncodingMode.ROBUST,        # 2 colors (B&W)
    module_count=200,
    error_correction_level=0.50      # Maximum ECC
)

# Lower frame rate for better decode
cv2.waitKey(50)  # 50ms = 20 fps
```

---

## 🔧 Advanced Usage

### Custom Encoding Pipeline

```python
from implementation.visual_encoder import VisualEncoder
import zstandard as zstd

# Compress data first
compressor = zstd.ZstdCompressor(level=3)
compressed = compressor.compress(original_data)

# Then encode
encoder = VisualEncoder()
frames = encoder.encode_data(compressed)

# Receiver reverses:
# 1. Decode frames → compressed data
# 2. Decompress → original data
```

### Frame Interleaving for Reliability

```python
# Instead of sequential: [F0, F1, F2, F3]
# Send interleaved: [F0, F2, F0', F1, F3, F1', F2']

def interleave_frames(frames, redundancy=0.3):
    interleaved = []
    redundant_count = int(len(frames) * redundancy)
    
    for i, frame in enumerate(frames):
        interleaved.append(frame)
        
        # Add redundant copies for first N frames
        if i < redundant_count:
            interleaved.append(frame)  # Duplicate
    
    return interleaved
```

---

## 📚 Next Steps

1. **Read the full spec:** [PROTOCOL_SPEC.md](../PROTOCOL_SPEC.md)
2. **Explore architecture:** [architecture/system_design.md](../architecture/system_design.md)
3. **Check performance:** [analysis/performance_benchmarks.md](../analysis/performance_benchmarks.md)
4. **See roadmap:** [ROADMAP.md](../ROADMAP.md)

---

## 💬 Get Help

- **Issues:** Report bugs or request features on GitHub
- **Discussions:** Ask questions in GitHub Discussions
- **Documentation:** Check the docs/ folder

---

**Happy transferring! 🚀**
