import pyautogui
import time
from datetime import datetime
import os
import ddddocr
import tkinter as tk  # 新增

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class SimpleScreenshotApp:
    def __init__(self):
        self.x1 = self.y1 = self.x2 = self.y2 = None
        self.save_dir = os.path.join(SCRIPT_DIR, "screenshots")
        self.running = True
        self.max_files = 10
        self.file_list = []
        self.ocr = ddddocr.DdddOcr(show_ad=False)

    def select_region(self):
        """使用鼠标拖动选取截图区域，屏幕实时显示矩形框"""
        print("请按住鼠标左键拖动选取截图区域，释放后完成选择")
        print("（屏幕上会出现半透明窗口，拖动时显示矩形框）")

        root = tk.Tk()
        root.attributes('-fullscreen', True)      # 全屏
        root.attributes('-topmost', True)         # 置顶
        root.attributes('-alpha', 0.3)            # 半透明，可看到下方内容
        root.overrideredirect(True)               # 无标题栏
        root.config(cursor='cross')               # 十字光标

        canvas = tk.Canvas(root, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        rect = None
        start_x = start_y = None

        def on_press(event):
            nonlocal start_x, start_y, rect
            start_x, start_y = event.x, event.y
            if rect:
                canvas.delete(rect)
            # 创建矩形（仅边框，红色，2像素宽）
            rect = canvas.create_rectangle(start_x, start_y, start_x, start_y,
                                           outline='red', width=2)

        def on_drag(event):
            nonlocal rect
            if rect:
                # 更新矩形右下角坐标
                canvas.coords(rect, start_x, start_y, event.x, event.y)

        def on_release(event):
            nonlocal start_x, start_y
            # 记录最终坐标（相对于窗口，全屏下即屏幕坐标）
            self.x1, self.y1 = start_x, start_y
            self.x2, self.y2 = event.x, event.y
            root.destroy()  # 关闭窗口

        canvas.bind('<ButtonPress-1>', on_press)
        canvas.bind('<B1-Motion>', on_drag)
        canvas.bind('<ButtonRelease-1>', on_release)

        root.mainloop()

        # 检查是否有效选取
        if self.x1 is None or self.x2 is None:
            print("未完成选择，请重试")
            return False

        # 保证左上角坐标小于右下角
        self.x1, self.x2 = min(self.x1, self.x2), max(self.x1, self.x2)
        self.y1, self.y2 = min(self.y1, self.y2), max(self.y1, self.y2)

        print(f"截图区域: ({self.x1}, {self.y1}) → ({self.x2}, {self.y2})")
        print(f"区域大小: {self.x2-self.x1} x {self.y2-self.y1} 像素")
        return True

    def take_screenshot(self):
        """执行截图并保存，同时进行OCR识别"""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        screenshot = pyautogui.screenshot(
            region=(self.x1, self.y1, self.x2 - self.x1, self.y2 - self.y1)
        )
        now = datetime.now()
        filename = f"{now.year}年-{now.month:02d}月-{now.day:02d}日-{now.hour:02d}h-{now.minute:02d}m-{now.second:02d}s.png"
        filepath = os.path.join(self.save_dir, filename)
        screenshot.save(filepath)
        print(f"[{now.strftime('%H:%M:%S')}] 已保存: {filename}")

        with open(filepath, 'rb') as f:
            img_bytes = f.read()
        ocr_result = self.ocr.classification(img_bytes)
        print(f"{filename} → {ocr_result}")

        self.file_list.append(filepath)

        if len(self.file_list) > self.max_files:
            oldest = self.file_list.pop(0)
            if os.path.exists(oldest):
                os.remove(oldest)
                print(f"已删除旧截图: {os.path.basename(oldest)}")

    def run(self):
        if not self.select_region():
            return

        if os.path.exists(self.save_dir):
            for f in os.listdir(self.save_dir):
                os.remove(os.path.join(self.save_dir, f))
        
        print(f"\n开始定时截图（每5秒），最多保留{self.max_files}张")
        print("按 Ctrl+C 停止程序")

        try:
            while self.running:
                self.take_screenshot()
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n程序已停止")

if __name__ == "__main__":
    app = SimpleScreenshotApp()
    app.run()