from typing import List


class ASRDataSeg:
    def __init__(self, text, start_time, end_time):
        self.text = text
        self.start_time = start_time
        self.end_time = end_time

    def to_srt_ts(self) -> str:
        """Convert to SRT timestamp format"""
        return f"{self._ms_to_srt_time(self.start_time)} --> {self._ms_to_srt_time(self.end_time)}"

    @staticmethod
    def _ms_to_srt_time(ms) -> str:
        """Convert milliseconds to SRT time format (HH:MM:SS,mmm)"""
        total_seconds, milliseconds = divmod(ms, 1000)
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{int(milliseconds):03}"

    def to_lrc_ts(self) -> str:
        """Convert to LRC timestamp format"""
        return f"[{self._ms_to_lrc_time(self.start_time)}]"

    def _ms_to_lrc_time(self, ms) -> str:
        seconds = ms / 1000
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes):02}:{seconds:.2f}"

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

    def has_data(self) -> bool:
        """Check if there are any utterances"""
        return len(self.segments) > 0

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

    def to_lrc(self) -> str:
        """Convert to LRC subtitle format"""
        return "\n".join(
            f"{seg.to_lrc_ts()}{seg.transcript}" for seg in self.segments
        )

    def to_ass(self) -> str:
        """Convert to ASS subtitle format"""
        raise NotImplementedError("ASS format conversion not implemented yet")

    def to_json(self) -> dict:
        result_json = {}
        for i, segment in enumerate(self.segments):
            result_json[i] = segment.text
        return result_json

    def __str__(self):
        return self.to_txt()


if __name__ == '__main__':
    pass
    # asr_data = ASRData(seg)
    # Uncomment to test different formats:
    # print(asr_data.to_srt())
    # print(asr_data.to_lrc())
    # print(asr_data.to_txt())
    # print(asr_data.to_json())
    # print(asr_data.to_json())




