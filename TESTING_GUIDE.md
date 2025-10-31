# Testing Guide - HVATP Web App

## 🎯 Quick Test (Recommended First Steps)

### Step 1: Test Sender
1. Open on desktop: https://rogerjs93.github.io/Hibriddatatransfer/webapp/sender.html
2. Create a small test file (5-10 KB):
   - Create `test.txt` with some content
   - Or use any small text file
3. Drag & drop or click to upload
4. Settings:
   - Mode: **BALANCED** (4 colors)
   - Error Correction: **Medium (35%)**
   - Frame Rate: **30 fps**
   - Audio: **Enabled** ✓
5. Click **"Start Transfer"**
6. Watch for:
   - ✅ Encoding progress (should complete in 2-5 seconds)
   - ✅ Animated colored frames on screen
   - ✅ Audio beeps (triple beep at start, then sync beeps)

### Step 2: Test Receiver
1. Open on phone: https://rogerjs93.github.io/Hibriddatatransfer/webapp/receiver.html
2. **Optional**: Check "Enable Audio Detection" (experimental)
3. Click **"📷 Start Camera"**
4. Grant permissions:
   - Camera access (required)
   - Microphone access (if audio detection enabled)
5. Point camera at desktop screen showing sender
6. Watch for:
   - ✅ "✓ Frame X captured" messages in log
   - ✅ Frame counter increasing
   - ✅ If audio enabled: "🔊 Audio sync detected" messages

## 🐛 Troubleshooting

### Issue: Receiver not detecting frames

**Symptoms**: Camera on, but no frames captured

**Checklist**:
1. ✅ **Distance**: Keep phone 50-100 cm from screen (not too close!)
2. ✅ **Brightness**: Increase screen brightness to maximum
3. ✅ **Lighting**: Good room lighting, avoid screen glare
4. ✅ **Stability**: Hold phone steady (use stand if possible)
5. ✅ **Angle**: Point directly at screen (perpendicular)
6. ✅ **Focus**: Tap screen to focus camera on display
7. ✅ **Frame rate**: Try 15 fps on sender (slower = easier to scan)

**Advanced**:
- Try **ROBUST mode** (B&W, easier to detect)
- Disable audio on both sides initially
- Use smaller test file (< 5 KB)
- Clear browser cache and reload

### Issue: "startBtn is null" error

**Status**: ✅ **FIXED** in latest version

**If still seeing**: Hard refresh the page (Ctrl+Shift+R or Cmd+Shift+R)

### Issue: Browser timeout during encoding

**Status**: ✅ **FIXED** in latest version

**Limits**:
- Max file size: 500 KB (hard limit)
- Recommended: < 100 KB
- Warning shown for files > 100 KB

**If still timing out**:
- Use smaller file
- Lower error correction (25%)
- Use ROBUST mode (fewer colors = faster)

### Issue: No audio beeps

**Desktop Sender**:
1. Check "Enable Audio Channel" is checked ✓
2. Unmute your speakers
3. Check browser isn't muted (tab icon)
4. Try clicking the page first (browsers require user interaction)

**Mobile Receiver** (if using audio detection):
1. Grant microphone permission
2. Enable "Enable Audio Detection" checkbox
3. Volume doesn't matter (using mic, not speakers)

### Issue: Permissions denied

**Camera**:
- Click lock icon in address bar
- Set Camera → Allow
- Reload page

**Microphone**:
- Click lock icon in address bar  
- Set Microphone → Allow
- Reload page

## 📊 Expected Performance

### Small File (5-10 KB)
- **Encoding**: 1-2 seconds
- **Frames**: 15-35 frames
- **Transfer**: 10-30 seconds
- **Detection Rate**: 60-90%

### Medium File (25-50 KB)
- **Encoding**: 3-8 seconds
- **Frames**: 85-170 frames
- **Transfer**: 30-90 seconds
- **Detection Rate**: 50-80%

### Large File (100+ KB)
- **Encoding**: 10-30 seconds
- **Frames**: 350+ frames
- **Transfer**: 2-5 minutes
- **Detection Rate**: 40-70%

## 🎬 Ideal Test Scenario

### Desktop Setup
```
1. Screen brightness: 100%
2. File size: 10 KB text file
3. Mode: BALANCED
4. Error correction: 35%
5. Frame rate: 30 fps
6. Audio: Enabled
```

### Phone Setup
```
1. Distance: 60-80 cm from screen
2. Audio detection: Disabled (for first test)
3. Focus: Auto-focus on screen
4. Hold: Steady or on stand
```

### Expected Result
```
- Encoding: ~2 seconds
- Frames generated: ~35
- Frames detected: 20-30 (60-90%)
- Time to complete: 20-40 seconds
- Audio beeps: Heard clearly
```

## 🔬 Advanced Testing

### Test Visual Decoder
The receiver now uses a custom decoder that:
1. Detects finder patterns (black squares in corners)
2. Extracts module data from colored grid
3. Uses hash-based deduplication
4. Has 200ms cooldown between captures

**Debug tip**: Open browser console (F12) to see detailed detection logs

### Test Audio Detection
When enabled, the receiver:
1. Creates Web Audio API context
2. Analyzes frequency spectrum
3. Detects peaks around 1000 Hz (±500 Hz range)
4. Logs "🔊 Audio sync detected" when beep heard

**Frequency breakdown**:
- Metadata beeps: 800, 1200, 1600 Hz (triple beep)
- Frame sync: 1000-1900 Hz (varies by frame)
- End signal: 1500→500 Hz sweep

### Test Different Modes

**HIGH_DENSITY (8 colors)**:
- ✅ More data per frame (3 bits/module)
- ⚠️ Harder to detect (color accuracy needed)
- 🎯 Use for: Optimal conditions only

**BALANCED (4 colors)**:
- ✅ Good data density (2 bits/module)
- ✅ Reliable detection
- 🎯 Use for: Most scenarios (recommended)

**ROBUST (2 colors - B&W)**:
- ✅ Best reliability (1 bit/module)
- ⚠️ Slower transfer (more frames)
- 🎯 Use for: Difficult conditions

## 📱 Mobile Browser Compatibility

### Tested & Working
- ✅ Chrome Android (90+)
- ✅ Safari iOS (14+)
- ✅ Firefox Android (88+)
- ✅ Samsung Internet (14+)

### Known Issues
- ⚠️ iOS Safari: Requires HTTPS for camera access (GitHub Pages ✓)
- ⚠️ iOS Safari: Audio may need tap to start
- ⚠️ Some phones: Camera resolution limited to 720p

## 🎓 Understanding Detection

### Why frames might be missed:
1. **Motion blur**: Phone moved while capturing
2. **Out of focus**: Camera couldn't focus on screen
3. **Glare**: Light reflection on screen
4. **Frame rate**: Too fast for camera to keep up
5. **Distance**: Too close or too far
6. **Angle**: Not perpendicular to screen

### Why detection works:
1. **Finder patterns**: Distinctive black squares in corners
2. **Color encoding**: Multiple bits per module
3. **Hash deduplication**: Same frame not counted twice
4. **Cooldown**: Prevents rapid re-detection
5. **Module sampling**: Robust to minor distortion

## 📈 Optimization Tips

### For Better Detection Rate
1. **Reduce frame rate**: 15-20 fps easier to scan
2. **Use ROBUST mode**: B&W is most reliable
3. **Increase error correction**: 50% for difficult conditions
4. **Better lighting**: Avoid dim rooms
5. **Steady phone**: Use tripod or phone stand

### For Faster Transfer
1. **Increase frame rate**: 60 fps if detection is good
2. **Use HIGH_DENSITY**: More data per frame
3. **Lower error correction**: 25% if conditions are ideal
4. **Smaller files**: Break large files into chunks

## 🧪 Test Files

### Recommended Test Files

**Tiny (< 5 KB)**:
```
Create test.txt with:
Hello from HVATP!
This is a test of the hybrid visual+audio transfer protocol.
[Repeat 10 times]
```

**Small (10-20 KB)**:
```
Any text document or small JSON file
```

**Medium (50 KB)**:
```
Small code file or short article
```

**Large (100+ KB)**:
```
Only after successful smaller tests!
```

## ✅ Success Checklist

Before reporting issues, verify:
- [ ] Using latest version (hard refresh)
- [ ] Screen brightness at 100%
- [ ] Camera permissions granted
- [ ] Distance 50-100 cm
- [ ] Room well lit
- [ ] Phone held steady
- [ ] Started with small file (< 10 KB)
- [ ] Used BALANCED or ROBUST mode
- [ ] Frame rate 30 fps or less

## 🎉 Expected First Test Result

With a 10 KB file, BALANCED mode, 30 fps:
```
✅ Encoding: 2 seconds
✅ Transfer starts: Frames display + audio beeps
✅ Receiver: Detects 20-30 of 35 frames (60-85%)
✅ Time: 20-40 seconds total
✅ Result: Partial data received (can see captured frames)
```

**Note**: 100% frame capture is rare in web version due to:
- Camera limitations
- JavaScript performance
- Screen refresh sync
- Environmental factors

The protocol includes error correction and will eventually support frame retransmission!
