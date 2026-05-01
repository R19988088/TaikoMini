"""
姝屾洸淇℃伅鏄剧ず妯″潡 (Song Info Display Module)
璐熻矗鍦ㄦ父鎴忕晫闈㈠彸涓婅鏄剧ず姝屽悕鍜屽垎绫?"""

import pygame
from pathlib import Path
from .paths import resource_dir, asset_path


class SongInfoDisplay:
    """
    姝屾洸淇℃伅鏄剧ず绫?    
    鍔熻兘锛?    - 鍦ㄥ睆骞曞彸涓婅鏄剧ず姝屽悕鍜屽垎绫?    - 鏀寔鑷畾涔夊瓧浣撱€佸ぇ灏忋€侀鑹层€佷綅缃?    - 鏀寔鍦嗚鑳屾櫙
    """
    
    def __init__(self, screen, config_manager=None):
        """
        鍒濆鍖栨瓕鏇蹭俊鎭樉绀哄櫒
        
        鍙傛暟:
            screen: Pygame灞忓箷瀵硅薄
            config_manager: 閰嶇疆绠＄悊鍣ㄥ疄渚嬶紙鐢ㄤ簬鑾峰彇鍒嗙被鍥剧墖锛?        """
        self.screen = screen
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        self.config_manager = config_manager
        
        # 鏄剧ず浣嶇疆閰嶇疆锛堣窛绂诲彸涓婅鐨勫亸绉伙級
        self.right_margin = 20   # 鍙宠竟璺?        self.top_margin = 20     # 涓婅竟璺濓紙鐩存帴鎺у埗鏁翠釜鍖哄煙鐨刌浣嶇疆锛?        self.vertical_spacing = 10  # 姝屽悕鍜屽垎绫讳箣闂寸殑闂磋窛
        
        # 鍒嗙被鑳屾櫙閰嶇疆
        self.category_padding_x = 15  # 妯悜鍐呰竟璺?        self.category_padding_y = 0   # 绾靛悜鍐呰竟璺?        self.category_border_radius_ratio = 0.5  # 鍦嗚鍗婂緞锛堢浉瀵逛簬楂樺害锛?        self.genre_image_dir = resource_dir()  # 鍒嗙被鍥剧墖鐩綍
        
        # 瀛椾綋澶у皬閰嶇疆
        self.title_font_size = 30    # 姝屽悕瀛椾綋澶у皬
        self.category_font_size = 25  # 鍒嗙被瀛椾綋澶у皬
        
        # 鎻忚竟閰嶇疆
        self.title_outline_width = 0    # 姝屽悕鎻忚竟瀹藉害
        self.category_outline_width = 0  # 鍒嗙被鎻忚竟瀹藉害
        self.outline_color = (0, 0, 0)   # 鎻忚竟棰滆壊锛堥粦鑹诧級
        
        # 棰滆壊閰嶇疆
        self.title_color = (255, 255, 255)      # 鐧借壊
        self.category_text_color = (255, 255, 255)  # 鐧借壊
        self.default_category_bg_color = (247, 152, 36)  # 榛樿姗欒壊
        
        # 瀛椾綋
        self.font_title = None
        self.font_category = None
        
        # 鍒嗙被鍥剧墖缂撳瓨 {鍒嗙被鍚? pygame.Surface}
        self.category_image_cache = {}
        
        # 鍔犺浇瀛椾綋
        self._load_fonts()
    
    def _load_fonts(self):
        """鍔犺浇涓枃瀛椾綋"""
        # === 姝屽悕瀛椾綋锛氫娇鐢ㄩ」鐩瓧浣?===
        try:
            font_path = asset_path("lib", "res", "FZPangWaUltra-Regular.ttf")
            if font_path.exists():
                self.font_title = pygame.font.Font(str(font_path), self.title_font_size)
                print(f"Loaded title font: FZPangWaUltra-Regular.ttf (size: {self.title_font_size})")
            else:
                # 鍚庡锛氫娇鐢ㄧ郴缁熷瓧浣?                cjk_fonts = ['Microsoft YaHei', 'SimHei', 'MS Gothic', 'Meiryo', 'Arial']
                for font_name in cjk_fonts:
                    try:
                        if pygame.font.match_font(font_name):
                            self.font_title = pygame.font.SysFont(font_name, self.title_font_size)
                            print(f"Loaded title font: {font_name} (size: {self.title_font_size})")
                            break
                    except:
                        continue
                else:
                    self.font_title = pygame.font.Font(None, self.title_font_size)
        except Exception as e:
            print(f"Warning: Could not load title font: {e}")
            self.font_title = pygame.font.Font(None, self.title_font_size)
        
        # === 鍒嗙被瀛椾綋锛氫紭鍏堜娇鐢ㄦ敮鎸佲劉绗﹀彿鍜屼腑鏃ユ枃鐨勫瓧浣擄紙绮椾綋锛?==
        # Arial 鍜?Microsoft YaHei 閮芥敮鎸佲劉绗﹀彿
        category_fonts = ['Microsoft YaHei', 'Arial Unicode MS', 'Arial', 'SimHei']
        for font_name in category_fonts:
            try:
                if pygame.font.match_font(font_name):
                    self.font_category = pygame.font.SysFont(font_name, self.category_font_size, bold=True)
                    print(f"Loaded category font: {font_name} Bold (size: {self.category_font_size})")
                    return
            except:
                continue
        
        # 鏈€鍚庡悗澶囷細浣跨敤榛樿瀛椾綋
        self.font_category = pygame.font.Font(None, self.category_font_size)
        print(f"Warning: Using default category font (size: {self.category_font_size})")
    
    def _load_category_image(self, category: str) -> pygame.Surface:
        """
        鍔犺浇鍒嗙被鑳屾櫙鍥剧墖
        
        鍙傛暟:
            category: 鍒嗙被鍚嶇О
        
        杩斿洖:
            鍔犺浇鐨勫浘鐗?Surface锛屽鏋滃け璐ュ垯杩斿洖 None
        """
        if category in self.category_image_cache:
            return self.category_image_cache[category]
        
        # 浠庨厤缃幏鍙栧浘鐗囨枃浠跺悕
        if self.config_manager:
            category_info = self.config_manager.get_category_info(category)
            if category_info and category_info[2]:  # category_info = (color, b1_image_filename, genre_bg_image_filename)
                image_filename = category_info[2]  # 浣跨敤genre_bg鍥剧墖浣滀负鍒嗙被鑳屾櫙
                image_path = self.genre_image_dir / image_filename
                
                try:
                    if image_path.exists():
                        # 鍔犺浇鍥剧墖
                        image = pygame.image.load(str(image_path)).convert_alpha()
                        # 缂撳瓨鍥剧墖
                        self.category_image_cache[category] = image
                        print(f"Loaded category image: {image_filename} for {category}")
                        return image
                    else:
                        print(f"Category image not found: {image_path}")
                except Exception as e:
                    print(f"Error loading category image '{image_filename}': {e}")
        
        return None
    
    def _render_text_with_outline(self, text, font, text_color, outline_color, outline_width):
        """
        娓叉煋甯︽弿杈圭殑鏂囧瓧
        
        鍙傛暟:
            text: 鏂囧瓧鍐呭
            font: 瀛椾綋瀵硅薄
            text_color: 鏂囧瓧棰滆壊 (R, G, B)
            outline_color: 鎻忚竟棰滆壊 (R, G, B)
            outline_width: 鎻忚竟瀹藉害锛堝儚绱狅級
        
        杩斿洖:
            pygame.Surface: 娓叉煋鍚庣殑surface
        """
        # 鍒涘缓鏂囧瓧surface
        text_surface = font.render(text, True, text_color)
        w, h = text_surface.get_size()
        
        outline_surface = pygame.Surface((w + outline_width * 2, h + outline_width * 2), pygame.SRCALPHA)
        
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0:  # 璺宠繃涓績
                    if dx*dx + dy*dy <= outline_width * outline_width:  # 鍦嗗舰鎻忚竟
                        outline_text = font.render(text, True, outline_color)
                        outline_surface.blit(outline_text, (outline_width + dx, outline_width + dy))
        
        # 鍦ㄤ腑蹇冪粯鍒朵富鏂囧瓧
        outline_surface.blit(text_surface, (outline_width, outline_width))
        
        return outline_surface
    
    def update_screen_size(self, width, height):
        """
        鏇存柊灞忓箷灏哄锛堢獥鍙ｅぇ灏忔敼鍙樻椂璋冪敤锛?        
        鍙傛暟:
            width: 鏂扮殑灞忓箷瀹藉害
            height: 鏂扮殑灞忓箷楂樺害
        """
        self.screen_width = width
        self.screen_height = height
    
    def draw(self, song_title="", category="", category_color=None):
        """
        缁樺埗姝屾洸淇℃伅
        
        鍙傛暟:
            song_title: 姝屾洸鏍囬锛堝彲浠ヤ负绌猴級
            category: 鍒嗙被鍚嶇О锛堝彲浠ヤ负绌猴級
            category_color: 鍒嗙被鑳屾櫙棰滆壊 (R, G, B)锛屽鏋滀负None鍒欎娇鐢ㄩ粯璁ら鑹?        """
        if not song_title and not category:
            return  # 濡傛灉閮戒负绌哄垯涓嶇粯鍒?        
        # 鍙冲榻愬熀鍑嗙偣
        right_x = self.screen_width - self.right_margin
        # 璧峰Y鍧愭爣锛堢洿鎺ヤ娇鐢╰op_margin锛屼笉鍋氶澶栧亸绉伙級
        current_y = self.top_margin
        
        if song_title:
            if self.title_outline_width > 0:
                # 缁樺埗鎻忚竟
                title_outline = self._render_text_with_outline(
                    song_title, self.font_title, self.title_color, 
                    self.outline_color, self.title_outline_width
                )
                title_rect = title_outline.get_rect(topright=(right_x, current_y))
                self.screen.blit(title_outline, title_rect)
                current_y += title_outline.get_height() + (self.vertical_spacing if category else 0)
            else:
                title_surface = self.font_title.render(song_title, True, self.title_color)
                title_rect = title_surface.get_rect(topright=(right_x, current_y))
                self.screen.blit(title_surface, title_rect)
                current_y += title_surface.get_height() + (self.vertical_spacing if category else 0)
        
        # 缁樺埗鍒嗙被锛堝彸瀵归綈锛屽甫鑳屾櫙鍜屾弿杈癸級
        if category:
            bg_color = category_color if category_color else self.default_category_bg_color
            
            if self.category_outline_width > 0:
                category_surface = self._render_text_with_outline(
                    category, self.font_category, self.category_text_color,
                    self.outline_color, self.category_outline_width
                )
            else:
                category_surface = self.font_category.render(category, True, self.category_text_color)
            
            # 璁＄畻鑳屾櫙鐭╁舰锛堝彸瀵归綈锛?            text_width = category_surface.get_width()
            text_height = category_surface.get_height()
            bg_width = text_width + self.category_padding_x * 2
            bg_height = text_height + self.category_padding_y * 2
            # 鍙冲榻愶細浠庡彸杈圭晫鍚戝乏璁＄畻
            bg_x = right_x - bg_width
            bg_y = current_y
            bg_rect = pygame.Rect(bg_x, bg_y, bg_width, bg_height)
            
            # 缁樺埗鑳屾櫙锛堜紭鍏堜娇鐢ㄥ垎绫荤嫭绔嬪浘鐗囷級
            category_image = self._load_category_image(category)
            
            if category_image:
                # 浣跨敤鍒嗙被鐙珛鍥剧墖锛堜繚鎸佸師濮嬪楂樻瘮锛屼笉鍙樺舰锛?                # 鑾峰彇鍥剧墖鍘熷灏哄
                orig_width = category_image.get_width()
                orig_height = category_image.get_height()
                orig_ratio = orig_width / orig_height
                
                # 璁＄畻鐩爣楂樺害锛堜互鏂囧瓧楂樺害涓哄熀鍑嗭紝鏀惧ぇ1.7鍊嶏級
                target_height = int(text_height * 1.7)
                # 鏍规嵁鍘熷姣斾緥璁＄畻鐩爣瀹藉害
                target_width = int(target_height * orig_ratio)
                
                # 鎸夋瘮渚嬬缉鏀惧浘鐗囷紙淇濇寔瀹介珮姣旓級
                scaled_bg = pygame.transform.smoothscale(category_image, (target_width, target_height))
                
                # 鍙冲榻愬浘鐗囷細浠巖ight_x鍚戝乏缁樺埗
                image_x = right_x - target_width
                # 鍨傜洿灞呬腑瀵归綈锛氳€冭檻鏂囧瓧鐨勫疄闄呬綅缃?                image_y = bg_y + (bg_height - target_height) // 2
                self.screen.blit(scaled_bg, (image_x, image_y))
                
                # 缁樺埗鍒嗙被鏂囧瓧锛堝湪鍥剧墖涓婏紝姘村钩鍜屽瀭鐩撮兘灞呬腑锛?                # 浣跨敤鍥剧墖鐨勫疄闄呭尯鍩熶綔涓哄熀鍑?                image_rect = pygame.Rect(image_x, image_y, target_width, target_height)
                text_rect = category_surface.get_rect(center=image_rect.center)
                self.screen.blit(category_surface, text_rect)
            else:
                # 浣跨敤鍦嗚鐭╁舰鑳屾櫙
                border_radius = int(bg_height * self.category_border_radius_ratio)
                pygame.draw.rect(self.screen, bg_color, bg_rect, border_radius=border_radius)
                
                # 缁樺埗鍒嗙被鏂囧瓧锛堝湪鐭╁舰涓婂眳涓級
                text_rect = category_surface.get_rect(center=bg_rect.center)
                self.screen.blit(category_surface, text_rect)
    
    # ===== 閰嶇疆鏂规硶锛堟柟渚跨敤鎴疯皟鏁达級 =====
    
    def set_position(self, right_margin=None, top_margin=None, vertical_spacing=None):
        """
        璁剧疆鏄剧ず浣嶇疆
        
        鍙傛暟:
            right_margin: 鍙宠竟璺濓紙鍍忕礌锛?            top_margin: 涓婅竟璺濓紙鍍忕礌锛?            vertical_spacing: 姝屽悕鍜屽垎绫讳箣闂寸殑闂磋窛锛堝儚绱狅級
        """
        if right_margin is not None:
            self.right_margin = right_margin
        if top_margin is not None:
            self.top_margin = top_margin
        if vertical_spacing is not None:
            self.vertical_spacing = vertical_spacing
    
    def set_font_sizes(self, title_size=None, category_size=None):
        """
        璁剧疆瀛椾綋澶у皬锛堜細绔嬪嵆閲嶆柊鍔犺浇瀛椾綋锛?        
        鍙傛暟:
            title_size: 姝屽悕瀛椾綋澶у皬
            category_size: 鍒嗙被瀛椾綋澶у皬
        """
        reload_needed = False
        
        if title_size is not None and title_size != self.title_font_size:
            self.title_font_size = title_size
            reload_needed = True
            print(f"Set title font size to: {title_size}")
        
        if category_size is not None and category_size != self.category_font_size:
            self.category_font_size = category_size
            reload_needed = True
            print(f"Set category font size to: {category_size}")
        
        if reload_needed:
            print("Reloading fonts with new sizes...")
            self._load_fonts()
    
    def set_colors(self, title_color=None, category_text_color=None, default_category_bg=None):
        """
        璁剧疆棰滆壊
        
        鍙傛暟:
            title_color: 姝屽悕棰滆壊 (R, G, B)
            category_text_color: 鍒嗙被鏂囧瓧棰滆壊 (R, G, B)
            default_category_bg: 榛樿鍒嗙被鑳屾櫙棰滆壊 (R, G, B)
        """
        if title_color is not None:
            self.title_color = title_color
        if category_text_color is not None:
            self.category_text_color = category_text_color
        if default_category_bg is not None:
            self.default_category_bg_color = default_category_bg
    
    def set_outline(self, title_outline=None, category_outline=None, outline_color=None):
        """
        璁剧疆鏂囧瓧鎻忚竟
        
        鍙傛暟:
            title_outline: 姝屽悕鎻忚竟瀹藉害锛堝儚绱狅紝0=鏃犳弿杈癸級
            category_outline: 鍒嗙被鎻忚竟瀹藉害锛堝儚绱狅紝0=鏃犳弿杈癸級
            outline_color: 鎻忚竟棰滆壊 (R, G, B)锛岄粯璁ら粦鑹?        """
        if title_outline is not None:
            self.title_outline_width = title_outline
        if category_outline is not None:
            self.category_outline_width = category_outline
        if outline_color is not None:
            self.outline_color = outline_color
    
    def set_category_padding(self, padding_x=None, padding_y=None):
        """
        璁剧疆鍒嗙被鑳屾櫙鍐呰竟璺?        
        鍙傛暟:
            padding_x: 妯悜鍐呰竟璺濓紙鍍忕礌锛?            padding_y: 绾靛悜鍐呰竟璺濓紙鍍忕礌锛?        """
        if padding_x is not None:
            self.category_padding_x = padding_x
        if padding_y is not None:
            self.category_padding_y = padding_y
    
    def set_border_radius_ratio(self, ratio):
        """
        璁剧疆鍦嗚鍗婂緞姣斾緥
        
        鍙傛暟:
            ratio: 鍦嗚鍗婂緞鐩稿浜庤儗鏅珮搴︾殑姣斾緥锛?.0-1.0锛?                  0.5 = 瀹屽叏鍦嗚锛堟き鍦嗭級
                  0.0 = 鏃犲渾瑙掞紙鐭╁舰锛?        """
        self.category_border_radius_ratio = max(0.0, min(1.0, ratio))
    
    def set_category_background_image(self, image_path: str):
        """
        璁剧疆鍒嗙被鑳屾櫙鍥剧墖
        
        鍙傛暟:
            image_path: 鍥剧墖鏂囦欢璺緞
        """
        try:
            from pathlib import Path
            img_path = Path(image_path)
            if img_path.exists():
                self.category_bg_image = pygame.image.load(str(img_path)).convert_alpha()
                self.use_category_bg_image = True
                print(f"Loaded category background image: {image_path}")
            else:
                print(f"Category background image not found: {image_path}")
                self.use_category_bg_image = False
        except Exception as e:
            print(f"Error loading category background image: {e}")
            self.use_category_bg_image = False



