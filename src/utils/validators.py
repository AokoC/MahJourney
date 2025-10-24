from collections import Counter
import re

class Validator:
    @staticmethod
    def _parse_tiles_from_string(hands_text):
        """Get tiles[] from hands string"""

        tiles = []
        current_numbers = ""
        
        for char in hands_text:
            if char in 'mpsz':
                if current_numbers:
                    for num in current_numbers:
                        tiles.append(num + char)
                    current_numbers = ""
            elif char in '0123456789':
                current_numbers += char
        
        return tiles
    
    @staticmethod
    def _fivedize_zero(tile):
        """Turn 0 into 5, for pon and kan"""

        num = tile[0]
        suit = tile[1]
        fivedized = '5' if num == '0' else num
        return fivedized + suit

    @staticmethod
    def can_ankan(hands_text):
        """Check if can ankan"""

        if not hands_text:
            return False
            
        tiles = Validator._parse_tiles_from_string(hands_text)
        
        # Must in turn
        if len(tiles) not in [2, 5, 8, 11, 14]:
            return False
            
        fivedized_tiles = [Validator._fivedize_zero(tile) for tile in tiles]
        tile_counter = Counter(fivedized_tiles)

        # Must have 4 same tiles
        has_quad = any(count == 4 for count in tile_counter.values())
        
        return has_quad

    @staticmethod
    def can_chi(hands_text):
        """Check if can chi"""

        '''print(len(hands_text))'''
        if not hands_text:
            return False
            
        tile_list = Validator._parse_tiles_from_string(hands_text)
        
        suits = {'m': [], 'p': [], 's': []}
        
        for tile in tile_list:
            num = tile[0]
            suit = tile[1]
            if suit in suits:
                fivedized_num = '5' if num == '0' else num
                suits[suit].append(int(fivedized_num))
        
        # Check m, p, s
        for suit, numbers in suits.items():
            if len(numbers) < 2:
                continue
                
            # Remove repeat tiles
            sorted_nums = sorted(set(numbers))
            
            for i in range(len(sorted_nums)):
                current = sorted_nums[i]
                
                # Check if consecutive tiles
                if (current + 1 in sorted_nums):
                    return True
                
                # Check if closed wait (?)
                if (current + 2 in sorted_nums):
                    return True
        
        return False

    @staticmethod
    def can_pon(hands_text):
        """Check if can pon"""

        if not hands_text:
            return False
            
        tile_list = Validator._parse_tiles_from_string(hands_text)

        fivedized_tiles = [Validator._fivedize_zero(tile) for tile in tile_list]
        tile_counter = Counter(fivedized_tiles)
        
        # Find out all pairs
        pairs = [tile for tile, count in tile_counter.items() if count >= 2]
        
        if not pairs:
            return False
        
        # Check if all pairs are in 4
        all_pairs_are_quads = all(tile_counter[tile] == 4 for tile in pairs)
        
        return not all_pairs_are_quads

    @staticmethod
    def can_kan(hands_text):
        """Check if can kan"""

        if not hands_text:
            return False
            
        tile_list = Validator._parse_tiles_from_string(hands_text)

        fivedized_tiles = [Validator._fivedize_zero(tile) for tile in tile_list]
        tile_counter = Counter(fivedized_tiles)
        
        # Find out all triplets
        triplets = [tile for tile, count in tile_counter.items() if count >= 3]
        
        if not triplets:
            return False
        
        # Check if all triplets are in 4
        all_triplets_are_quads = all(tile_counter[tile] == 4 for tile in triplets)
        
        return not all_triplets_are_quads
    
    '''@staticmethod
    def get_required_tiles_for_meld(hands_text, action_type):
        """Get tiles those must be used for furo, to disable them in tile selector.. @.@
        This is extremely difficult so I have given up. 
        You will need to find all possible Chi combinations, to disable tiles those "are totally not possible to be discarded" after a Chi. Which is very difficult. """

        if not hands_text:
            return []
        
        tile_list = Validator._parse_tiles_from_string(hands_text)
        normalized_tiles = [Validator._fivedize_zero(tile) for tile in tile_list]
        tile_counter = Counter(normalized_tiles)
        
        required_tiles = set()
        
        if action_type == "chi":
            # Find all possible chi
            possible_chi_tiles = Validator._find_possible_chi_combinations(tile_list)
            
            # If only 1 possible chi, they cannot be discarded after chi
            if len(possible_chi_tiles) <= 2:
                required_tiles.update(possible_chi_tiles)
            pass
        
        elif action_type == "pon":
            # Find all possible pon
            possible_pon_tiles = [tile for tile, count in tile_counter.items() 
                                if count >= 2 and count < 4]
            
            # If only 1 possible pon, they cannot be discarded after pon
            if len(possible_pon_tiles) == 1:
                pon_tile = possible_pon_tiles[0]
                for tile in tile_list:
                   if Validator._fivedize_zero(tile) == pon_tile:
                        required_tiles.add(tile)
        
        elif action_type == "kan":
            # Find all possible kan
            possible_kan_tiles = [tile for tile, count in tile_counter.items() 
                                if count >= 3 and count < 4]
            
            # If only 1 possible kan, they cannot be discarded after kan
            if len(possible_kan_tiles) == 1:
                kan_tile = possible_kan_tiles[0]
                for tile in tile_list:
                    if Validator._fivedize_zero(tile) == kan_tile:
                        required_tiles.add(tile)
        
        return list(required_tiles)''' 

    @staticmethod
    def validate_hands_format(hands_text):
        """Validate hands format (similar to Upload)"""

        if not re.match(r'^[0-9mpsz]*$', hands_text):
            return {"valid": False, "error_type": "format", "total_tiles": 0}
        
        parts = []
        current_part = ""
        
        for char in hands_text:
            if char in 'mpsz':
                if current_part:
                    parts.append(current_part + char)
                    current_part = ""
                else:
                    return {"valid": False, "error_type": "format", "total_tiles": 0}
            elif char in '0123456789':
                current_part += char
            else:
                return {"valid": False, "error_type": "format", "total_tiles": 0}
        
        if current_part:
            return {"valid": False, "error_type": "format", "total_tiles": 0}
        
        total_tiles = 0
        all_numbers = []
        
        for part in parts:
            suit = part[-1]
            numbers = part[:-1]
            
            if suit == 'z':
                for num in numbers:
                    if num in '089':
                        return {"valid": False, "error_type": "honor", "total_tiles": 0}
                    if not '1' <= num <= '7':
                        return {"valid": False, "error_type": "format", "total_tiles": 0}
            
            counter = Counter(numbers)
            for num, count in counter.items():
                if count > 4:
                    return {"valid": False, "error_type": "duplicate", "total_tiles": 0}
            
            total_tiles += len(numbers)
            all_numbers.extend(numbers)
        
        valid_counts = [1, 2, 4, 5, 7, 8, 10, 11, 13, 14]
        if total_tiles not in valid_counts:
            return {"valid": False, "error_type": "count", "total_tiles": total_tiles}
        
        suit_counter = Counter([part[-1] for part in parts])
        
        duplicate_suits = [suit for suit, count in suit_counter.items() if count > 1]
        
        if duplicate_suits:
            for suit, count in suit_counter.items():
                if count > 2:
                    return {"valid": False, "error_type": "format", "total_tiles": total_tiles}
                
            if total_tiles not in [2, 5, 8, 11, 14]:
                return {"valid": False, "error_type": "drawError", "total_tiles": total_tiles}
            
            if len(duplicate_suits) > 1:
                return {"valid": False, "error_type": "format", "total_tiles": total_tiles}
            
            duplicate_suit = duplicate_suits[0]
            duplicate_parts = [part for part in parts if part[-1] == duplicate_suit]
            
            if parts[-1][-1] != duplicate_suit:
                return {"valid": False, "error_type": "format", "total_tiles": total_tiles}
            
            last_part = parts[-1]
            if len(last_part) != 2:
                return {"valid": False, "error_type": "format", "total_tiles": total_tiles}
        
        return {"valid": True, "error_type": "", "total_tiles": total_tiles}

    @staticmethod
    def normalize_hand_tiles(hand_text):
        """Normalize hands (remove and insert the rightmost tile; for the above method and search use)"""

        if not hand_text:
            return []
        
        tiles = []
        current_numbers = ""
        
        for char in hand_text:
            if char in 'mpsz':
                if current_numbers:
                    for num in current_numbers:
                        tiles.append(num + char)
                    current_numbers = ""
            elif char in '0123456789':
                current_numbers += char
        
        def tile_sort_key(tile):
            suit_order = {'m': 0, 'p': 1, 's': 2, 'z': 3}
            num = tile[0]
            suit = tile[1]
            if num == '0':
                num = '4.5'
            return (suit_order[suit], float(num))
        
        tiles.sort(key=tile_sort_key)
        return tiles

    @staticmethod
    def parse_hand_tiles_for_display(hand_text):
        """Parse hand text into tile list for display with special hand count logic"""

        if not hand_text:
            return []
        
        tiles = []
        current_numbers = ""
        
        total_numbers = len(hand_text.replace('m', '').replace('p', '').replace('s', '').replace('z', ''))
        is_special_count = total_numbers in [2, 5, 8, 11, 14]
        
        if is_special_count and len(hand_text) >= 2:
            last_suit_index = -1
            for i in range(len(hand_text)-1, -1, -1):
                if hand_text[i] in 'mpsz':
                    last_suit_index = i
                    break
            
            if last_suit_index > 0:
                main_part = hand_text[:last_suit_index+1]
                last_tile_number = hand_text[last_suit_index-1]
                last_tile_suit = hand_text[last_suit_index]
                last_tile = last_tile_number + last_tile_suit
                
                main_tiles = []
                current_numbers = ""
                for char in main_part[:-2]:
                    if char in 'mpsz':
                        if current_numbers:
                            for num in current_numbers:
                                main_tiles.append(num + char)
                            current_numbers = ""
                    elif char in '0123456789':
                        current_numbers += char
                
                def tile_sort_key(tile):
                    suit_order = {'m': 0, 'p': 1, 's': 2, 'z': 3}
                    num = tile[0]
                    suit = tile[1]
                    if num == '0':
                        num = '4.5'
                    return (suit_order[suit], float(num))
                
                main_tiles.sort(key=tile_sort_key)
                
                return main_tiles + [last_tile]
        
        # Normal parsing (no special handling needed)
        for char in hand_text:
            if char in 'mpsz':
                if current_numbers:
                    for num in current_numbers:
                        tiles.append(num + char)
                    current_numbers = ""
            elif char in '0123456789':
                current_numbers += char
        
        # Sort normal hand tiles
        def tile_sort_key(tile):
            suit_order = {'m': 0, 'p': 1, 's': 2, 'z': 3}
            num = tile[0]
            suit = tile[1]
            if num == '0':
                num = '4.5'
            return (suit_order[suit], float(num))
        
        tiles.sort(key=tile_sort_key)
        return tiles

    @staticmethod
    def to_code(tile):
        """Turn the tiles into numbers, in order to check tenpai/agari.
        m: 1-9, p: 11-19, s: 21-29, z: 31-37"""

        if not tile or len(tile) < 2:
            return None
            
        suffix = tile[-1].lower()
        num_str = tile[:-1]
        
        try:
            num = int(num_str)
        except ValueError:
            return None
            
        if suffix == 'm' and 1 <= num <= 9:
            return num
        elif suffix == 'p' and 1 <= num <= 9:
            return 10 + num
        elif suffix == 's' and 1 <= num <= 9:
            return 20 + num
        elif suffix == 'z' and 1 <= num <= 7:
            return 30 + num
        elif suffix == 'm' and num == 0:  # 0m
            return 5 + num
        elif suffix == 'p' and num == 0:  # 0p
            return 15 + num
        elif suffix == 's' and num == 0:  # 0s
            return 25 + num
        
        return None

    @staticmethod
    def is_all_melds(cards):
        """Check if all can be melds. Use recursion to check all combinations"""

        if len(cards) == 0:
            return True
            
        cards_sorted = sorted(cards)
        
        # Check triplets
        if len(cards_sorted) >= 3 and cards_sorted[0] == cards_sorted[1] and cards_sorted[1] == cards_sorted[2]:
            if Validator.is_all_melds(cards_sorted[3:]):
                return True
        
        # Check straights
        if cards_sorted[0] <= 29 and cards_sorted[0] % 10 <= 7:
            if cards_sorted[0] + 1 in cards_sorted and cards_sorted[0] + 2 in cards_sorted:
                new_cards = cards_sorted.copy()
                new_cards.remove(cards_sorted[0])
                new_cards.remove(cards_sorted[0] + 1)
                new_cards.remove(cards_sorted[0] + 2)
                if Validator.is_all_melds(new_cards):
                    return True
                    
        return False

    @staticmethod
    def is_chiitoi(hand_codes):
        """Check if is Chiitoi (seven pairs)"""

        if len(hand_codes) != 14:
            return False
            
        counts = {}
        for code in hand_codes:
            counts[code] = counts.get(code, 0) + 1
            
        # All tiles must be in pairs, and each type can only exist once
        return all(count == 2 for count in counts.values()) and len(counts) == 7

    @staticmethod
    def is_kokushi(hand_codes):
        """Check if is kokushi (13 1/9)"""

        if len(hand_codes) != 14:
            return False
            
        orphans = [1, 9, 11, 19, 21, 29, 31, 32, 33, 34, 35, 36, 37]
        counts = {}
        for code in hand_codes:
            counts[code] = counts.get(code, 0) + 1
            
        # Must include all 1/9, and one type is in pair
        has_duplicate = False
        for orphan in orphans:
            if orphan not in counts:
                return False
            if counts[orphan] == 2:
                has_duplicate = True
            elif counts[orphan] != 1:
                return False
                
        return has_duplicate

    @staticmethod
    def is_agari(hand_codes):
        """Check if is agari"""

        n = len(hand_codes)
        if n not in [2, 5, 8, 11, 14]:
            return False

        if n == 14:
            if Validator.is_chiitoi(hand_codes):
                return True
            if Validator.is_kokushi(hand_codes):
                return True
        
        # How many mentsu needs to be formed?
        m = (n - 2) // 3
        codes_sorted = sorted(hand_codes)
        
        # Try all
        for i in set(codes_sorted):
            if codes_sorted.count(i) >= 2:
                new_codes = codes_sorted.copy()
                new_codes.remove(i)
                new_codes.remove(i)
                if Validator.is_all_melds(new_codes):
                    return True
        return False

    @staticmethod
    def is_tenpai(hand_codes):
        """Check if is tenpai, by adding all tiles to it, and then check if is agari"""

        n = len(hand_codes)
        if n not in [1, 4, 7, 10, 13]:
            return False
            
        all_tiles = (
            list(range(1, 10)) +
            list(range(11, 20)) +
            list(range(21, 30)) +
            list(range(31, 38))
        )

        new_hand = []
        
        for tile in all_tiles:
            # Check if that tile can be added
            if hand_codes.count(tile) < 4:
                new_hand = hand_codes + [tile]
            if Validator.is_agari(new_hand):
                return True
        return False
    
    @staticmethod
    def check_mahjong_hand(hand_list):
        """The vinegar of jiaozi. It is really useless besides validation check... I hate validations.
        Returns: 
        3 - Agari in turn
        2 - Tenpai in turn
        1 - Tenpai out of turn (also is agari-able, since we don't have other players' discard info.)
        0 - NouTen"""

        if not hand_list:
            return 0
            
        n = len(hand_list)
        
        hand_codes = []
        for tile in hand_list:
            code = Validator.to_code(tile)
            if code is None:
                return 0
            hand_codes.append(code)
        
        # In turn
        if n in [2, 5, 8, 11, 14]:
            if Validator.is_agari(hand_codes):
                return 3
            else:
                # Check if tenpai in turn: Remove tile one by one to create new hands, and check tenpai for each hands.
                for tile in set(hand_codes):
                    new_hand = hand_codes.copy()
                    new_hand.remove(tile)
                    if Validator.is_tenpai(new_hand):
                        return 2
                return 0
                
        # Out of turn      
        elif n in [1, 4, 7, 10, 13]:
            if Validator.is_tenpai(hand_codes):
                return 1
            else:
                return 0
                
        else:
            return 0