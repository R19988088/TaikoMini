"""
Most of this code was adapted from https://github.com/WHMHammer/tja-tools and converted to Python.
The original repository does not specify a license. Usage of said code
is intended to fall under fair use for educational or non-commercial purposes.
If there are any concerns or issues regarding the usage of this code, please
contact @keifunky on discord.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict
from math import ceil, floor
import math
import typing

from src.config import config

HEADER_GLOBAL = [
    'TITLE',
    'SUBTITLE',
    'BPM',
    'WAVE',
    'OFFSET',
    'DEMOSTART',
    'GENRE',
]

HEADER_COURSE = [
    'COURSE',
    'LEVEL',
    'BALLOON',
    'SCOREINIT',
    'SCOREDIFF',
    'TTROWBEAT',
]

COMMAND = [
    'START',
    'END',
    'GOGOSTART',
    'GOGOEND',
    'MEASURE',
    'SCROLL',
    'BPMCHANGE',
    'DELAY',
    'BRANCHSTART',
    'BRANCHEND',
    'SECTION',
    'N',
    'E',
    'M',
    'LEVELHOLD',
    'BMSCROLL',
    'HBSCROLL',
    'BARLINEOFF',
    'BARLINEON',
    'TTBREAK',
]

def parse_line(line):
    match = None
    
    # comment
    match = re.match(r'//.*', line)
    if match:
        line = line[:match.start()].strip()

    # header
    match = re.match(r'^([A-Z]+):(.+)', line, re.IGNORECASE)
    if match:
        name_upper = match.group(1).upper()
        value = match.group(2).strip()

        # 对于SCOREINIT和SCOREDIFF，只取逗号前的第一个值
        if name_upper in ['SCOREINIT', 'SCOREDIFF']:
            value = value.split(',')[0]

        if name_upper in HEADER_GLOBAL:
            return {
                'type': 'header',
                'scope': 'global',
                'name': name_upper,
                'value': value
            }
        elif name_upper in HEADER_COURSE:
            return {
                'type': 'header',
                'scope': 'course',
                'name': name_upper,
                'value': value
            }
    
    # command
    match = re.match(r'^#([A-Z]+)(?:\s+(.+))?', line, re.IGNORECASE)
    if match:
        name_upper = match.group(1).upper()
        value = match.group(2) or ''

        if name_upper in COMMAND:
            return {
                'type': 'command',
                'name': name_upper,
                'value': value.strip()
            }
    
    # data
    match = re.match(r'^(([0-9]|A|B|C|F|G|n|d|o|t|k)*,?)$', line)
    if match:
        data = match.group(1)
        return {
            'type': 'data',
            'data': data
        }
    
    return {
        'type': 'unknown',
        'value': line
    }

def get_course(tja_headers, lines):
    headers = {
        'course': 'Oni',
        'level': 0,
        'balloon': [],
        'scoreInit': 480,  # 使用固定值
        'scoreDiff': 120,  # 使用固定值
        'ttRowBeat': 16
    }

    # 添加一个标记来检查是否遇到 STYLE
    has_style = False

    measures = []

    measure_dividend = 4
    measure_divisor = 4
    measure_properties = {}
    measure_data = ''
    measure_events = []
    current_branch = 'N'
    target_branch = 'N'
    flag_levelhold = False

    for line in lines:
        if line['type'] == 'header':
            # 检查是否有 STYLE 标记
            if line['name'] == 'STYLE':
                return None  # 直接返回 None，不显示确认弹窗
            if line['name'] == 'COURSE':
                headers['course'] = line['value']
            elif line['name'] == 'LEVEL':
                headers['level'] = int(line['value'])
            elif line['name'] == 'BALLOON':
                try:
                    headers['balloon'] = [int(b) for b in re.split(r'[^0-9]', line['value']) if b] or [5]
                except:
                    headers['balloon'] = [5]
            elif line['name'] == 'TTROWBEAT':
                headers['ttRowBeat'] = int(line['value'])
        
        elif line['type'] == 'command':
            if line['name'] == 'BRANCHSTART':
                if not flag_levelhold:
                    values = line['value'].split(',')
                    if values[0] == 'r':
                        if len(values) >= 3:
                            target_branch = 'M'
                        elif len(values) == 2:
                            target_branch = 'E'
                        else:
                            target_branch = 'N'
                    elif values[0] == 'p':
                        if len(values) >= 3 and float(values[2]) <= 100:
                            target_branch = 'M'
                        elif len(values) >= 2 and float(values[1]) <= 100:
                            target_branch = 'E'
                        else:
                            target_branch = 'N'
            
            elif line['name'] == 'BRANCHEND':
                current_branch = target_branch
            
            elif line['name'] in ('N', 'E', 'M'):
                current_branch = line['name']
            
            elif line['name'] in ('START', 'END'):
                current_branch = 'N'
                target_branch = 'N'
                flag_levelhold = False
            
            else:
                if current_branch != target_branch:
                    continue
                if line['name'] == 'MEASURE':
                    match_measure = re.match(r'(\d+)/(\d+)', line['value'])
                    if match_measure:
                        measure_dividend = int(match_measure.group(1))
                        measure_divisor = int(match_measure.group(2))
                
                elif line['name'] == 'GOGOSTART':
                    measure_events.append({
                        'name': 'gogoStart',
                        'position': len(measure_data)
                    })
                
                elif line['name'] == 'GOGOEND':
                    measure_events.append({
                        'name': 'gogoEnd',
                        'position': len(measure_data)
                    })
                
                elif line['name'] == 'SCROLL':
                    measure_events.append({
                        'name': 'scroll',
                        'position': len(measure_data),
                        'value': float(line['value'])
                    })
                
                elif line['name'] == 'BPMCHANGE':
                    measure_events.append({
                        'name': 'bpm',
                        'position': len(measure_data),
                        'value': float(line['value'])
                    })
                
                elif line['name'] == 'TTBREAK':
                    measure_properties['ttBreak'] = True
                
                elif line['name'] == 'LEVELHOLD':
                    flag_levelhold = True
        
        elif line['type'] == 'data' and current_branch == target_branch:
            data = line['data']
            if data.endswith(','):
                measure_data += data[:-1]
                measures.append({
                    'length': [measure_dividend, measure_divisor],
                    'properties': measure_properties,
                    'data': measure_data,
                    'events': measure_events
                })
                measure_data = ''
                measure_events = []
                measure_properties = {}
            else:
                measure_data += data

    # 如果遇到 STYLE，返回 None 表示忽略这个难度组
    if has_style:
        return None

    if measures:
        first_bpm_event_found = any(evt['name'] == 'bpm' and evt['position'] == 0 for evt in measures[0]['events'])
        if not first_bpm_event_found:
            measures[0]['events'].insert(0, {
                'name': 'bpm',
                'position': 0,
                'value': tja_headers['bpm']
            })

    course = {
        'easy': 0,
        'normal': 1,
        'hard': 2,
        'oni': 3,
        'edit': 4,
        'ura': 4,
        '0': 0,
        '1': 1,
        '2': 2,
        '3': 3,
        '4': 4
    }.get(headers['course'].lower(), 0)

    if measure_data:
        measures.append({
            'length': [measure_dividend, measure_divisor],
            'properties': measure_properties,
            'data': measure_data,
            'events': measure_events
        })
    else:
        for event in measure_events:
            event['position'] = len(measures[-1]['data'])
            measures[-1]['events'].append(event)

    return {'course': course, 'headers': headers, 'measures': measures}

def parse_tja(tja):
    lines = [line.strip() for line in re.split(r'(\r\n|\r|\n)', tja) if line.strip()]

    headers = {
        'title': '',
        'subtitle': '',
        'bpm': 120,
        'wave': '',
        'offset': 0,
        'demoStart': 0,
        'genre': ''
    }

    courses = {}
    course_lines = []

    for line in lines:
        parsed = parse_line(line)

        if parsed['type'] == 'header' and parsed['scope'] == 'global':
            headers[parsed['name'].lower()] = parsed['value']

        elif parsed['type'] == 'header' and parsed['scope'] == 'course':
            if parsed['name'] == 'COURSE' and course_lines:
                course = get_course(headers, course_lines)
                if course:  # 只添加没有 STYLE 标记的难度组
                    courses[course['course']] = course
                course_lines = []

            course_lines.append(parsed)

        elif parsed['type'] in ('command', 'data'):
            course_lines.append(parsed)

    if course_lines:
        course = get_course(headers, course_lines)
        if course:  # 只添加没有 STYLE 标记的难度组
            courses[course['course']] = course

    return {'headers': headers, 'courses': courses}

def pulse_to_time(events, objects):
    bpm = 120
    passed_beat = 0
    passed_time = 0
    eidx = 0
    oidx = 0

    times = []

    while oidx < len(objects):
        event = events[eidx] if eidx < len(events) else None
        obj_beat = objects[oidx]

        while event and event['beat'] <= obj_beat:
            if event['type'] == 'bpm':
                beat = event['beat'] - passed_beat
                time = 60 / bpm * beat

                passed_beat += beat
                passed_time += time
                bpm = float(event['value'])

            eidx += 1
            event = events[eidx] if eidx < len(events) else None

        beat = obj_beat - passed_beat
        time = 60 / bpm * beat
        times.append(passed_time + time)

        passed_beat += beat
        passed_time += time
        oidx += 1

    return times

def convert_to_timed(course):
    events = []
    notes = []
    beat = 0
    balloon = 0
    imo = False

    for measure in course['measures']:
        length = measure['length'][0] / measure['length'][1] * 4

        for event in measure['events']:
            e_beat = length / (len(measure['data']) or 1) * event['position']

            if event['name'] == 'bpm':
                events.append({
                    'type': 'bpm',
                    'value': event['value'],
                    'beat': beat + e_beat,
                })
            elif event['name'] == 'gogoStart':
                events.append({
                    'type': 'gogoStart',
                    'beat': beat + e_beat,
                })
            elif event['name'] == 'gogoEnd':
                events.append({
                    'type': 'gogoEnd',
                    'beat': beat + e_beat,
                })

        for d, ch in enumerate(measure['data']):
            n_beat = length / len(measure['data']) * d

            note = {'type': '', 'beat': beat + n_beat}

            if ch in ['1', 'n', 'd', 'o']:
                note['type'] = 'don'
            elif ch in ['2', 't', 'k']:
                note['type'] = 'kat'
            elif ch == '3' or ch == 'A':
                note['type'] = 'donBig'
            elif ch == '4' or ch == 'B':
                note['type'] = 'katBig'
            elif ch == '5':
                note['type'] = 'renda'
            elif ch == '6':
                note['type'] = 'rendaBig'
            elif ch == '7':
                note['type'] = 'balloon'
                if balloon < len(course['headers']['balloon']):
                    note['count'] = course['headers']['balloon'][balloon]
                else:
                    note['count'] = 5  # 默认值
                balloon += 1
            elif ch == '8':
                note['type'] = 'end'
                if imo:
                    imo = False
            elif ch == '9':
                if not imo:
                    note['type'] = 'balloon'
                    if balloon < len(course['headers']['balloon']):
                        note['count'] = course['headers']['balloon'][balloon]
                    else:
                        note['count'] = 5  # 默认值
                    balloon += 1
                    imo = True

            if note['type']:
                notes.append(note)

        beat += length

    # Assuming pulse_to_time is a pre-defined function
    times = pulse_to_time(events, [n['beat'] for n in notes])
    for idx, t in enumerate(times):
        notes[idx]['time'] = t

    return {'headers': course['headers'], 'events': events, 'notes': notes}

def get_statistics(course):
    # Initialize variables
    notes = [0, 0, 0, 0]
    rendas, balloons = [], []
    start, end, combo = 0, 0, 0
    renda_start = -1
    balloon_start, balloon_count, balloon_gogo = False, 0, 0
    sc_cur_event_idx = 0
    sc_cur_event = course['events'][sc_cur_event_idx]
    sc_gogo = 0
    sc_notes = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    sc_balloon = [0, 0]
    sc_balloon_pop = [0, 0]
    sc_potential = 0
    current_bpm = 0
    bpm_at_renda_start = 0
    type_note = ['don', 'kat', 'donBig', 'katBig']
    for i, note in enumerate(course['notes']):
        # Check and handle events
        if sc_cur_event and sc_cur_event['beat'] <= note['beat']:
            while sc_cur_event and sc_cur_event['beat'] <= note['beat']:
                if sc_cur_event['type'] == 'gogoStart':
                    sc_gogo = 1
                elif sc_cur_event['type'] == 'gogoEnd':
                    sc_gogo = 0
                elif sc_cur_event['type'] == 'bpm':
                    current_bpm = float(sc_cur_event['value'])
                sc_cur_event_idx += 1
                if sc_cur_event_idx < len(course['events']):
                    sc_cur_event = course['events'][sc_cur_event_idx]
                else:
                    sc_cur_event = None

        v1 = type_note.index(note['type']) if note['type'] in type_note else -1
        if v1 != -1:
            if i == 0:
                start = note['time']
            end = note['time']

            notes[v1] += 1
            combo += 1

            big = v1 in (2, 3)
            sc_range = (0 if combo < 10 else 1 if combo < 30 else 2 if combo < 50 else 3 if combo < 100 else 4)
            sc_notes[sc_gogo][sc_range] += 2 if big else 1

            note_score_base = (
                course['headers']['scoreInit'] +
                course['headers']['scoreDiff'] * (0 if combo < 10 else 1 if combo < 30 else 2 if combo < 50 else 4 if combo < 100 else 8)
            )

            note_score = (note_score_base // 10) * 10
            if sc_gogo:
                note_score = (note_score * 1.2 // 10) * 10
            if big:
                note_score *= 2

            sc_potential += note_score

            continue

        if note['type'] in ('renda', 'rendaBig'):
            renda_start = note['time']
            bpm_at_renda_start = current_bpm
            continue

        elif note['type'] == 'balloon':
            balloon_start = note['time']
            balloon_count = note['count']
            bpm_at_renda_start = current_bpm
            balloon_gogo = sc_gogo
            continue

        elif note['type'] == 'end':
            if renda_start != -1:
                rendas.append([note['time'] - renda_start, bpm_at_renda_start])
                renda_start = -1
            elif balloon_start:
                balloon_length = note['time'] - balloon_start
                balloon_speed = balloon_count / balloon_length
                balloons.append([balloon_length, balloon_count, balloon_speed > 40, bpm_at_renda_start])
                balloon_start = False

                if balloon_speed <= 60:
                    sc_balloon[balloon_gogo] += balloon_count - 1
                    sc_balloon_pop[balloon_gogo] += 1

    return {
        'totalCombo': combo,
        'notes': notes,
        'length': end - start,
        'rendas': rendas,
        'balloons': balloons,
        'score': {
            'score': sc_potential,
            'notes': sc_notes,
            'balloon': sc_balloon,
            'balloonPop': sc_balloon_pop,
        }
    }

@dataclass
class SongData:
    """歌曲数据类"""
    demo_start: float = 0.0
    title: str = ""
    sub: str = ""
    star: List[int] = field(default_factory=lambda: [0, 0, 0, 0, 0])
    length: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0, 0.0])
    shinuti: List[int] = field(default_factory=lambda: [0, 0, 0, 0, 0])
    shinuti_score: List[int] = field(default_factory=lambda: [0, 0, 0, 0, 0])
    onpu_num: List[int] = field(default_factory=lambda: [0, 0, 0, 0, 0])
    renda_time: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0, 0.0])
    fuusen_total: List[int] = field(default_factory=lambda: [0, 0, 0, 0, 0])

    # 添加中文属性名
    @property
    def 标题(self) -> str:
        return self.title

    @property
    def 副标题(self) -> str:
        return self.sub

    @property
    def 星级(self) -> List[int]:
        return self.star

    @property
    def 真打(self) -> List[int]:
        return self.shinuti

    @property
    def 真打分数(self) -> List[int]:
        return self.shinuti_score

def parse_and_get_data(tja_file: str, shinuti_override: List[int] = None, required_renda_speed_override: List[float] = None) -> SongData:
    """读取tja文件并返回SongData对象"""
    ret = SongData()
    file_str = None  # Initialize file_str to avoid the UnboundLocalError

    # Try opening the file with different encodings
    encodings = ['utf-8-sig', 'shiftjis', 'shift_jisx0213', 'utf-8', 'shift_jis_2004', 'latin-1']
    for encoding in encodings:
        try:
            with open(tja_file, encoding=encoding) as file:
                file_str = file.read()
            print(f'Successfully read file with {encoding} encoding')
            break  # If successful, break out of the loop
        except Exception as e:
            print(f'Error reading file with {encoding} encoding: {e}')
            continue

    if file_str:
        # Proceed with the parsing if file_str has been assigned
        parsed = parse_tja(file_str)
    else:
        raise Exception("Failed to parse TJA File")

    ret.demo_start = float(parsed['headers']['demostart'])
    ret.title = parsed['headers']['title']
    sub = parsed['headers']['subtitle']
    ret.sub = sub[2::] if sub.startswith('--') else sub

    # 修改难度名称映射
    difficulty_names = {
        'easy': '简单',
        'normal': '普通',
        'hard': '困难',
        'oni': '魔王',
        'edit': '里',
        'ura': '里',
        '0': '简单',
        '1': '普通',
        '2': '困难',
        '3': '魔王',
        '4': '里'
    }

    for i in parsed['courses'].keys():
        ret.star[i] = parsed['courses'][i]['headers']['level']
        stats = get_statistics(convert_to_timed(parsed['courses'][i]))
        ret.length[i] = stats['length']
        ret.onpu_num[i] = stats['totalCombo']

        impoppable_balloon_s = 0.0 #BTD reference???
        impoppable_balloon_count = 0
        poppable_balloon_count = 0
        for time, count, impoppable, bpm_start in stats['balloons']:
            if impoppable:
                impoppable_balloon_s += time
                impoppable_balloon_count += count
            else:
                poppable_balloon_count += count

        # 收集连打时间，并减少一点
        for time, bpm_start in stats['rendas']:
            # 根据不同难度使用不同的系数
            if i <= 0:  # Easy
                ret.renda_time[i] += time * 0.96296546  # 简单难度减少5%
            elif i == 1:  # Normal
                ret.renda_time[i] += time * 0.9536449  # 普通难度减少6%
            else:  # Hard, Oni, Ura
                ret.renda_time[i] += time * 0.94737088  # 困难及以上减少7%

        ret.fuusen_total[i] = poppable_balloon_count

        # 使用传入的连打速度覆盖默认值
        if required_renda_speed_override is not None and required_renda_speed_override[i] != 0:
            连打速度 = required_renda_speed_override[i]
        else:
            连打速度 = 获取默认连打速度(i)

        if shinuti_override is not None and shinuti_override[i] != 0:
            真打值 = shinuti_override[i]
        else:
            真打值 = 0

        ret.shinuti[i], ret.shinuti_score[i], _ = 计算真打和真打分数(
            ret.renda_time[i], 
            impoppable_balloon_s, 
            poppable_balloon_count, 
            ret.onpu_num[i], 
            连打速度,
            真打值,
            i
        )

    return ret

def 获取默认连打速度(难度: int) -> float:
    """
    根据难度返回默认连打速度（每秒点击次数）
    难度: 0=简单, 1=普通, 2=困难, 3=魔王, 4=里
    基于60帧的游戏速度计算
    """
    from src.config import config
    return config.default_required_renda_speeds[难度]

def 计算真打和真打分数(连打时长, 不可能气球时长, 气球数量, 音符数量, 要求连打速度, 真打值, 难度):
    """计算真打值和真打分数"""
    连打速度 = round(要求连打速度, 2)
    
    # 气球分数 - 每个气球100分
    气球分数 = 气球数量 * 100
    
    # 连打分数计算 - 每10次1000分
    连打次数 = math.ceil(连打速度 * 连打时长)
    连打分数 = math.ceil(连打次数 / 10) * 1000  # 使用 math.ceil 向上取整
    
    # 如果没有提供真打值，根据目标分数计算
    if 真打值 == 0:
        # 计算每个音符的分数
        剩余分数 = float(1000000 - 气球分数 - 连打分数)  # 转为float以保持精度
        每音符基础分数 = 剩余分数 / 音符数量
        每音符基础分数 /= 10  # 除以10
        每音符分数 = math.ceil(每音符基础分数) * 10  # 向上取整后乘以10
        真打值 = 每音符分数
    
    # 使用真打值计算总分
    每音符真打分数 = 真打值  # 已经是10的倍数了
    基础分数 = 每音符真打分数 * 音符数量
    真打总分 = 基础分数 + 气球分数 + 连打分数  # 直接相加，已经都是10的倍数了

    return 真打值, 真打总分, 每音符真打分数

def calculate_tenjyou_and_shinuti_score_from_renda_count(shinuti: int, poppable_balloon_count: int, onpu_num: int, required_renda_count: int) -> tuple[int, int]:
    """使用连打次数计算分数"""
    # 确保真打值是10的倍数，向上取整
    真打值 = ((shinuti + 9) // 10) * 10
    
    # 气球分数
    气球分数 = poppable_balloon_count * 100
    
    # 连打分数 - 每10次1000分，有余数就给一个完整的1000分
    基础连打分数 = (required_renda_count // 10) * 1000
    if required_renda_count % 10 > 0:
        基础连打分数 += 1000
    连打分数 = 基础连打分数
    
    # 总分 - 确保分数是10的倍数，向上取整
    天井分数 = ((真打值 * 10 * onpu_num + 气球分数 + 9) // 10) * 10
    真打总分 = ((天井分数 + 连打分数 + 9) // 10) * 10
    
    return 天井分数, 真打总分

