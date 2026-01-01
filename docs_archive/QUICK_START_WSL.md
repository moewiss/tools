# Quick Start Guide for WSL/Linux

## ✅ Problem Fixed!

I've made the following changes:
1. **Changed port from 5000 to 5001** (port 5000 was already in use)
2. **Created setup scripts** for virtual environment (fixes the externally-managed-environment error)
3. **Created helper scripts** to manage the application

---

## 🚀 Quick Start (Choose One Method)

### **Method 1: Automatic Setup & Start (Recommended)**

Run this single command:

```bash
bash setup_and_start.sh
```

This will:
- Create a virtual environment (venv)
- Install all dependencies
- Start the web server on port 5001

Then open your browser to: **http://localhost:5001**

---

### **Method 2: Manual Setup**

If you prefer to do it manually:

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate it
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the app
python3 web_app.py
```

Then open: **http://localhost:5001**

---

### **Method 3: Kill Port 5000 Process (Use Original Port)**

If you want to use port 5000 instead:

```bash
# Find and kill the process using port 5000
bash kill_port_5000.sh

# Then start normally
bash setup_and_start.sh
```

---

## 🔄 Starting the App Later

After the initial setup, just run:

```bash
bash start_app.sh
```

This activates the virtual environment and starts the server.

---

## 🛑 Stopping the Server

Press `CTRL+C` in the terminal where the server is running.

---

## 🔧 Troubleshooting

### "Permission denied" when running scripts

Make them executable:

```bash
chmod +x setup_and_start.sh kill_port_5000.sh start_app.sh
```

### "python3-venv not found"

Install it:

```bash
sudo apt update
sudo apt install python3-venv python3-pip
```

### "Port already in use"

The app is now using port **5001** instead of 5000, so this should be fixed!

If you still have issues, run:

```bash
bash kill_port_5000.sh  # Kill process on 5000
# OR
lsof -ti:5001 | xargs kill -9  # Kill process on 5001
```

---

## 📝 Important Notes

1. **Always activate the virtual environment** before running the app
2. The app now runs on **port 5001** (changed from 5000)
3. Access URLs:
   - Local: http://localhost:5001
   - Network: http://172.18.62.164:5001 (or your IP)

---

## 🎯 Next Steps

1. Run `bash setup_and_start.sh`
2. Open http://localhost:5001 in your browser
3. Enjoy all the tools! 🎉

