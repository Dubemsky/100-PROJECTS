import qrcode
import customtkinter as ctk
from tkinter import colorchooser, filedialog
from PIL import Image, ImageDraw

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("QR Code Generator")
app.configure(fg_color="#f0f0f0")


colors = {"qr": "#000000", "background": "#ffffff"}
logo = {"path": None}
last_qr_image = {"image": None}


# builds the QR data string for whichever input mode is currently selected
def get_qr_data():
    mode = mode_selector.get()

    if mode == "WiFi":
        ssid = wifi_ssid_entry.get()
        password = wifi_password_entry.get()
        encryption_code = {"WPA/WPA2": "WPA", "WEP": "WEP", "None": "nopass"}[wifi_encryption_menu.get()]
        return f"WIFI:T:{encryption_code};S:{ssid};P:{password};;"

    return text_entry.get()


# builds a QR code image from the chosen input, colors, and optional logo, then shows it
def generate_qr_code():
    text = get_qr_data()
    if not text:
        return

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(text)
    qr_image = qr.make_image(fill_color=colors["qr"], back_color=colors["background"]).convert("RGB")

    if logo["path"]:
        logo_image = Image.open(logo["path"]).convert("RGBA")
        logo_size = qr_image.size[0] // 4
        logo_image = logo_image.resize((logo_size, logo_size))
        position = ((qr_image.size[0] - logo_size) // 2, (qr_image.size[1] - logo_size) // 2)

        padding = 10
        box_position = (position[0] - padding, position[1] - padding)
        box_end = (box_position[0] + logo_size + padding * 2, box_position[1] + logo_size + padding * 2)
        ImageDraw.Draw(qr_image).rounded_rectangle([box_position, box_end], radius=12, fill="white")

        qr_image.paste(logo_image, position, mask=logo_image)

    last_qr_image["image"] = qr_image

    qr_display_image = qr_image.resize((170, 170))
    ctk_image = ctk.CTkImage(light_image=qr_display_image, size=(170, 170))
    qr_label.configure(image=ctk_image, text="")


# opens the color picker and updates the given swatch button
def pick_color(color_key, swatch_button):
    picked_color = colorchooser.askcolor(color=colors[color_key])[1]
    if picked_color:
        colors[color_key] = picked_color
        swatch_button.configure(fg_color=picked_color)


# opens a file picker to choose a logo image
def choose_logo():
    path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
    if path:
        logo["path"] = path
        logo_button.configure(text="Logo Selected ✓")


# saves the last generated QR code to a PNG file
def save_qr_code():
    if not last_qr_image["image"]:
        return

    path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
    if path:
        last_qr_image["image"].save(path)


# toggles the wifi password between hidden and visible
def toggle_password_visibility():
    if wifi_password_entry.cget("show") == "":
        wifi_password_entry.configure(show="•")
        password_toggle_button.configure(text="👁")
    else:
        wifi_password_entry.configure(show="")
        password_toggle_button.configure(text="🙈")


# shows the input frame for the chosen mode and hides the others
def switch_mode(mode):
    for frame in input_frames.values():
        frame.pack_forget()
    input_frames[mode].pack()



card = ctk.CTkFrame(app, corner_radius=16, fg_color="white", border_width=1, border_color="#e5e5e5")
card.pack(padx=20, pady=20)

title_label = ctk.CTkLabel(card, text="QR Code Generator", font=("Arial", 18, "bold"), text_color="black")
title_label.pack(pady=(15, 10))

# mode selector: switches which input frame below is shown
mode_selector = ctk.CTkSegmentedButton(
    card,
    values=["URL/Text", "WiFi"],
    selected_color="#2f5fdc",
    selected_hover_color="#2549b0",
    command=switch_mode,
)
mode_selector.set("URL/Text")
mode_selector.pack(pady=(0, 8))

# fixed-height area so the layout doesn't jump when switching modes
input_area = ctk.CTkFrame(card, width=380, height=105, fg_color="transparent")
input_area.pack()
input_area.pack_propagate(False)

# URL/Text input
url_frame = ctk.CTkFrame(input_area, fg_color="transparent")
text_entry = ctk.CTkEntry(
    url_frame,
    width=360,
    height=36,
    corner_radius=10,
    fg_color="#f7f7f7",
    border_width=1,
    border_color="#e0e0e0",
    placeholder_text="Enter text or a URL",
)
text_entry.pack(pady=5)

# WiFi input
wifi_frame = ctk.CTkFrame(input_area, fg_color="transparent")
wifi_ssid_entry = ctk.CTkEntry(
    wifi_frame,
    width=360,
    height=32,
    corner_radius=10,
    fg_color="#f7f7f7",
    border_width=1,
    border_color="#e0e0e0",
    placeholder_text="Network name (SSID)",
)
wifi_ssid_entry.pack(pady=(0, 5))
password_row = ctk.CTkFrame(wifi_frame, fg_color="transparent")
password_row.pack(pady=(0, 5))

wifi_password_entry = ctk.CTkEntry(
    password_row,
    width=315,
    height=32,
    corner_radius=10,
    fg_color="#f7f7f7",
    border_width=1,
    border_color="#e0e0e0",
    placeholder_text="Password",
    show="•",
)
wifi_password_entry.pack(side="left", padx=(0, 5))

password_toggle_button = ctk.CTkButton(
    password_row,
    text="🙈",
    width=32,
    height=32,
    corner_radius=8,
    fg_color="#e0e0e0",
    text_color="black",
    hover_color="#cfcfcf",
    command=toggle_password_visibility,
)
password_toggle_button.pack(side="left")
wifi_encryption_menu = ctk.CTkOptionMenu(
    wifi_frame, width=360, height=32, corner_radius=10, values=["WPA/WPA2", "WEP", "None"]
)
wifi_encryption_menu.pack()

input_frames = {"URL/Text": url_frame, "WiFi": wifi_frame}
url_frame.pack()

# color pickers, side by side
color_row = ctk.CTkFrame(card, fg_color="transparent")
color_row.pack(pady=(2, 6))

qr_color_label = ctk.CTkLabel(color_row, text="QR COLOR", font=("Arial", 11, "bold"), text_color="#999999")
qr_color_label.grid(row=0, column=0, padx=45)

bg_color_label = ctk.CTkLabel(color_row, text="BACKGROUND", font=("Arial", 11, "bold"), text_color="#999999")
bg_color_label.grid(row=0, column=1, padx=45)

qr_color_swatch = ctk.CTkButton(color_row, text="", width=60, height=28, corner_radius=8, fg_color=colors["qr"], border_width=1, border_color="#d0d0d0")
qr_color_swatch.configure(command=lambda: pick_color("qr", qr_color_swatch))
qr_color_swatch.grid(row=1, column=0, padx=45, pady=3)

bg_color_swatch = ctk.CTkButton(color_row, text="", width=60, height=28, corner_radius=8, fg_color=colors["background"], border_width=1, border_color="#d0d0d0")
bg_color_swatch.configure(command=lambda: pick_color("background", bg_color_swatch))
bg_color_swatch.grid(row=1, column=1, padx=45, pady=3)

logo_button = ctk.CTkButton(
    card,
    text="Choose Logo (optional)",
    width=280,
    height=30,
    corner_radius=15,
    fg_color="#e0e0e0",
    text_color="black",
    hover_color="#cfcfcf",
    command=choose_logo,
)
logo_button.pack(pady=(0, 8))

generate_button = ctk.CTkButton(
    card,
    text="Generate",
    width=280,
    height=36,
    corner_radius=18,
    font=("Arial", 14, "bold"),
    fg_color="#2f5fdc",
    hover_color="#2549b0",
    command=generate_qr_code,
)
generate_button.pack(pady=(0, 10))

qr_display_frame = ctk.CTkFrame(card, width=190, height=190, corner_radius=12, fg_color="#f7f7f7", border_width=1, border_color="#e5e5e5")
qr_display_frame.pack()
qr_display_frame.pack_propagate(False)

qr_label = ctk.CTkLabel(qr_display_frame, text="Your QR code\nwill appear here", text_color="#999999")
qr_label.pack(expand=True)

save_button = ctk.CTkButton(
    card,
    text="Save as PNG",
    width=280,
    height=34,
    corner_radius=17,
    fg_color="#e0e0e0",
    text_color="black",
    hover_color="#cfcfcf",
    command=save_qr_code,
)
save_button.pack(pady=(8, 15))

app.resizable(False, False)
app.mainloop()
