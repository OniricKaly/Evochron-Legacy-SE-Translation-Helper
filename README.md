# Evochron Legacy SE Translation Helper

A Python-based tool for extracting, translating, and applying translations to Evochron Legacy SE game files. This tool simplifies the process of localizing the game by providing an easy way to manage game text.

## Features

- Extract text from various game files (`text.dat`, `systemdata.dat`, `itemdata.dat`, `optionsdata.dat`, `techdata.dat`, `traintext.sw`)
- Support for multiple file formats and structures
- Built-in Google Translate integration for automatic translations
- Preserves original file structure when applying translations
- User-friendly console interface with progress tracking
- Creates backups of original files before making changes

## Requirements

- Python 3.7 or higher
- pip (Python package manager)

## Installation

1. Clone or download this repository
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Place the script in your Evochron Legacy SE game directory (where the `.dat` files are located)
2. Run the script:
   ```bash
   python translate_helper.py
   ```
3. Follow the on-screen menu:
   - **Option 1**: Extract text from game files (creates JSON files in the `translation` directory)
   - **Option 2**: Apply translations from JSON files back to game files
   - **Option 3**: Auto-translate extracted text using Google Translate
   - **Option 4**: Exit the program

## File Structure

- `translate_helper.py`: Main script file
- `translation/`: Directory containing extracted text in JSON format
- `*.bak`: Backup files created when applying translations

## Translation Process

1. **Extract Text**: Run the script and select option 1 to extract all translatable text
2. **Translate**:
   - Edit the JSON files in the `translation` directory manually, or
   - Use option 3 for automatic translation (requires internet connection)
3. **Apply Translations**: Run the script and select option 2 to apply your translations

## Supported File Types

- `text.dat`: General game text and UI strings
- `systemdata.dat`: System names and descriptions
- `itemdata.dat`: Item names and descriptions
- `optionsdata.dat`: Options and menu text
- `techdata.dat`: Technical data and specifications
- `traintext.sw`: Tutorial and training text

## Notes

- Always back up your game files before making changes
- The script creates `.bak` files when applying translations
- For best results, review auto-translated text before applying
- Some text might require manual adjustment for context
- At this time the tool is not complete and may have errors such as text that does not grab well.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is not affiliated with or endorsed by StarWraith 3D Games LLC. Evochron Legacy is a registered trademark of StarWraith 3D Games LLC.
