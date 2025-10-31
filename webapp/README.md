# HVATP Web Application

Simple web-based demo of the Hybrid Visual + Audio Transfer Protocol.

## 🚀 Quick Start

### Option 1: Local Testing

1. **Open Sender (on desktop/laptop):**
   - Open `sender.html` in a web browser
   - Upload a file
   - Configure settings
   - Click "Start Transfer"

2. **Open Receiver (on phone):**
   - Open `receiver.html` on your phone's browser
   - Grant camera permissions
   - Click "Start Camera"
   - Point camera at sender's screen

### Option 2: GitHub Pages

1. Push to GitHub
2. Enable GitHub Pages in repository settings
3. Access via: `https://yourusername.github.io/Hibriddatatransfer/webapp/sender.html`

## 📱 Features

### Sender (`sender.html`)
- ✅ File upload (drag & drop or browse)
- ✅ Encoding mode selection (High Density / Balanced / Robust)
- ✅ Error correction levels (25% / 35% / 50%)
- ✅ Frame rate control (15 / 30 / 60 fps)
- ✅ Real-time statistics (frames, throughput, progress)
- ✅ Visual QR code display
- ✅ Pause/Resume functionality

### Receiver (`receiver.html`)
- ✅ Camera access
- ✅ Real-time QR code scanning
- ✅ Frame detection and assembly
- ✅ Progress tracking
- ✅ Activity logging
- ✅ File download
- ✅ Data preview

## 🔧 Technical Details

### Simplified Implementation

This web demo uses a simplified version of the full HVATP protocol:

- **Visual Channel Only:** Audio channel not implemented in web version
- **Simplified QR Encoding:** Uses basic color patterns instead of full JAB Code
- **Basic Error Correction:** Relies on frame retransmission
- **Browser-Based:** Uses HTML5 Canvas and WebRTC

### Browser Compatibility

- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+
- ✅ Mobile browsers with camera support

## 📊 Performance

Web version performance is lower than native implementation:

- **Throughput:** ~50-150 KB/s (vs 1-2 MB/s native)
- **Latency:** Higher due to browser overhead
- **Reliability:** Good with jsQR library, basic without

## 🔒 Privacy

- ✅ All processing happens locally in browser
- ✅ No data sent to servers
- ✅ Camera access required only for receiver
- ✅ Files never uploaded to cloud

## 🐛 Troubleshooting

### Camera not working
- Grant camera permissions
- Use HTTPS (required for camera access)
- Try different browser
- Check if camera is already in use

### Poor detection rate
- Improve lighting conditions
- Reduce distance to screen
- Use higher resolution camera
- Lower frame rate on sender
- Use "Robust" mode (B&W)

### File not downloading
- Check browser's download settings
- Ensure pop-ups are allowed
- Try different browser

## 🔮 Future Enhancements

- [ ] Audio channel integration (Web Audio API)
- [ ] Full JAB Code implementation
- [ ] Reed-Solomon error correction
- [ ] WebAssembly acceleration
- [ ] Progressive Web App (PWA)
- [ ] Offline support
- [ ] File encryption

## 📚 Related Files

- `../implementation/` - Python native implementation
- `../PROTOCOL_SPEC.md` - Full protocol specification
- `../README.md` - Project overview
