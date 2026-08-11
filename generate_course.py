"""Generate the two-hour, image-oriented Fourier transform notebook course."""
from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parent


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": dedent(text).strip() + "\n"}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": dedent(text).strip() + "\n",
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


COMMON = code(r'''
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams["figure.figsize"] = (10, 4)
plt.rcParams["image.cmap"] = "gray"
plt.rcParams["axes.grid"] = True
# 优先使用常见中文字体；最后的 DejaVu Sans 保证数字和英文正常显示
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

def show_images(images, titles, cmap="gray"):
    """并排显示若干幅图像。"""
    fig, axes = plt.subplots(1, len(images), figsize=(5 * len(images), 4))
    axes = np.atleast_1d(axes)
    for ax, image, title in zip(axes, images, titles):
        ax.imshow(image, cmap=cmap)
        ax.set_title(title)
        ax.axis("off")
    plt.tight_layout()
    plt.show()
''')


COURSE = {
"00_从波到频谱_25分钟.ipynb": notebook([
md(r'''
# 第 0 课：从波到频谱

## 学完你能做什么

- 用“配方表”解释频谱，而不是死背公式；
- 看懂频率、振幅、相位；
- 用 `np.fft.fft` 找出一维信号中隐藏的周期。

> 两小时原则：先运行、拖动参数、观察，再读解释。暂时不用推导积分公式。
'''),
COMMON,
md(r'''
## 0. 傅里叶变换需要的数学：一圈、正弦与弧度

高中三角函数常用角度，但 Python 的 `sin` 使用**弧度**：

- 走完一整圈：360° = $2\pi$ 弧度；
- 半圈：180° = $\pi$ 弧度；
- 四分之一圈：90° = $\pi/2$ 弧度。

想象一个点沿圆周匀速旋转。这个点的纵坐标随时间变化，画出来就是正弦波。正弦波不是凭空出现的公式，它是“匀速转圈在竖直方向上的投影”。
'''),
code(r'''
angles = np.linspace(0, 2*np.pi, 400)
selected = np.array([0, np.pi/2, np.pi, 3*np.pi/2, 2*np.pi])

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

# 左：圆周运动
axes[0].plot(np.cos(angles), np.sin(angles))
axes[0].scatter(np.cos(selected), np.sin(selected), zorder=3)
for a, label in zip(selected, ["0", "π/2", "π", "3π/2", "2π"]):
    axes[0].annotate(label, (np.cos(a), np.sin(a)), xytext=(5, 5), textcoords="offset points")
axes[0].axhline(0, color="gray", linewidth=0.8)
axes[0].axvline(0, color="gray", linewidth=0.8)
axes[0].set_aspect("equal")
axes[0].set_title("走一圈：角度从 0 到 2π")
axes[0].set_xlabel("横坐标 cos(角度)")
axes[0].set_ylabel("纵坐标 sin(角度)")

# 右：圆上点的纵坐标展开成波
axes[1].plot(angles, np.sin(angles))
axes[1].scatter(selected, np.sin(selected), zorder=3)
axes[1].set_xticks(selected)
axes[1].set_xticklabels(["0", "π/2", "π", "3π/2", "2π"])
axes[1].set_title("把纵坐标展开，就得到正弦波")
axes[1].set_xlabel("转过的角度（弧度）")
axes[1].set_ylabel("sin(角度)")
plt.tight_layout(); plt.show()
'''),
md(r'''
## 0.1 看懂工程里常见的正弦公式

$$y(t)=A\sin(2\pi f t+\varphi)$$

不需要推导，只要读懂每个零件：

- $t$：时间；
- $A$：振幅，控制上下摆动有多高；
- $f$：频率，控制每秒转几圈，单位 Hz；
- $2\pi ft$：经过 $t$ 秒一共转了多少弧度；
- $\varphi$（读作 phi）：相位，表示出发前已经提前转了多少角度。

`2 * np.pi * f * t` 就是公式 $2\pi ft$ 的 Python 写法。
'''),
code(r'''
t_demo = np.linspace(0, 1, 500)
f_demo = 2

plt.figure(figsize=(11, 4))
for phase, label in [(0, "相位 0"), (np.pi/2, "相位 π/2"), (np.pi, "相位 π")]:
    plt.plot(t_demo, np.sin(2*np.pi*f_demo*t_demo + phase), label=label)
plt.axvline(0, color="gray", linewidth=0.8)
plt.xlabel("时间（秒）")
plt.ylabel("振幅")
plt.title("相位只让波左右错开，不改变频率和振幅")
plt.legend(); plt.show()
'''),
md(r'''
上图三条波每秒都重复 2 次，振幅也都是 1，区别只是从周期中的不同位置出发。因此：

> **相位描述同一种周期变化在什么位置。** 对图像而言，它对边缘和物体出现在什么位置非常重要。
'''),
md(r'''
## 0.2 从直角坐标系到“换一套坐标轴”

先不谈傅里叶。平面上的同一个箭头，可以用不同坐标系描述：

- 在普通直角坐标系中，它由“水平方向多少、竖直方向多少”描述；
- 把坐标轴旋转后，箭头没有变化，但两个坐标值变了。

所以**换坐标系不是改变对象，而是改用另一套基本方向描述同一个对象**。
'''),
code(r'''
v = np.array([2.4, 1.6])
theta = np.deg2rad(35)
e1 = np.array([np.cos(theta), np.sin(theta)])
e2 = np.array([-np.sin(theta), np.cos(theta)])
new_coordinates = np.array([v @ e1, v @ e2])

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

def draw_vector_and_basis(ax, basis1, basis2, labels, coordinates, title):
    ax.arrow(0, 0, v[0], v[1], width=0.025, length_includes_head=True,
             color="tab:red", label="同一个箭头 v")
    scale = 3.2
    ax.arrow(0, 0, *(scale*basis1), width=0.012, length_includes_head=True,
             color="tab:blue")
    ax.arrow(0, 0, *(scale*basis2), width=0.012, length_includes_head=True,
             color="tab:green")
    ax.text(*(2.7*basis1), labels[0], color="tab:blue")
    ax.text(*(2.7*basis2), labels[1], color="tab:green")
    ax.text(v[0], v[1]+0.2, f"坐标 = ({coordinates[0]:.2f}, {coordinates[1]:.2f})",
            ha="center", color="tab:red")
    ax.set_xlim(-2.5, 3.5); ax.set_ylim(-1.0, 3.5)
    ax.set_aspect("equal"); ax.set_title(title)
    ax.axhline(0, color="gray", linewidth=0.7); ax.axvline(0, color="gray", linewidth=0.7)
    ax.grid(True)

draw_vector_and_basis(axes[0], np.array([1,0]), np.array([0,1]),
                      ["x 轴", "y 轴"], v, "普通直角坐标系")
draw_vector_and_basis(axes[1], e1, e2,
                      ["旋转后的轴 1", "旋转后的轴 2"], new_coordinates, "旋转后的坐标系")
plt.tight_layout(); plt.show()
'''),
md(r'''
傅里叶变换做的是同一类事情，只是对象从二维箭头换成了一整段信号：

- 普通描述：第 0 个时刻是多少、第 1 个时刻是多少……这些采样值就是原坐标；
- 傅里叶描述：0 Hz 波有多少、1 Hz 波有多少、2 Hz 波有多少……这些波的含量就是新坐标。

二维空间只有两根坐标轴；含有 $N$ 个采样点的信号可以看作一个 $N$ 维向量。人无法画出 $N$ 维空间，但“换一组基本方向”的原理完全相同。

> 普通坐标轴关注每个位置；傅里叶坐标轴是一组不同频率的正弦波和余弦波。
'''),
md(r'''
## 1. 正弦波是频域的基本积木

正弦波可以理解为一种永不改变节奏的振动：

- **频率**：每秒重复几次，单位 Hz；
- **振幅**：波有多强；
- **相位**：波从周期中的哪个位置开始。

下面把 3 Hz 和 8 Hz 的波相加。观察混合信号很复杂，但它的“配方”只有两项。
'''),
code(r'''
sample_rate = 100       # 每秒采 100 个点
duration = 2            # 共观察 2 秒
t = np.arange(0, duration, 1 / sample_rate)

wave_3hz = 1.0 * np.sin(2 * np.pi * 3 * t)
wave_8hz = 0.45 * np.sin(2 * np.pi * 8 * t + 0.7)
mixed = wave_3hz + wave_8hz

fig, axes = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
for ax, y, title in zip(axes, [wave_3hz, wave_8hz, mixed],
                        ["3 Hz，振幅 1.0", "8 Hz，振幅 0.45，相位偏移 0.7", "两者相加"]):
    ax.plot(t, y)
    ax.set_title(title)
    ax.set_ylabel("振幅")
axes[-1].set_xlabel("时间（秒）")
plt.tight_layout()
plt.show()
'''),
md(r'''
## 1.1 怎样测量信号在某根“频率坐标轴”上有多少？

在直角坐标系里，我们把箭头投影到 x 轴、y 轴来得到坐标。傅里叶变换也做投影：依次拿不同频率的波与原信号比较。

- 节奏匹配时，同向部分会不断累加，得到较大的坐标；
- 节奏不匹配时，正负部分互相抵消，坐标接近零。

下面暂时不用 `fft`，而是手动让 0～15 Hz 的“探测波”逐一试探。正弦和余弦都要测，是为了不被相位错开影响。
'''),
code(r'''
candidate_freqs = np.linspace(0, 15, 301)
coordinates = []

for f in candidate_freqs:
    cosine_axis = np.cos(2*np.pi*f*t)
    sine_axis = np.sin(2*np.pi*f*t)
    coordinate_cos = 2/len(t) * np.sum(mixed * cosine_axis)
    coordinate_sin = 2/len(t) * np.sum(mixed * sine_axis)
    coordinates.append(np.sqrt(coordinate_cos**2 + coordinate_sin**2))

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(t, mixed)
axes[0].set_xlim(0, 1)
axes[0].set_xlabel("时间（秒）"); axes[0].set_ylabel("信号值")
axes[0].set_title("原坐标：每个时刻的采样值")

axes[1].plot(candidate_freqs, coordinates)
axes[1].set_xlabel("作为坐标轴的波的频率（Hz）")
axes[1].set_ylabel("投影大小 / 该频率的含量")
axes[1].set_title("傅里叶坐标：每种频率的含量")
axes[1].axvline(3, color="tab:red", linestyle="--")
axes[1].axvline(8, color="tab:red", linestyle="--")
plt.tight_layout(); plt.show()
'''),
md(r'''
右图在 3 Hz 和 8 Hz 出现峰，因为原信号正是由这两个频率组成。这幅图就是傅里叶变换最核心的直觉：

> **不是把波形神奇地“变成”频谱，而是在一组波形坐标轴上重新读取同一个信号的坐标。**

手动试探很慢；FFT 是一种高效算法，可以一次算出所有这些坐标。
'''),
md(r'''
## 2. 傅里叶变换在回答什么？

时域问：“每个时刻的值是多少？” 频域问：“这个信号由哪些频率组成，各有多强？”

`fft` 产生复数。现阶段记住：

- `abs(FFT)` 给出强度（幅度谱）；
- `angle(FFT)` 给出相位；
- 实信号的负频率部分与正频率镜像，所以工程中常看 `rfft`。
'''),
md(r'''
### 先把 FFT 函数当作工程工具使用

```python
F = np.fft.rfft(signal)                     # 输入一维实数信号，得到频率成分
freqs = np.fft.rfftfreq(len(signal), 1/fs)  # 为每个频率成分生成 Hz 坐标
amplitude = np.abs(F)                       # 取每个频率成分的强度
signal_back = np.fft.irfft(F)               # 从频域还原为信号
```

`F` 不是一张可以直接看的图，而是一组复数。画频谱时，横坐标用 `freqs`，纵坐标通常用 `np.abs(F)`。
'''),
code(r'''
F = np.fft.rfft(mixed)
freqs = np.fft.rfftfreq(len(mixed), d=1 / sample_rate)

# 除以样本数并乘 2，把柱高换算回正弦波振幅（直流项除外）
amplitude = 2 * np.abs(F) / len(mixed)
amplitude[0] /= 2

plt.figure(figsize=(11, 4))
plt.stem(freqs, amplitude, basefmt=" ")
plt.xlim(0, 15)
plt.xlabel("频率（Hz）")
plt.ylabel("振幅")
plt.title("混合信号的单边幅度谱：峰的位置=频率，峰的高度=强度")
plt.show()
'''),
md(r'''
## 2.1 为什么 FFT 会产生复数？

一个实数只能记录一条数轴上的位置；复数使用两个数 `(实部, 虚部)` 记录平面上的一个点。FFT 用这个平面点同时表达：

- 点离原点多远 → 该频率有多强，即**幅度**；
- 点朝哪个方向 → 该频率转到了周期中的什么位置，即**相位**。

工程中可以把复数理解为“同时装着幅度和相位的容器”。`abs(z)` 取距离，`angle(z)` 取方向。
'''),
code(r'''
phases = np.array([0.2, 0.9, 1.7, 2.7])
amplitudes = np.array([1.0, 1.0, 1.0, 1.0])
z = amplitudes * np.exp(1j * phases)

fig, ax = plt.subplots(figsize=(6, 6))
circle = np.linspace(0, 2*np.pi, 300)
ax.plot(np.cos(circle), np.sin(circle), color="gray", alpha=0.5)
for point, phase in zip(z, phases):
    ax.arrow(0, 0, point.real, point.imag, head_width=0.05,
             length_includes_head=True)
    ax.text(point.real*1.08, point.imag*1.08, f"相位 {phase:.1f}", ha="center")
ax.axhline(0, color="gray", linewidth=0.8); ax.axvline(0, color="gray", linewidth=0.8)
ax.set_aspect("equal"); ax.set_xlim(-1.25, 1.25); ax.set_ylim(-1.25, 1.25)
ax.set_xlabel("实部"); ax.set_ylabel("虚部")
ax.set_title("复数：箭头长度表示幅度，方向表示相位")
plt.show()
'''),
md(r'''
上面的 `np.exp(1j * phases)` 暂时不要求会推导。它的作用只是：“根据给定相位，在复数平面上生成相应方向的箭头”。

## 2.2 负频率到底是什么？

正频率和负频率不是“频率小于零”或“时间倒流”，而是复数平面上的两个旋转方向：

- 正频率：一个方向旋转；
- 负频率：相反方向旋转。

真实的正弦或余弦信号可以看成两个相反方向的旋转合在一起，所以完整 FFT 会在 `+f` 和 `-f` 各出现一个对称峰。处理实数信号时，负频率通常没有新增信息，因此 `rfft` 只返回不重复的右半边。
'''),
code(r'''
cosine = np.cos(2*np.pi*3*t)
F_full = np.fft.fftshift(np.fft.fft(cosine))
freq_full = np.fft.fftshift(np.fft.fftfreq(len(cosine), d=1/sample_rate))

plt.figure(figsize=(11, 4))
plt.stem(freq_full, np.abs(F_full)/len(cosine), basefmt=" ")
plt.xlim(-10, 10)
plt.xlabel("频率（Hz）")
plt.ylabel("强度")
plt.title("完整 FFT：3 Hz 真实余弦波在 -3 Hz 和 +3 Hz 各有一个峰")
plt.show()
'''),
md(r'''
### 你需要掌握到什么程度？

- 要会：实数信号的完整频谱左右对称，`rfft` 可以只看非负频率；
- 要会：复数的长度保存幅度，方向保存相位；
- 暂时不用：用欧拉公式推导正弦波为什么等于两个反向旋转。
'''),
md(r'''
### 现在请回答（先猜，再运行）

1. 哪两个频率峰最高？
2. 8 Hz 的峰为什么比 3 Hz 低？
3. 把 `wave_8hz` 的振幅从 `0.45` 改成 `1.5`，频谱如何变化？

答案：3 Hz 和 8 Hz；因为设定振幅较小；改振幅只改变对应峰高，不改变峰的位置。
'''),
md(r'''
## 3. 图像里的“频率”是什么？

图像没有时间轴，但有空间坐标。空间频率描述亮暗变化得多快：

- 平缓背景：低频；
- 细纹理、文字、边缘：高频；
- 水平方向快速明暗交替，会在频域水平方向出现离中心较远的能量。

下一课将把这套直觉扩展到二维。
'''),
md(r'''
## 本课最小记忆卡

`信号 --FFT--> 频谱`，`频谱 --逆 FFT--> 信号`

- 峰在哪里 → 有什么频率；
- 峰多高 → 该频率有多强；
- 高频不是“数值高”，而是“变化快”。
'''),
]),

"01_二维FFT看懂图像_30分钟.ipynb": notebook([
md(r'''
# 第 1 课：二维 FFT 看懂图像（约 30 分钟）

目标：知道二维频谱的中心、方向和距离分别代表什么，并能用代码显示图像频谱。
'''),
COMMON,
md(r'''
## 1. 先造几幅可控图像

这样我们确切知道图像中有什么，不需要下载样例图片。
'''),
code(r'''
n = 256
y, x = np.mgrid[0:n, 0:n]

vertical_stripes = 0.5 + 0.5 * np.sin(2 * np.pi * x / 16)
horizontal_stripes = 0.5 + 0.5 * np.sin(2 * np.pi * y / 32)
checker = 0.5 + 0.25 * np.sin(2 * np.pi * x / 16) + 0.25 * np.sin(2 * np.pi * y / 32)

show_images([vertical_stripes, horizontal_stripes, checker],
            ["竖条纹", "横条纹", "两个方向叠加"])
'''),
md(r'''
## 2. 二维 FFT 与频谱显示

- `fft2`：二维傅里叶变换；
- `fftshift`：把零频（最慢变化）移到画面中心，便于人看；
- `log1p(abs(F))`：频谱强弱跨度很大，取对数后暗处才看得见。

注意：对数只用于**显示**，真正处理仍使用原始复数频谱 `F`。
'''),
code(r'''
def spectrum_image(image):
    F = np.fft.fft2(image)
    F_centered = np.fft.fftshift(F)
    display = np.log1p(np.abs(F_centered))
    return F_centered, display

fig, axes = plt.subplots(3, 2, figsize=(9, 12))
for row, (image, name) in enumerate([
    (vertical_stripes, "竖条纹"),
    (horizontal_stripes, "横条纹"),
    (checker, "叠加")
]):
    F, spec = spectrum_image(image)
    axes[row, 0].imshow(image)
    axes[row, 0].set_title(name)
    axes[row, 1].imshow(spec)
    axes[row, 1].set_title(name + "的对数幅度谱")
    for ax in axes[row]: ax.axis("off")
plt.tight_layout()
plt.show()
'''),
md(r'''
## 读图口诀

1. **中心**代表直流与低频，即平均亮度和缓慢变化；
2. 离中心越远，空间变化越快；
3. 频谱亮点方向与图像变化方向一致，因此竖条纹沿 x 方向变化，亮点出现在频谱水平轴；
4. 实数图像的频谱通常中心对称。

这里很容易混淆：“竖条纹”本身竖着，但亮度是在左右移动时变化，所以频谱亮点左右展开。
'''),
md(r'''
## 3. 相位为何不能丢？

幅度大致记录“含有哪些纹理”，相位记录“这些结构放在哪里”。下面交换两幅图的幅度与相位。
'''),
code(r'''
# 两个简单物体，位置和形状不同
image_a = np.zeros((n, n)); image_a[45:125, 35:105] = 1
image_b = np.zeros((n, n));
circle = (x - 170) ** 2 + (y - 155) ** 2 < 48 ** 2
image_b[circle] = 1

Fa, Fb = np.fft.fft2(image_a), np.fft.fft2(image_b)

# A 的幅度 + B 的相位，反之亦然
a_mag_b_phase = np.real(np.fft.ifft2(np.abs(Fa) * np.exp(1j * np.angle(Fb))))
b_mag_a_phase = np.real(np.fft.ifft2(np.abs(Fb) * np.exp(1j * np.angle(Fa))))

show_images([image_a, image_b, a_mag_b_phase, b_mag_a_phase],
            ["A：矩形", "B：圆", "A幅度+B相位", "B幅度+A相位"])
'''),
md(r'''
### 工程结论

不要只保存幅度谱再期待完美还原图像。逆变换需要完整复数频谱，它同时包含幅度和相位。
'''),
md(r'''
## 小练习

把条纹周期 `/16` 改成 `/8`。频谱亮点应当离中心更远，因为周期更短、变化更快、频率更高。
'''),
]),

"02_频域滤波与图像增强_35分钟.ipynb": notebook([
md(r'''
# 第 2 课：频域滤波与图像增强（约 35 分钟）

目标：亲手完成低通、高通和周期噪声抑制，并理解它们在频谱上做了什么。
'''),
COMMON,
md(r'''
## 1. 构造一幅接近工程场景的测试图

包含缓慢背景、矩形边缘、细条纹和周期噪声。
'''),
code(r'''
n = 256
y, x = np.mgrid[0:n, 0:n]

background = 0.2 + 0.45 * x / n
objects = np.zeros((n, n))
objects[45:120, 35:110] = 0.55
objects[((x - 175) ** 2 + (y - 155) ** 2) < 42 ** 2] = 0.45
fine_texture = 0.08 * np.sin(2 * np.pi * x / 7) * (y > 170)
clean = np.clip(background + objects + fine_texture, 0, 1)

periodic_noise = 0.13 * np.sin(2 * np.pi * x / 12)
noisy = np.clip(clean + periodic_noise, 0, 1)
show_images([clean, noisy], ["干净图像", "加入竖向周期噪声"])
'''),
md(r'''
## 2. 低通滤波：只让中心附近通过

低频位于频谱中心。圆形低通掩膜保留中心、删除外围高频，结果是平滑/模糊。
'''),
code(r'''
def frequency_grid(shape):
    h, w = shape
    yy, xx = np.mgrid[:h, :w]
    return yy - h // 2, xx - w // 2

def apply_frequency_mask(image, mask):
    F = np.fft.fftshift(np.fft.fft2(image))
    filtered_F = F * mask
    result = np.real(np.fft.ifft2(np.fft.ifftshift(filtered_F)))
    return result, F, filtered_F

dy, dx = frequency_grid(noisy.shape)
radius = np.sqrt(dx ** 2 + dy ** 2)
cutoff = 22
low_pass = radius <= cutoff

smoothed, F, low_F = apply_frequency_mask(noisy, low_pass)
show_images([noisy, low_pass, smoothed],
            ["原图", f"低通掩膜（半径 {cutoff}）", "低通结果：噪声和细节都减少"])
'''),
md(r'''
### 观察实验

依次把 `cutoff` 改成 8、22、60：

- 截止半径小 → 保留频率少 → 更模糊；
- 截止半径大 → 保留更多细节，也可能保留更多噪声。

这就是滤波中的核心取舍：降噪与保留细节通常不能同时最大化。
'''),
md(r'''
## 3. 高通滤波：保留外围

高通删除慢变化的背景，突出边缘和细纹理。它不是魔法“锐化”，而是保留快速变化。
'''),
code(r'''
high_pass = radius > 14
edges, _, high_F = apply_frequency_mask(noisy, high_pass)

show_images([noisy, high_pass, edges],
            ["原图", "高通掩膜", "高频结果（边缘与纹理）"])
'''),
md(r'''
## 4. 工程实用招：陷波去除周期噪声

周期噪声往往在频谱中形成一对离散亮点。陷波（notch）只挖掉这对小区域，比大范围低通更能保护图像细节。
'''),
code(r'''
F_noisy = np.fft.fftshift(np.fft.fft2(noisy))
spec = np.log1p(np.abs(F_noisy))

plt.figure(figsize=(7, 6))
plt.imshow(spec)
plt.xlim(n//2 - 50, n//2 + 50)
plt.ylim(n//2 + 50, n//2 - 50)
plt.title("中心附近频谱：寻找左右对称的噪声亮点")
plt.axis("off")
plt.show()
'''),
code(r'''
# 噪声周期约 12 像素，因此频率索引约为 n/12
offset = round(n / 12)
notch_radius = 3
notch_mask = np.ones((n, n), dtype=float)

for cx in (n // 2 - offset, n // 2 + offset):
    notch = (x - cx) ** 2 + (y - n // 2) ** 2 <= notch_radius ** 2
    notch_mask[notch] = 0

denoised, _, notched_F = apply_frequency_mask(noisy, notch_mask)
show_images([noisy, notch_mask, np.clip(denoised, 0, 1), clean],
            ["含周期噪声", "陷波掩膜", "陷波结果", "参考干净图"])

mae_before = np.mean(np.abs(noisy - clean))
mae_after = np.mean(np.abs(denoised - clean))
print(f"处理前平均绝对误差: {mae_before:.4f}")
print(f"处理后平均绝对误差: {mae_after:.4f}")
'''),
md(r'''
## 5. 为什么硬边界掩膜可能出现振铃？

频域突然从 1 跳到 0，相当于使用“硬截止”，图像边缘附近可能出现波纹。工程中常用高斯/巴特沃斯等平滑掩膜。
'''),
code(r'''
sigma = 22
gaussian_low_pass = np.exp(-(radius ** 2) / (2 * sigma ** 2))
gaussian_result, _, _ = apply_frequency_mask(noisy, gaussian_low_pass)

hard_result, _, _ = apply_frequency_mask(noisy, radius <= sigma)
show_images([radius <= sigma, gaussian_low_pass, hard_result, gaussian_result],
            ["理想低通（硬边）", "高斯低通（平滑）", "硬截止结果", "高斯结果"])
'''),
md(r'''
## 本课最小记忆卡

- 低通：模糊、降噪；
- 高通：边缘、细节；
- 陷波：精准删除周期干扰；
- 掩膜边缘越硬，越容易振铃；
- 修改频谱后必须 `ifftshift` 再 `ifft2`。
'''),
]),

"03_采样陷阱与实战模板_30分钟.ipynb": notebook([
md(r'''
# 第 3 课：采样陷阱与实战模板（约 30 分钟）

目标：避开 FFT 工程中最常见的坑，并拿到可替换真实图片的处理模板。
'''),
COMMON,
md(r'''
## 1. 混叠：采得不够密会“看见假频率”

奈奎斯特原则：采样率至少要大于信号最高频率的 2 倍。图像中同理：过密纹理被像素网格错误记录，会产生摩尔纹。
'''),
code(r'''
true_frequency = 18
duration = 1

fig, axes = plt.subplots(2, 1, figsize=(11, 6))
for ax, fs in zip(axes, [100, 25]):
    t_dense = np.linspace(0, duration, 2000)
    t_sample = np.arange(0, duration, 1 / fs)
    ax.plot(t_dense, np.sin(2*np.pi*true_frequency*t_dense), alpha=0.35, label="真实 18 Hz")
    ax.plot(t_sample, np.sin(2*np.pi*true_frequency*t_sample), "o-", label=f"{fs} Hz 采样")
    ax.set_title(f"采样率 {fs} Hz；奈奎斯特频率 {fs/2:g} Hz")
    ax.set_xlabel("时间（秒）"); ax.set_ylabel("振幅"); ax.legend()
plt.tight_layout(); plt.show()
'''),
md(r'''
100 Hz 足以表达 18 Hz；25 Hz 的奈奎斯特频率只有 12.5 Hz，18 Hz 会伪装成更低频率。图像缩小时先做抗混叠滤波，正是为了避免这个问题。
'''),
md(r'''
## 2. 频谱泄漏：观察窗口装不下完整周期

FFT 默认截取片段首尾可以无缝相接。如果首尾断裂，这个跳变会制造大量额外频率。窗函数让两端平滑收敛，减少泄漏，但会让峰变宽。
'''),
code(r'''
fs = 100
n = 100
t = np.arange(n) / fs
signal = np.sin(2 * np.pi * 7.4 * t)  # 1 秒内不是整数个周期
window = np.hanning(n)

freq = np.fft.rfftfreq(n, 1/fs)
raw_spec = 2*np.abs(np.fft.rfft(signal))/n
win_spec = 2*np.abs(np.fft.rfft(signal*window))/np.sum(window)

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(t, signal, label="原信号")
axes[0].plot(t, signal*window, label="乘 Hann 窗")
axes[0].set_title("窗函数压低片段两端"); axes[0].legend()
axes[1].plot(freq, raw_spec, "o-", label="不加窗")
axes[1].plot(freq, win_spec, "o-", label="Hann 窗")
axes[1].set_xlim(0, 20); axes[1].set_title("泄漏减少，但主峰变宽")
axes[1].set_xlabel("频率（Hz）"); axes[1].legend()
plt.tight_layout(); plt.show()
'''),
md(r'''
## 3. 对图像做 FFT 的通用模板

把下面的 `image_path` 改成自己的图片路径。彩色图像先转灰度是为了学习方便；真实项目也可以分别处理 RGB 通道，或只处理亮度通道。
'''),
code(r'''
from pathlib import Path
from PIL import Image

image_path = Path("your_image.png")

if image_path.exists():
    image = np.asarray(Image.open(image_path).convert("L"), dtype=float) / 255.0
    print("已载入：", image_path, "尺寸：", image.shape)
else:
    print("未找到 your_image.png，改用合成示例；替换 image_path 即可处理自己的图。")
    n = 256
    yy, xx = np.mgrid[:n, :n]
    image = 0.35 + 0.25*np.sin(2*np.pi*xx/24) + 0.2*((xx-128)**2+(yy-128)**2 < 55**2)

F = np.fft.fftshift(np.fft.fft2(image))
spectrum_for_display = np.log1p(np.abs(F))
reconstructed = np.real(np.fft.ifft2(np.fft.ifftshift(F)))

show_images([image, spectrum_for_display, reconstructed],
            ["输入灰度图", "对数幅度谱", "未经修改的逆变换"])
print("重建最大绝对误差：", np.max(np.abs(image - reconstructed)))
'''),
md(r'''
## 4. 可复用滤波函数

接口设计：输入二维灰度图和掩膜，返回结果。掩膜必须与图像同尺寸，值通常在 0～1。
'''),
code(r'''
def fft_filter(image, mask):
    """使用给定的中心化频域掩膜过滤二维灰度图。"""
    if image.ndim != 2:
        raise ValueError("image 必须是二维灰度图")
    if image.shape != mask.shape:
        raise ValueError("mask 尺寸必须与 image 一致")
    F = np.fft.fftshift(np.fft.fft2(image))
    result = np.fft.ifft2(np.fft.ifftshift(F * mask))
    return np.real(result)

def gaussian_low_pass_mask(shape, sigma):
    h, w = shape
    y, x = np.mgrid[:h, :w]
    distance_sq = (x - w//2)**2 + (y - h//2)**2
    return np.exp(-distance_sq / (2*sigma**2))

mask = gaussian_low_pass_mask(image.shape, sigma=18)
filtered = fft_filter(image, mask)
show_images([image, mask, filtered], ["输入", "高斯低通掩膜", "输出"])
'''),
md(r'''
## 5. 最终检查清单

拿到一个真实图像频域任务时，按顺序问：

1. 我想删掉的是慢变化、高频细节，还是特定周期干扰？
2. 图像是否需要先转灰度/亮度通道？
3. 是否正确使用 `fftshift` 和 `ifftshift`？
4. 显示频谱时是否用了 `log1p(abs(F))`，处理时是否保留复数 `F`？
5. 掩膜是否中心对称、尺寸一致？
6. 硬截止是否导致振铃？
7. 结果是否用客观指标和原图对比，而不只是“看起来不错”？
'''),
md(r'''
# 两小时后你应当能解释

- 傅里叶变换：把图像从“每个位置多亮”转换为“各种空间变化模式有多强”；
- 二维频谱中心是低频，外侧是高频，方向表示变化方向；
- 低通、高通、陷波本质上都是给频谱乘一个掩膜；
- 逆变换能回到图像，但必须保留幅度和相位；
- 实际效果受采样、混叠、泄漏、截止方式影响。

如果这些话你能结合 Notebook 中的图解释出来，就已经达到工程入门目标。
'''),
]),
}


for filename, data in COURSE.items():
    (ROOT / filename).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("generated", filename)
