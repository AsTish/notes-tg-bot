# **📒 notes-tg-bot**  

**notes-tg-bot** is a simple Telegram bot for managing notes and folders using the **Aiogram** framework. Users can create, view, and delete notes, organize them into folders, and interact with the bot via commands and inline buttons.  

---

## **🚀 Features**  
- 📂 Folder management – Create, browse, and delete folders for notes.
- 📝 Note management – Create, view, and delete notes.
- 🔍 **Quick access** – View all notes or folders with a single command.  
- 🛠 **Built with Aiogram** – Uses `aiogram` for efficient and scalable Telegram bot development.  
- 📦 **Environment management with Pipenv** – Ensures dependency isolation and simplified package management.  

---

## **📥 Installation**  

### **1. Clone the repository**  
```sh
git clone https://github.com/AsTish/notes-tg-bot.git
cd notes-tg-bot
```

### **2. Install dependencies using Pipenv**  
```sh
pipenv install
```

### **3. Set up environment variables**  
Create a `.env` file and add your **Telegram Bot API Token**:  
```sh
BOT_TOKEN=your-telegram-bot-token
```

### **4. Activate the virtual environment**  
```sh
pipenv shell
```

### **5. Run the bot**  
```sh
cd notes_project
cd bot
python bot.py
```
