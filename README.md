# Evochron Legacy SE Translation Helper

A powerful Python tool for translating Evochron Legacy SE game files. Easily extract, translate, and apply translations while preserving the game's file structure.

## 🌟 Features

- Extract text from game files in `media/` directory
- Support for multiple file types with different formats
- Built-in Google Translate integration
- Preserves original file structure
- User-friendly console interface
- Automatic backup system

## 📋 Requirements

- Python 3.7+
- pip (Python package manager)
- Game files in `media/` directory

## 🚀 Quick Start

1. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```

2. **Prepare Your Game Files**
   - Navigate to your Evochron Legacy SE installation directory
   - Locate the `media` folder containing the game files
   - Place `translate_helper.py` in the same directory as the `media` folder

3. **Run the Tool**
   ```bash
   python translate_helper.py
   ```

## 🎮 Usage Guide

### 1. Extracting Text
- Select option 1 to extract text from all supported files
- JSON files will be created in the `translation` directory
- Each file corresponds to a game file in the `media` folder

### 2. Translating Text
- **Manual**: Edit the JSON files in the `translation` directory
- **Auto-translate**: Use option 3 for Google Translate

### 3. Applying Translations
- Select option 2 to apply your translations
- Original files will be backed up with `.bak` extension
- Check the console for progress and any warnings

## 📁 File Locations

Game files are located in the `media/` directory:
- `media/text.dat`
- `media/systemdata.dat`
- `media/itemdata.dat`
- `media/optionsdata.dat`
- `media/techdata.dat`
- `media/traintext.sw`

## ⚠️ Important Notes

1. **Backup Your Game Files**
   - The tool creates `.bak` files, but it's good practice to create your own backup

2. **Auto Translation Quality**
   - Auto-translation provides a good starting point
   - Review all translations for accuracy and context
   - Some game-specific terms may need manual adjustment
3. **File Permissions**
   - Ensure you have write permissions for the game directory
   - Run as administrator if needed

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## ⚠️ Disclaimer
At this time the tool is not complete and may have errors such as text that does not grab well.

This is an fan tool not affiliated with or endorsed by StarWraith 3D Games LLC
