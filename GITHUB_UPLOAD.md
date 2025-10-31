# 📤 How to Upload to GitHub

Follow these steps to upload the HVATP project to your GitHub repository.

---

## 🔗 Step 1: Connect to Remote Repository

```bash
# Add the remote repository
git remote add origin https://github.com/rogerjs93/Hibriddatatransfer.git

# Verify remote was added
git remote -v
```

---

## 📤 Step 2: Push to GitHub

```bash
# Push to main branch (or master, depending on your default branch)
git push -u origin master
```

**If you get an error about the branch name:**
```bash
# Rename branch to 'main' if needed
git branch -M main
git push -u origin main
```

---

## 🌐 Step 3: Enable GitHub Pages (for Web App)

1. Go to your repository: https://github.com/rogerjs93/Hibriddatatransfer
2. Click **Settings** tab
3. Scroll down to **Pages** section (left sidebar)
4. Under **Source**, select:
   - Branch: `main` (or `master`)
   - Folder: `/ (root)`
5. Click **Save**
6. Wait 1-2 minutes for deployment

**Your web apps will be available at:**
- Sender: `https://rogerjs93.github.io/Hibriddatatransfer/webapp/sender.html`
- Receiver: `https://rogerjs93.github.io/Hibriddatatransfer/webapp/receiver.html`

---

## 📱 Step 4: Test the Web Apps

### On Desktop (Sender):
1. Open: `https://rogerjs93.github.io/Hibriddatatransfer/webapp/sender.html`
2. Upload a test file
3. Click "Start Transfer"
4. QR codes will display on screen

### On Phone (Receiver):
1. Open: `https://rogerjs93.github.io/Hibriddatatransfer/webapp/receiver.html`
2. Grant camera permissions
3. Click "Start Camera"
4. Point camera at desktop screen showing QR codes
5. Watch as frames are detected and assembled

---

## 🔧 If Repository Already Has Content

If the repository already exists with content:

```bash
# Pull existing content first
git pull origin main --rebase

# Then push
git push -u origin main
```

---

## 🆘 Troubleshooting

### "Repository not found"
- Verify repository URL: https://github.com/rogerjs93/Hibriddatatransfer
- Check you have push access
- Ensure repository exists on GitHub

### "Failed to push"
```bash
# If remote has content, you may need to force push (⚠️ use carefully)
git push -u origin main --force

# Or merge remote changes first
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### GitHub Pages not working
- Check Settings > Pages is enabled
- Ensure correct branch is selected
- Wait a few minutes for deployment
- Clear browser cache
- Check repository is public (Pages requires public repo for free tier)

---

## 📋 Complete Command Sequence

Here's the complete sequence of commands to run:

```bash
# 1. Navigate to project
cd c:\Users\roger\Desktop\Roger\studies\N-Neuroscience\projects\datatransfer

# 2. Verify git is initialized
git status

# 3. Add remote
git remote add origin https://github.com/rogerjs93/Hibriddatatransfer.git

# 4. Push to GitHub
git push -u origin master
# OR if using 'main' branch
git branch -M main
git push -u origin main

# 5. Done! Check GitHub repository in browser
```

---

## 🎉 After Upload

Your repository will contain:

```
Hibriddatatransfer/
├── README.md                   # Main documentation
├── PROTOCOL_SPEC.md            # Technical specification
├── QUICKSTART.md               # Getting started guide
├── ROADMAP.md                  # Implementation roadmap
├── PROJECT_SUMMARY.md          # Project summary
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
│
├── webapp/
│   ├── sender.html            # 🌐 Web sender app
│   ├── receiver.html          # 🌐 Web receiver app
│   └── README.md              # Web app documentation
│
├── implementation/
│   ├── visual_encoder.py      # Python visual encoder
│   ├── visual_decoder.py      # Python visual decoder
│   ├── audio_encoder.py       # Python audio encoder
│   └── example_transfer.py    # Example usage
│
├── architecture/
│   └── system_design.md       # Architecture details
│
└── analysis/
    └── performance_benchmarks.md  # Performance analysis
```

---

## 📱 Testing the Live Web App

Once GitHub Pages is enabled:

1. **Desktop (Sender):**
   - Navigate to: `https://rogerjs93.github.io/Hibriddatatransfer/webapp/sender.html`
   - Upload a small text file (< 10 KB for testing)
   - Start transfer
   
2. **Phone (Receiver):**
   - Navigate to: `https://rogerjs93.github.io/Hibriddatatransfer/webapp/receiver.html`
   - Allow camera access
   - Point at desktop screen
   - Watch frames being detected

**Tips for best results:**
- Use good lighting
- Keep phone steady (1-2 meters from screen)
- Use "Balanced" or "Robust" mode for first test
- Start with small files (< 50 KB)

---

## 🔄 Making Updates

After initial upload, to push changes:

```bash
# Make changes to files
# ...

# Stage changes
git add .

# Commit
git commit -m "Description of changes"

# Push
git push
```

---

**Need help?** Open an issue on GitHub or check the documentation!
