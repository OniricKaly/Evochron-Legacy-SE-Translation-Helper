import os
import json
import re
import time
from pathlib import Path
from deep_translator import GoogleTranslator
from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel
from rich import print as rprint

# Initialize console
console = Console()

class GameTextExtractor:
    def __init__(self, game_dir):
        self.game_dir = Path(game_dir)
        self.translation_dir = self.game_dir / 'translation'
        self.translation_dir.mkdir(exist_ok=True)
        
        # Supported game files and their handlers
        self.supported_files = [
            'text.dat',
            'systemdata.dat',
            'itemdata.dat',
            'optionsdata.dat',
            'techdata.dat',
            'traintext.sw'
        ]
        
        # File type detection patterns
        self.file_patterns = {
            'text': r'^\d+=',
            'item': r'^\+Item',
            'desc': r'^\+Desc=',
            'tech': r'^\+[A-Za-z]',
            'system': r'^\-?\d+\s*$|^[A-Za-z ]+:'
        }
        
    def _detect_file_type(self, content):
        """Detect file type based on content patterns"""
        for line in content.split('\n')[:10]:  # Check first 10 lines
            for file_type, pattern in self.file_patterns.items():
                if re.search(pattern, line):
                    return file_type
        return 'unknown'
    
    def _parse_text_file(self, content):
        """Parse text.dat format (key=value)"""
        entries = []
        for line in content.split('\n'):
            line = line.strip()
            if not line or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if value and not value.startswith('<'):
                entries.append({
                    'key': key,
                    'original': value,
                    'translated': '',
                    'type': 'text'
                })
        return entries
    
    def _parse_desc_file(self, content):
        """Parse optionsdata.dat format (+Desc= sections)"""
        entries = []
        sections = re.split(r'(\+Desc=\d+\nLines=\d+\n)', content)
        for i in range(1, len(sections), 2):
            if i + 1 >= len(sections):
                continue
            header = sections[i].strip()
            text = sections[i+1].strip()
            if text:
                entries.append({
                    'key': header.split('\n')[0],
                    'original': text,
                    'translated': '',
                    'type': 'desc'
                })
        return entries
    
    def _parse_tech_file(self, content):
        """Parse techdata.dat format (+Section with multi-line content)"""
        entries = []
        # Split by sections starting with + followed by letters
        sections = re.split(r'(\+[A-Za-z0-9]+\nLines=\d+\n)', content)
        for i in range(1, len(sections), 2):
            if i + 1 >= len(sections):
                continue
            header = sections[i].strip()
            text = sections[i+1].strip()
            if text:
                # First line is usually the title
                lines = text.split('\n')
                title = lines[0]
                description = '\n'.join(lines[1:]) if len(lines) > 1 else ''
                
                entries.append({
                    'key': header.split('\n')[0],
                    'title': title,
                    'original': description,
                    'translated': '',
                    'type': 'tech'
                })
        return entries
    
    def _parse_item_file(self, content):
        """Parse itemdata.dat format (+Item sections)"""
        entries = []
        sections = re.split(r'(\+Item\d+\nLines=\d+\n)', content)
        for i in range(1, len(sections), 2):
            if i + 1 >= len(sections):
                continue
            header = sections[i].strip()
            text = sections[i+1].strip()
            if text:
                entries.append({
                    'key': header.split('\n')[0],
                    'original': text,
                    'translated': '',
                    'type': 'item'
                })
        return entries
    
    def _parse_system_file(self, content):
        """Parse systemdata.dat format (freeform with sections)"""
        entries = []
        sections = re.split(r'(\-?\d+\s*\n\d+\s*\n)', content)
        
        for i in range(1, len(sections), 2):
            if i + 1 >= len(sections):
                continue
                
            section_header = sections[i].strip()
            section_content = sections[i+1].strip()
            
            if not section_content:
                continue
                
            # Split into lines and process each line
            lines = section_content.split('\n')
            system_name = lines[0].replace('System Information:', '').strip()
            
            # Add the system name as a separate entry
            if system_name and 'System Information:' in lines[0]:
                entries.append({
                    'key': f'system_{len(entries)}_name',
                    'original': system_name,
                    'translated': '',
                    'type': 'system_name'
                })
                
                # Add the system info as another entry
                info_lines = []
                for line in lines[1:]:
                    line = line.strip()
                    if line and not line.startswith('Alerts:'):
                        info_lines.append(line)
                
                if info_lines:
                    entries.append({
                        'key': f'system_{len(entries)-1}_info',
                        'original': '\n'.join(info_lines),
                        'translated': '',
                        'type': 'system_info'
                    })
            else:
                # For other sections, add as is
                entries.append({
                    'key': f'system_{len(entries)}',
                    'original': section_content,
                    'translated': '',
                    'type': 'system_other'
                })
            
        return entries
        
    def _parse_traintext_file(self, content):
        """Parse traintext.sw format (tutorial text with indicators)"""
        entries = []
        # Split by section markers (lines starting with - followed by a number)
        sections = re.split(r'(\-\d+\s*\n\d+\s*\n(?:Indicators\=[0-9]\n)?(?:WaitEnter\=[0-9]\n)?)', content)
        
        current_section = None
        
        for i in range(1, len(sections), 2):
            if i + 1 >= len(sections):
                continue
                
            section_header = sections[i].strip()
            section_content = sections[i+1].strip()
            
            if not section_content:
                continue
                
            # Skip indicator lines at the start of the content
            lines = section_content.split('\n')
            text_lines = []
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('Indicators=') or line.startswith('WaitEnter='):
                    continue
                text_lines.append(line)
                
            if not text_lines:
                continue
                
            # Join lines with spaces, preserving line breaks where needed
            text = ' '.join(text_lines)
            
            # Create entry
            entries.append({
                'key': f'train_{len(entries)}',
                'original': text,
                'translated': '',
                'type': 'tutorial'
            })
            
        return entries
    
    def extract_text(self, filename):
        """Extract translatable text from a file"""
        filepath = self.game_dir / filename
        if not filepath.exists():
            console.print(f"[red]File not found: {filepath}[/]")
            return
            
        console.print(f"[cyan]Extracting text from {filename}...[/]")
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            entries = []
            file_type = None
            
            # Detect file type and parse accordingly
            if 'text.dat' in filename:
                entries = self._parse_text_file(content)
                file_type = 'text'
            elif 'optionsdata.dat' in filename:
                entries = self._parse_desc_file(content)
                file_type = 'desc'
            elif 'techdata.dat' in filename:
                entries = self._parse_tech_file(content)
                file_type = 'tech'
            elif 'itemdata.dat' in filename:
                entries = self._parse_item_file(content)
                file_type = 'item'
            elif 'systemdata.dat' in filename:
                entries = self._parse_system_file(content)
                file_type = 'system'
            elif 'traintext.sw' in filename:
                entries = self._parse_traintext_file(content)
                file_type = 'tutorial'
            else:
                console.print(f"[yellow]Unsupported file type: {filename}[/]")
                return
                
            if not entries:
                console.print(f"No translatable text found in {filename}")
                return
                
            # Create translation directory if it doesn't exist
            self.translation_dir.mkdir(exist_ok=True)
            
            # Prepare output data with metadata
            output_data = {
                'metadata': {
                    'file_type': file_type,
                    'source_file': filename,
                    'extraction_date': time.strftime('%Y-%m-%d %H:%M:%S')
                },
                'entries': entries
            }
            
            # Save extracted text to JSON
            output_file = self.translation_dir / f"{filename}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
                
            console.print(f"✓ Extracted {len(entries)} entries to {output_file}")
            
        except Exception as e:
            console.print(f"[red]Error processing {filename}: {str(e)}[/]", style="bold")
            import traceback
            console.print(traceback.format_exc())
    
    def _apply_text_dat(self, filepath, translations):
        """Apply translations to text.dat files"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
            for line in lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    if key in translations:
                        line = f"{key}={translations[key]}\n"
                f.write(line)
    
    def _apply_sectioned_file(self, filepath, translations, section_pattern):
        """Apply translations to files with sections (items, desc, tech)"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        sections = re.split(section_pattern, content)
        modified = False
        
        for i in range(1, len(sections), 2):
            if i + 1 >= len(sections):
                continue
                
            section_header = sections[i].strip()
            section_content = sections[i+1]
            
            # Get the section key (first line of the header)
            section_key = section_header.split('\n')[0].strip()
            
            if section_key in translations:
                # For tech files, we might have both title and description
                if 'title' in translations[section_key]:
                    lines = section_content.split('\n')
                    if lines:
                        lines[0] = translations[section_key]['title']
                        if 'description' in translations[section_key]:
                            lines = [lines[0]] + translations[section_key]['description'].split('\n')
                        sections[i+1] = '\n'.join(lines)
                        modified = True
                else:
                    sections[i+1] = translations[section_key] + '\n'
                    modified = True
        
        if modified:
            with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(''.join(sections))
    
    def _apply_system_dat(self, filepath, translations):
        """Apply translations to systemdata.dat files"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        sections = content.split('\n\n')
        modified = False
        
        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue
                
            key = f'system_{i}'
            if key in translations:
                sections[i] = translations[key]
                modified = True
        
        if modified:
            with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                f.write('\n\n'.join(sections) + '\n')
    
    def apply_translation(self, filename):
        """Apply translated text back to original file"""
        json_file = self.translation_dir / f"{filename}.json"
        if not json_file.exists():
            console.print(f"[red]Translation file not found: {json_file}[/]")
            return
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get the entries and metadata
            entries = data.get('entries', [])
            file_type = data.get('metadata', {}).get('file_type', '')
            
            # Create a dictionary of translations for quick lookup
            translations = {}
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                
                key = entry.get('key')
                translated = entry.get('translated', '').strip()
                
                if not key or not translated:
                    continue
                
                # Handle different file types
                if file_type == 'tech':
                    title = entry.get('title', '').strip()
                    if title and translated:
                        if key not in translations:
                            translations[key] = {}
                        translations[key]['title'] = translated
                    
                    desc = entry.get('original', '').strip()
                    if desc and translated and 'title' not in translations[key]:
                        if key not in translations:
                            translations[key] = {}
                        translations[key]['description'] = translated
                else:
                    translations[key] = translated
            
            if not translations:
                console.print("[yellow]No valid translations found to apply.[/]")
                return
                
            console.print(f"[cyan]Found {len(translations)} translations to apply...[/]")
            
            # Create backup of original file
            original_file = self.game_dir / filename
            backup_file = self.game_dir / f"{filename}.bak"
            
            if not original_file.exists():
                console.print(f"[red]Original file not found: {original_file}[/]")
                return
                
            import shutil
            shutil.copy2(original_file, backup_file)
            console.print(f"[green]✓ Created backup: {backup_file}[/]")
            
            # Apply translations based on file type
            if 'text.dat' in filename or file_type == 'text':
                self._apply_text_dat(original_file, translations)
            elif 'optionsdata.dat' in filename or file_type == 'desc':
                self._apply_sectioned_file(original_file, translations, r'(\+Desc=\d+\nLines=\d+\n)')
            elif 'techdata.dat' in filename or file_type == 'tech':
                self._apply_sectioned_file(original_file, translations, r'(\+[A-Za-z0-9]+\nLines=\d+\n)')
            elif 'itemdata.dat' in filename or file_type == 'item':
                self._apply_sectioned_file(original_file, translations, r'(\+Item\d+\nLines=\d+\n)')
            elif 'systemdata.dat' in filename or file_type == 'system':
                self._apply_system_dat(original_file, translations)
            else:
                console.print(f"[yellow]Unsupported file type for applying translations: {filename}[/]")
                return
            
            console.print(f"[green]✓ Successfully applied translations to {filename}[/]")
                
        except json.JSONDecodeError as e:
            console.print(f"[red]Error reading translation file {json_file}: Invalid JSON format[/]")
            console.print(f"Error details: {str(e)}")
        except Exception as e:
            console.print(f"[red]Error processing translation file {json_file}: {str(e)}[/]")
            import traceback
            console.print(traceback.format_exc())
            
        print(f"Applied translations to {original_file}")
    
    def _apply_text_dat(self, filepath, translations):
        """Apply translations to text.dat files"""
        lines = []
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    if key in translations:
                        line = f"{key}={translations[key]}\n"
                lines.append(line)
        
        with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
            f.writelines(lines)
    
    def _apply_system_dat(self, filepath, translations):
        """Apply translations to system data files"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # This is a simplified approach - may need adjustment based on actual file structure
        for i in range(len(translations)):
            key = f"system_{i}"
            if key in translations:
                content = content.replace(translations[key], translations[key])
        
        with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(content)
    
    def _apply_item_dat(self, filepath, translations):
        """Apply translations to item data files"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Split by +Item sections
        sections = re.split(r'(\+Item\d+\nLines=\d+\n)', content)
        
        for i in range(1, len(sections), 2):
            if i + 1 >= len(sections):
                break
                
            item_id = sections[i].split('\n')[0]
            if item_id in translations:
                # Replace the content after the item header
                sections[i+1] = translations[item_id] + '\n\n'
        
        # Rebuild content
        content = ''.join(sections)
        
        with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(content)

    def auto_translate(self, source_lang='en', target_lang='es'):
        """Automatically translate extracted text using Google Translate"""
        console.rule("[bold blue]Auto-Translation Tool[/]")
        
        # Get all JSON files in translation directory
        translation_files = list(self.translation_dir.glob('*.json'))
        if not translation_files:
            console.print("[red]No translation files found. Please extract text first (option 1).[/]")
            return
        
        console.print(f"Found {len(translation_files)} translation files to process.")
        
        # Initialize translator
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        
        total_translated = 0
        total_entries = 0
        
        # Process each file
        for file_path in translation_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                total_entries += len(data)
                
                with Progress() as progress:
                    task = progress.add_task(f"[cyan]Translating {file_path.name}...", total=len(data))
                    
                    for i, entry in enumerate(data):
                        # Skip already translated entries
                        if not entry.get('translated') and entry.get('original'):
                            try:
                                # Translate the text
                                translated = translator.translate(entry['original'])
                                entry['translated'] = translated
                                total_translated += 1
                                
                                # Add a small delay to avoid hitting rate limits
                                time.sleep(0.5)
                                
                            except Exception as e:
                                console.print(f"[yellow]Warning: Could not translate entry {i}: {str(e)}[/]")
                                entry['translated'] = ""
                        
                        progress.update(task, advance=1)
                
                # Save the updated translations
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                console.print(f"[green]✓ Successfully processed {file_path.name}[/]")
                
            except Exception as e:
                console.print(f"[red]Error processing {file_path}: {str(e)}[/]")
        
        console.rule("[bold green]Translation Complete[/]")
        console.print(f"Translated {total_translated} out of {total_entries} entries.")
        console.print(f"Translation files updated in: {self.translation_dir}")

def display_banner():
    """Display a nice banner"""
    banner = """
    ╔══════════════════════════════════════════════╗
    ║   [bold blue]Evochron Legacy SE Translation Helper[/]      ║
    ║   [italic]Automatic Translation Tool[/]                 ║
    ╚══════════════════════════════════════════════╝
    """
    console.print(Panel.fit(banner, style="blue"))

def main():
    # Set up the extractor with the game directory
    game_dir = os.path.dirname(os.path.abspath(__file__))
    extractor = GameTextExtractor(game_dir)
    
    display_banner()
    
    while True:
        console.rule("Main Menu")
        console.print("1. [cyan]Extract text[/] for translation")
        console.print("2. [green]Apply translations[/] to game files")
        console.print("3. [yellow]Auto-translate[/] using Google Translate")
        console.print("4. [red]Exit[/]")
        
        choice = console.input("\nSelect an option (1-4): ").strip()
        
        if choice == '1':
            console.rule("Extracting Text")
            processed_files = 0
            for filename in extractor.supported_files:
                filepath = extractor.game_dir / filename
                if filepath.exists():
                    extractor.extract_text(filename)
                    processed_files += 1
                else:
                    console.print(f"[yellow]File not found, skipping: {filename}[/]")
            
            if processed_files > 0:
                console.print("\n[bold green]✓ Extraction complete![/]")
                console.print("Translation files have been created in the 'translation' directory.")
                console.print("You can now use option 3 for auto-translation or edit the JSON files manually.")
            else:
                console.print("\n[red]No files were processed. Make sure the game files are in the correct directory.[/]")
            
        elif choice == '2':
            console.rule("Applying Translations")
            processed_files = 0
            for filename in extractor.supported_files:
                json_file = extractor.translation_dir / f"{filename}.json"
                if json_file.exists():
                    extractor.apply_translation(filename)
                    processed_files += 1
                else:
                    console.print(f"[yellow]Translation file not found, skipping: {filename}.json[/]")
            
            if processed_files > 0:
                console.print("\n[bold green]✓ Translations applied successfully![/]")
                console.print("Original files were backed up with .bak extension.")
            else:
                console.print("\n[red]No translation files found. Please extract text first (option 1).[/]")
            
        elif choice == '3':
            console.rule("Auto-Translation")
            console.print("This will automatically translate all extracted text using Google Translate.")
            console.print("Note: Automatic translation may not be perfect. Review the results before applying.")
            
            source_lang = console.input("Source language (e.g., 'en' for English): ").strip() or 'en'
            target_lang = console.input("Target language (e.g., 'es' for Spanish): ").strip() or 'es'
            
            if console.input("Start translation? (y/n): ").lower() == 'y':
                extractor.auto_translate(source_lang, target_lang)
                
        elif choice == '4':
            console.print("\n[bold]Goodbye![/]")
            break
            
        else:
            console.print("[red]Invalid option. Please select a number between 1-4.[/]")
        
        if choice in ['1', '2', '3']:
            input("\nPress Enter to return to the main menu...")

if __name__ == "__main__":
    main()
