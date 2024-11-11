import json
import re
from typing import List
from pathlib import Path

class ASRDataSeg:
    def __init__(self, text, start_time, end_time):
        self.text = text
        self.start_time = start_time
        self.end_time = end_time

    def to_srt_ts(self) -> str:
        """Convert to SRT timestamp format"""
        return f"{self._ms_to_srt_time(self.start_time)} --> {self._ms_to_srt_time(self.end_time)}"


    def to_lrc_ts(self) -> str:
        """Convert to LRC timestamp format"""
        return f"[{self._ms_to_lrc_time(self.start_time)}]"
    
    def to_ass_ts(self) -> tuple[str, str]:
        """Convert to ASS timestamp format"""
        return self._ms_to_ass_ts(self.start_time), self._ms_to_ass_ts(self.end_time)

    def _ms_to_lrc_time(self, ms) -> str:
        seconds = ms / 1000
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes):02}:{seconds:.2f}"
    
    @staticmethod
    def _ms_to_srt_time(ms) -> str:
        """Convert milliseconds to SRT time format (HH:MM:SS,mmm)"""
        total_seconds, milliseconds = divmod(ms, 1000)
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{int(milliseconds):03}"

    @staticmethod
    def _ms_to_ass_ts(ms) -> str:
        """Convert milliseconds to ASS timestamp format (H:MM:SS.cc)"""
        total_seconds, milliseconds = divmod(ms, 1000)
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        # ASS格式使用厘秒(1/100秒)而不是毫秒
        centiseconds = int(milliseconds / 10)
        return f"{int(hours):01}:{int(minutes):02}:{int(seconds):02}.{centiseconds:02}"

    @property
    def transcript(self) -> str:
        """Return segment text"""
        return self.text

    def __str__(self) -> str:
        return f"ASRDataSeg({self.text}, {self.start_time}, {self.end_time})"


class ASRData:
    def __init__(self, segments: List[ASRDataSeg]):
        self.segments = segments

    def __iter__(self):
        return iter(self.segments)
    
    def __len__(self) -> int:
        return len(self.segments)
    
    def has_data(self) -> bool:
        """Check if there are any utterances"""
        return len(self.segments) > 0
    
    def is_word_timestamp(self) -> bool:
        """
        判断是否是字级时间戳
        规则：
        1. 对于英文，每个segment应该只包含一个单词
        2. 对于中文，每个segment应该只包含一个汉字
        3. 允许20%的误差率
        """
        if not self.segments:
            return False
            
        valid_segments = 0
        total_segments = len(self.segments)
        
        for seg in self.segments:
            text = seg.text.strip()
            # 检查是否只包含一个英文单词或一个汉字
            if (len(text.split()) == 1 and text.isascii()) or len(text.strip()) <= 2:
                valid_segments += 1
        print(f"valid_segments: {valid_segments}, total_segments: {total_segments}")
        return (valid_segments / total_segments) >= 0.8


    def save(self, save_path: str, ass_style: str = None, layout: str = "原文在上") -> None:
        """Save the ASRData to a file"""
        # 根据文件后缀名选择保存格式
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        if save_path.endswith('.srt'):
            self.to_srt(save_path=save_path)
        elif save_path.endswith('.txt'):
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(self.to_txt())
        elif save_path.endswith('.json'):
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_json(), f, ensure_ascii=False)
        elif save_path.endswith('.ass'):
            self.to_ass(save_path=save_path, style_str=ass_style, layout=layout)
        else:
            raise ValueError(f"Unsupported file extension: {save_path}")

    def to_txt(self) -> str:
        """Convert to plain text subtitle format (without timestamps)"""
        return "\n".join(seg.transcript for seg in self.segments)

    def to_srt(self, save_path=None) -> str:
        """Convert to SRT subtitle format"""
        srt_text = "\n".join(
            f"{n}\n{seg.to_srt_ts()}\n{seg.transcript}\n"
            for n, seg in enumerate(self.segments, 1))
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(srt_text)
        return srt_text

    def to_lrc(self, save_path=None) -> str:
        """Convert to LRC subtitle format"""
        lrc_text = "\n".join(
            f"{seg.to_lrc_ts()}{seg.transcript}" for seg in self.segments
        )
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(lrc_text)
        return lrc_text

    def to_json(self) -> dict:
        result_json = {}
        for i, segment in enumerate(self.segments, 1):
            # 检查是否有换行符
            if "\n" in segment.text:
                original_subtitle, translated_subtitle = segment.text.split("\n")
            else:
                original_subtitle, translated_subtitle = segment.text, ""

            result_json[str(i)] = {
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "original_subtitle": original_subtitle,
                "translated_subtitle": translated_subtitle
            }
        return result_json

    def to_ass(self, style_str: str = None, layout: str = "原文在上", save_path: str = None) -> str:
        """转换为ASS字幕格式
        
        Args:
            style_str: ASS样式字符串,为空则使用默认样式
            layout: 字幕布局,可选值["译文在上", "原文在上", "仅原文", "仅译文"]
            
        Returns:
            ASS格式字幕内容
        """
        # 默认样式
        if not style_str:
            style_str = (
                "[V4+ Styles]\n"
                "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
                "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
                "Alignment,MarginL,MarginR,MarginV,Encoding\n"
                "Style: Default,微软雅黑,66,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,"
                "0,0,1,2,0,2,10,10,10,1\n"
                "Style: Translate,微软雅黑,40,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,"
                "0,0,1,2,0,2,10,10,10,1"
            )

        # 构建ASS文件头
        ass_content = (
            "[Script Info]\n"
            "; Script generated by VideoCaptioner\n"
            "; https://github.com/weifeng2333\n"
            "ScriptType: v4.00+\n"
            "PlayResX: 1280\n"
            "PlayResY: 720\n\n"
            f"{style_str}\n\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )

        # 根据布局生成对话内容
        for seg in self.segments:
            start_time = seg.to_ass_ts()[0]
            end_time = seg.to_ass_ts()[1]
            dialogue_template = 'Dialogue: 0,{},{},{},,0,0,0,,{}\n'

            # 检查是否有换行符分隔的原文和译文
            if "\n" in seg.text:
                original, translate = seg.text.split("\n")
                if layout == "译文在上" and translate:
                    ass_content += dialogue_template.format(start_time, end_time, "Secondary", original)
                    ass_content += dialogue_template.format(start_time, end_time, "Default", translate)
                elif layout == "原文在上" and translate:
                    ass_content += dialogue_template.format(start_time, end_time, "Secondary", translate)
                    ass_content += dialogue_template.format(start_time, end_time, "Default", original)
                elif layout == "仅原文":
                    ass_content += dialogue_template.format(start_time, end_time, "Default", original)
                elif layout == "仅译文" and translate:
                    ass_content += dialogue_template.format(start_time, end_time, "Default", translate)
            else:
                original = seg.text
                ass_content += dialogue_template.format(start_time, end_time, "Default", original)
            # 根据布局生成对话行
            
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)
        return ass_content

    def merge_segments(self, start_index: int, end_index: int, merged_text: str = None):
            """合并从 start_index 到 end_index 的段（包含）。"""
            if start_index < 0 or end_index >= len(self.segments) or start_index > end_index:
                raise IndexError("无效的段索引。")
            merged_start_time = self.segments[start_index].start_time
            merged_end_time = self.segments[end_index].end_time
            if merged_text is None:
                merged_text = ''.join(seg.text for seg in self.segments[start_index:end_index+1])
            merged_seg = ASRDataSeg(merged_text, merged_start_time, merged_end_time)
            # 替换 segments[start_index:end_index+1] 为 merged_seg
            self.segments[start_index:end_index+1] = [merged_seg]

    def merge_with_next_segment(self, index: int) -> None:
        """合并指定索引的段与下一个段。"""
        if index < 0 or index >= len(self.segments) - 1:
            raise IndexError("索引超出范围或没有下一个段可合并。")
        current_seg = self.segments[index]
        next_seg = self.segments[index + 1]

        # 合并文本
        merged_text = f"{current_seg.text} {next_seg.text}"
        merged_start_time = current_seg.start_time
        merged_end_time = next_seg.end_time
        merged_seg = ASRDataSeg(merged_text, merged_start_time, merged_end_time)

        # 替换当前段为合并后的段
        self.segments[index] = merged_seg
        # 删除下一个段
        del self.segments[index + 1]

    def __str__(self):
        return self.to_txt()

def from_subtitle_file(file_path: str) -> 'ASRData':
    """从文件路径加载ASRData实例
    
    Args:
        file_path: 字幕文件路径，支持.srt、.vtt、.ass、.json格式
        
    Returns:
        ASRData: 解析后的ASRData实例
        
    Raises:
        ValueError: 不支持的文件格式或文件读取错误
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
        
    try:
        content = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        content = file_path.read_text(encoding='gbk')
        
    suffix = file_path.suffix.lower()
    
    if suffix == '.srt':
        return from_srt(content)
    elif suffix == '.vtt':
        if '<c>' in content:  # YouTube VTT格式包含字级时间戳
            return from_youtube_vtt(content)
        return from_vtt(content)
    elif suffix == '.ass':
        return from_ass(content)
    elif suffix == '.json':
        return from_json(json.loads(content))
    else:
        raise ValueError(f"不支持的文件格式: {suffix}")

def from_json(json_data: dict) -> 'ASRData':
    """从JSON数据创建ASRData实例"""
    segments = []
    for i in sorted(json_data.keys(), key=int):
        segment_data = json_data[i]
        text = segment_data['original_subtitle']
        if segment_data['translated_subtitle']:
            text += '\n' + segment_data['translated_subtitle']
        segment = ASRDataSeg(
            text=text,
            start_time=segment_data['start_time'],
            end_time=segment_data['end_time']
        )
        segments.append(segment)
    return ASRData(segments)

def from_srt(srt_str: str) -> 'ASRData':
    """
    从SRT格式的字符串创建ASRData实例。

    :param srt_str: 包含SRT格式字幕的字符串。
    :return: 解析后的ASRData实例。
    """
    segments = []
    srt_time_pattern = re.compile(
        r'(\d{2}):(\d{2}):(\d{1,2})[.,](\d{3})\s-->\s(\d{2}):(\d{2}):(\d{1,2})[.,](\d{3})'
    )

    for block in re.split(r'\n\s*\n', srt_str.strip()):
        lines = block.splitlines()
        if len(lines) < 3:
            continue

        match = srt_time_pattern.match(lines[1])
        if not match:
            continue

        time_parts = list(map(int, match.groups()))
        start_time = sum([
            time_parts[0] * 3600000,
            time_parts[1] * 60000,
            time_parts[2] * 1000,
            time_parts[3]
        ])
        end_time = sum([
            time_parts[4] * 3600000,
            time_parts[5] * 60000,
            time_parts[6] * 1000,
            time_parts[7]
        ])

        text = '\n'.join(lines[2:]).strip()
        segments.append(ASRDataSeg(text, start_time, end_time))

    return ASRData(segments)

def from_vtt(vtt_str: str) -> 'ASRData':
    """
    从YouTube VTT格式的字符串创建ASRData实例。
    
    :param vtt_str: YouTube VTT格式的字幕字符串
    :return: ASRData实例
    """
    segments = []
    # 跳过头部元数据
    content = vtt_str.split('\n\n')[2:]
    
    current_text = ""
    current_start = 0
    current_end = 0
    
    for block in content:
        lines = block.strip().split('\n')
        if not lines:
            continue
            
        # 解析时间戳行
        timestamp_line = lines[0]
        if '-->' not in timestamp_line:
            continue
            
        # 提取开始和结束时间
        times = timestamp_line.split(' --> ')[0]
        hours, minutes, seconds = times.split(':')
        seconds, milliseconds = seconds.split('.')
        start_time = (int(hours) * 3600 + int(minutes) * 60 + int(seconds)) * 1000 + int(milliseconds)
        
        times = timestamp_line.split(' --> ')[1].split()[0]
        hours, minutes, seconds = times.split(':')
        seconds, milliseconds = seconds.split('.')
        end_time = (int(hours) * 3600 + int(minutes) * 60 + int(seconds)) * 1000 + int(milliseconds)
        
        # 提取并清文本内容
        if len(lines) > 1:
            text_line = lines[1]
            # 移除时间戳和样式标记
            cleaned_text = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', text_line)
            cleaned_text = re.sub(r'</?c>', '', cleaned_text)
            cleaned_text = cleaned_text.strip()
            
            if cleaned_text and cleaned_text != " ":
                segments.append(ASRDataSeg(cleaned_text, start_time, end_time))
    
    return ASRData(segments)

def from_youtube_vtt(vtt_str: str) -> 'ASRData':
    """
    从YouTube VTT格式的字符串创建ASRData实例，提取字级时间戳。
    
    :param vtt_str: 包含VTT格式字幕的字符串
    :return: 解析后的ASRData实例
    """
    def parse_timestamp(ts: str) -> int:
        """将时间戳字符串转换为毫秒"""
        h, m, s = ts.split(':')
        return int(float(h) * 3600000 + float(m) * 60000 + float(s) * 1000)
    
    def split_timestamped_text(text: str) -> List[ASRDataSeg]:
        """分离带时间戳的文本为单词段"""
        # 匹配 <时间戳>文本 的模式
        pattern = re.compile(r'<(\d{2}:\d{2}:\d{2}\.\d{3})>([^<]*)')
        matches = list(pattern.finditer(text))
        word_segments = []
        
        for i in range(len(matches) - 1):
            current_match = matches[i]
            next_match = matches[i + 1]
            
            start_time = parse_timestamp(current_match.group(1))
            end_time = parse_timestamp(next_match.group(1))
            word = current_match.group(2).strip()
            
            if word:  # 只有当文本不为空时才创建segment
                word_segments.append(ASRDataSeg(word, start_time, end_time))
        
        return word_segments
    
    segments = []
    # 跳过WEBVTT头部
    blocks = re.split(r'\n\n+', vtt_str.strip())
    
    # 时间戳匹配模式
    timestamp_pattern = re.compile(
        r'(\d{2}):(\d{2}):(\d{2}\.\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}\.\d{3})'
    )    
    for block in blocks:
        lines = block.strip().split('\n')
        if not lines:
            continue
            
        # 匹配时间戳行
        match = timestamp_pattern.match(lines[0])
        if not match:
            continue
            
        # 计算块的开始和结束时间
        block_start_time = (
            int(match.group(1)) * 3600000 +
            int(match.group(2)) * 60000 +
            float(match.group(3)) * 1000
        )
        block_end_time = (
            int(match.group(4)) * 3600000 +
            int(match.group(5)) * 60000 +
            float(match.group(6)) * 1000
        )
        
        # 获取文本内容
        text = '\n'.join(lines)
        
        timestamp_row = re.search(r'\n(.*?<c>.*?</c>.*)', block)
        if timestamp_row:
            text = re.sub(r'<c>|</c>', '', timestamp_row.group(1))
            block_start_time_string = f"{match.group(1)}:{match.group(2)}:{match.group(3)}"
            block_end_time_string = f"{match.group(4)}:{match.group(5)}:{match.group(6)}"
            text = f"<{block_start_time_string}>{text}<{block_end_time_string}>"
            
            # 分离每个带时间戳的单词
            word_segments = split_timestamped_text(text)
            segments.extend(word_segments)
    
    return ASRData(segments)

def from_ass(ass_str: str) -> 'ASRData':
    """
    从ASS格式的字符串创建ASRData实例。
    
    :param ass_str: 包含ASS格式字幕的字符串
    :return: ASRData实例
    """
    segments = []
    # ASS时间戳格式: H:MM:SS.cc
    ass_time_pattern = re.compile(r'Dialogue: \d+,(\d+:\d{2}:\d{2}\.\d{2}),(\d+:\d{2}:\d{2}\.\d{2}),(.*?),.*?,\d+,\d+,\d+,.*?,(.*?)$')
    
    def parse_ass_time(time_str: str) -> int:
        """将ASS时间戳转换为毫秒"""
        hours, minutes, seconds = time_str.split(':')
        seconds, centiseconds = seconds.split('.')
        return (int(hours) * 3600000 + 
                int(minutes) * 60000 + 
                int(seconds) * 1000 + 
                int(centiseconds) * 10)  # 厘秒转毫秒
    
    # 按行处理ASS文件
    for line in ass_str.splitlines():
        if line.startswith('Dialogue:'):
            match = ass_time_pattern.match(line)
            if match:
                start_time = parse_ass_time(match.group(1))
                end_time = parse_ass_time(match.group(2))
                text = match.group(4)
                
                # 清理ASS格式标记
                text = re.sub(r'\{[^}]*\}', '', text)  # 移除样式标记 {xxx}
                text = text.replace('\\N', '\n')  # 处理换行符
                text = text.strip()
                
                if text:  # 只有当文本不为空时才创建segment
                    segments.append(ASRDataSeg(text, start_time, end_time))
    
    return ASRData(segments)

if __name__ == '__main__':
    ass_style_str = """[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,微软雅黑,62,&H0017f1be,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,1.0,0,1,0.8,0,2,10,10,10,1
Style: Secondary,微软雅黑,40,&H00ffffff,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0.0,0,1,0.0,0,2,10,10,10,1"""
    # 测试
    from pathlib import Path
    # vtt_file_path = r"E:\GithubProject\VideoCaptioner\app\work_dir\Setting the record straight\subtitle\original_subtitle.en.vtt"
    # vtt_file_path = r"E:\GithubProject\VideoCaptioner\work_dir\Wake up babe a dangerous new open-source AI model is here\subtitle\original.en.vtt"
    # asr_data = from_youtube_vtt(Path(vtt_file_path).read_text(encoding="utf-8"))
    srt_file_path = r"E:\GithubProject\VideoCaptioner\app\work_dir\低视力音乐助人者_mp4\result_subtitle.srt"
    asr_data = from_srt(Path(srt_file_path).read_text(encoding="utf-8"))

    print(asr_data.to_ass(style_str=ass_style_str, save_path=srt_file_path.replace(".srt", ".ass")))
    # pass
    # asr_data = ASRData(seg)
    # Uncomment to test different formats:
    # print(asr_data.to_srt(save_path=vtt_file_path.replace(".vtt", ".srt")))
    # print(asr_data.to_lrc())
    # print(asr_data.to_txt())
    # print(asr_data.to_json())
    # print(asr_data.to_json())




