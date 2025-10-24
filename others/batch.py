import json
import uuid
import datetime
import sys
import os

"""If you want to use this batch uploader, make sure you edit the UUID method below, to avoid collision when you import.
You may need to handle your unique pattern for the UUID, Title and Time.
Anyways, read the code before use."""

def parse_input_line(line):
    """xxx.txt input line Format: 
    e w 1 0 7 2z 6778p1122345s77z0p 2s
    Where: e is wind, w is self wind, 1 0 7 is game/honba/turn,
    6778p1122345s77z0p is hand (with 0p just drawed), 2s is answer
    *If there are special questions that includes other answer choice, or melds, you may need to mark them down and edit them one by one after batch uploading. """

    parts = line.strip().split()
    if len(parts) != 8:
        raise ValueError(f"Wrong format, need 8 parts but only {len(parts)}: {line}")
    
    return {
        'wind': parts[0],
        'self_wind': parts[1],
        'game': parts[2],
        'honba': parts[3],
        'turn': parts[4],
        'dora': parts[5],
        'hands': parts[6],
        'answer_input': parts[7]
    }

def convert_wind(wind_letter):
    """Convert wind letter to full name"""
    
    wind_map = {
        'E': 'east',
        'S': 'south', 
        'W': 'west',
        'N': 'north'
    }
    return wind_map.get(wind_letter.upper(), 'east')

def generate_uuid(sequence):
    base_uuid = uuid.UUID('00000000-0000-4000-8000-000000000001')
    new_uuid = uuid.UUID(int=base_uuid.int + sequence)
    return str(new_uuid)

def format_entry_data(entry_data):
    """Format entry data according to data_manager.py's save format"""
    
    def safe_str(value):
        if value is None:
            return '""'
        escaped = str(value).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
        return f'"{escaped}"'
    
    entry_lines = []
    entry_id = entry_data['id']

    # Specifically, for "How-to-cut 300" to use:
    entry_lines.append(f'  "{entry_id}": {{')
    entry_lines.append(f'    "create_time": {safe_str(entry_data.get("create_time", ""))}, "title": {safe_str(entry_data.get("title", ""))},')
    entry_lines.append(f'    "encounter": {entry_data.get("encounter", 0)}, "correct": {entry_data.get("correct", 0)}, "accuracy": {safe_str(entry_data.get("accuracy", "N/A %"))},')
    entry_lines.append(f'    "source": {safe_str(entry_data.get("source", ""))}, "players": {safe_str(entry_data.get("players", ""))}, "difficulty": {entry_data.get("difficulty", 0)},')
    entry_lines.append(f'    "wind": {safe_str(entry_data.get("wind", ""))}, "self_wind": {safe_str(entry_data.get("self_wind", ""))}, "game": {safe_str(entry_data.get("game", ""))}, "honba": {safe_str(entry_data.get("honba", ""))}, "turn": {safe_str(entry_data.get("turn", ""))},')
    entry_lines.append(f'    "dora": {safe_str(entry_data.get("dora", ""))}, "hands": {safe_str(entry_data.get("hands", ""))}, "answer_action": {safe_str(entry_data.get("answer_action", ""))}, "answer_input": {safe_str(entry_data.get("answer_input", ""))},')
    entry_lines.append(f'    "intro": {safe_str(entry_data.get("intro", ""))}, "notes": {safe_str(entry_data.get("notes", ""))},')
    entry_lines.append(f'    "image_filename": {safe_str(entry_data.get("image_filename", ""))}, "id": {safe_str(entry_data.get("id", ""))} }}')
    
    return '\n'.join(entry_lines)

def main():
    if len(sys.argv) != 2:
        print("How to use: Write the following line in terminal\npy batch.py <Name>.txt")
        sys.exit(1)
    
    input_filename = sys.argv[1]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_filename = os.path.join(script_dir, "data.json")
    
    if not os.path.exists(input_filename):
        print(f"File '{input_filename}' not exist")
        sys.exit(1)
    
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
   
    base_time = datetime.datetime(2025, 1, 1, 0, 0, 1)

    entries_data = {}
    
    for i, line in enumerate(lines):
        if not line.strip():
            continue
            
        try:
            data = parse_input_line(line)
            
            uid = generate_uuid(i)
            
            current_time = base_time + datetime.timedelta(seconds=i)
            title_num = str(i + 1).zfill(3)
            
            # Convert wind letters to full names
            wind_full = convert_wind(data['wind'])
            self_wind_full = convert_wind(data['self_wind'])
            
            entry = {
                "create_time": current_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "title": f"何切三百 {title_num}/300",
                "encounter": 0,
                "correct": 0,
                "accuracy": "N/A %",
                "source": "source.exercises",
                "players": "players.four",
                "difficulty": 0,
                "wind": f"info.{wind_full}",
                "self_wind": f"info.{self_wind_full}",
                "game": data['game'],
                "honba": data['honba'],
                "turn": data['turn'],
                "dora": data['dora'],
                "hands": data['hands'],
                "answer_action": "answer.discard",
                "answer_input": data['answer_input'],
                "intro": "/",
                "notes": "/",
                "image_filename": "",
                "id": uid
            }
            
            entries_data[uid] = entry
            
        except Exception as e:
            print(f"Error when Line {i+1}: {e}")
            print(f"Content: {line}")
            continue

    try:
        # Format output according to data_manager.py's style
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write('{\n')
            entries = []
            for entry_id, entry_data in entries_data.items():
                formatted_entry = format_entry_data(entry_data)
                entries.append(formatted_entry)
            
            f.write(',\n'.join(entries))
            f.write('\n}')
            
        print(f"Successfully gen {len(entries_data)} entries to {output_filename}")
            
    except Exception as e:
        print(f"Error when writing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()