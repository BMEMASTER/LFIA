import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

# 创建主窗口
root = tk.Tk()
root.title("DPI 转换器")
root.geometry("500x300")
root.config(bg="#f0f0f0")

# 全局变量，用于存储选择的图片路径
selected_image_path = None


# 选择图片的回调函数
def select_image():
    global selected_image_path
    selected_image_path = filedialog.askopenfilename(title="选择图片",
                                                     filetypes=[("Image files", "*.jpg *.png *.jpeg *.bmp")])
    if selected_image_path:
        image_label.config(text=f"已选择图片: {selected_image_path}", fg="green")
    else:
        image_label.config(text="未选择图片", fg="red")


# 转换 DPI 的回调函数
def convert_dpi():
    global selected_image_path
    if not selected_image_path:
        messagebox.showwarning("警告", "请选择图片")
        return

    try:
        # 获取用户输入的 DPI
        new_dpi = int(dpi_entry.get())
        if new_dpi <= 0:
            raise ValueError("DPI 应该是一个正整数")
    except ValueError:
        messagebox.showerror("错误", "请输入有效的 DPI 数值")
        return

    # 打开图片
    image = Image.open(selected_image_path)

    # 获取图片的像素尺寸和当前 DPI
    pixel_width, pixel_height = image.size
    dpi = image.info.get('dpi', (72, 72))
    dpi_width, dpi_height = dpi

    # 计算物理尺寸
    physical_width_in_inches = pixel_width / dpi_width
    physical_height_in_inches = pixel_height / dpi_height

    # 计算新像素尺寸
    new_pixel_width = int(physical_width_in_inches * new_dpi)
    new_pixel_height = int(physical_height_in_inches * new_dpi)

    # 调整图片大小
    resized_image = image.resize((new_pixel_width, new_pixel_height))

    # 保存图片
    save_path = filedialog.asksaveasfilename(defaultextension=".png",
                                             filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")])
    if save_path:
        resized_image.save(save_path, dpi=(new_dpi, new_dpi))
        messagebox.showinfo("成功", f"图片已成功保存为 {new_dpi} DPI")


# 创建一个上方的标题框架
title_frame = tk.Frame(root, bg="#f0f0f0")
title_frame.pack(pady=10)

title_label = tk.Label(title_frame, text="图片 DPI 转换器", font=("Helvetica", 18, "bold"), bg="#f0f0f0", fg="#333")
title_label.pack()

# 创建选择图片的按钮框架
image_frame = tk.Frame(root, bg="#f0f0f0")
image_frame.pack(pady=10)

select_image_button = tk.Button(image_frame, text="选择图片", command=select_image, width=20, height=2, bg="#4CAF50",
                                fg="white", font=("Helvetica", 10, "bold"))
select_image_button.pack(pady=10)

# 显示选择的图片路径
image_label = tk.Label(image_frame, text="未选择图片", bg="#f0f0f0", fg="red", font=("Helvetica", 10))
image_label.pack()

# 创建 DPI 输入框
dpi_frame = tk.LabelFrame(root, text="设置 DPI", bg="#f0f0f0", font=("Helvetica", 12))
dpi_frame.pack(pady=20, padx=20, fill="x")

dpi_label = tk.Label(dpi_frame, text="请输入新的 DPI:", bg="#f0f0f0", font=("Helvetica", 10))
dpi_label.pack(side="left", padx=10)

dpi_entry = tk.Entry(dpi_frame, width=10, font=("Helvetica", 10))
dpi_entry.pack(side="left", padx=10)

# 创建转换按钮
convert_button = tk.Button(root, text="转换 DPI", command=convert_dpi, width=20, height=2, bg="#2196F3", fg="white",
                           font=("Helvetica", 10, "bold"))
convert_button.pack(pady=20)

# 运行主循环
root.mainloop()
