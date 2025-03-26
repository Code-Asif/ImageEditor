import streamlit as st
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps
import io

# Function to convert PIL Image to OpenCV format
def pil_to_cv(image):
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

# Function to convert OpenCV format to PIL Image
def cv_to_pil(image):
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

# Function to ensure image is displayed in horizontal layout
def ensure_horizontal(image):
    """Rotates image if its height is greater than width to maintain horizontal layout."""
    if image.height > image.width:
        return image.rotate(-90, expand=True)  # Rotate counterclockwise for horizontal view
    return image

# Function to apply filters
def apply_filter(image, filter_type):
    if filter_type == "Sepia":
        kernel = np.array([[0.272, 0.534, 0.131], [0.349, 0.686, 0.168], [0.393, 0.769, 0.189]])
        return cv2.transform(image, kernel)
    elif filter_type == "Black & White":
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif filter_type == "Blur":
        return cv2.GaussianBlur(image, (15, 15), 0)
    elif filter_type == "Sharpen":
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        return cv2.filter2D(image, -1, kernel)
    return image

# Function to auto-enhance image
def auto_enhance(image):
    img_pil = cv_to_pil(image)
    img_pil = ImageEnhance.Contrast(img_pil).enhance(1.5)
    img_pil = ImageEnhance.Brightness(img_pil).enhance(1.2)
    return pil_to_cv(img_pil)

# Function to remove blemishes (simple Gaussian Blur)
def remove_blemishes(image):
    return cv2.bilateralFilter(image, 9, 75, 75)

# Function to smooth skin
def smooth_skin(image):
    return cv2.edgePreservingFilter(image, flags=1, sigma_s=50, sigma_r=0.4)

# Streamlit UI
st.set_page_config(page_title="Image Editor", layout="wide")
st.title("🖼️ Creative Image Editor")

# File uploader
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    image = ImageOps.exif_transpose(image)  # Fix orientation
    image = ensure_horizontal(image)  # Ensure horizontal layout
    img_cv = pil_to_cv(image)

    # Sidebar options
    st.sidebar.title("Editing Options")

    # Cropping
    crop = st.sidebar.checkbox("Crop Image")
    if crop:
        x1, x2 = st.sidebar.slider("Select Width Range", 0, image.width, (0, image.width))
        y1, y2 = st.sidebar.slider("Select Height Range", 0, image.height, (0, image.height))
        img_cv = img_cv[y1:y2, x1:x2]

    # Resize
    resize = st.sidebar.checkbox("Resize Image")
    if resize:
        width = st.sidebar.slider("Width", 10, 1000, image.width)
        height = st.sidebar.slider("Height", 10, 1000, image.height)
        img_cv = cv2.resize(img_cv, (width, height))

    # Rotate & Flip
    rotate = st.sidebar.radio("Rotate", [0, 90, 180, 270], index=0)
    if rotate in [90, 180, 270]:
        img_cv = cv2.rotate(img_cv, {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}[rotate])

    flip = st.sidebar.radio("Flip", ["None", "Horizontal", "Vertical"], index=0)
    if flip == "Horizontal":
        img_cv = cv2.flip(img_cv, 1)
    elif flip == "Vertical":
        img_cv = cv2.flip(img_cv, 0)

    # Brightness & Contrast
    brightness = st.sidebar.slider("Brightness", 0.5, 3.0, 1.0)
    contrast = st.sidebar.slider("Contrast", 0.5, 3.0, 1.0)
    img_pil = cv_to_pil(img_cv)
    enhancer = ImageEnhance.Brightness(img_pil)
    img_pil = enhancer.enhance(brightness)
    enhancer = ImageEnhance.Contrast(img_pil)
    img_pil = enhancer.enhance(contrast)
    img_cv = pil_to_cv(img_pil)

    # Filters
    filter_type = st.sidebar.selectbox("Apply Filter", ["None", "Sepia", "Black & White", "Blur", "Sharpen"])
    img_cv = apply_filter(img_cv, filter_type)

    # Auto-enhance
    if st.sidebar.button("Auto Enhance"):
        img_cv = auto_enhance(img_cv)

    # Retouching Features
    if st.sidebar.button("Remove Blemishes"):
        img_cv = remove_blemishes(img_cv)

    if st.sidebar.button("Smooth Skin"):
        img_cv = smooth_skin(img_cv)

    # Add Text
    add_text = st.sidebar.checkbox("Add Text")
    if add_text:
        text = st.sidebar.text_input("Enter text", "Sample Text")
        font_scale = st.sidebar.slider("Font Size", 0.5, 5.0, 1.0)
        color = st.sidebar.color_picker("Pick Text Color", "#ffffff")
        b, g, r = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        img_cv = cv2.putText(img_cv, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (b, g, r), 2)

    # Display edited image
    st.image(cv_to_pil(img_cv), caption="Edited Image", use_container_width=True)

    # Convert edited image to bytes
    img_bytes = io.BytesIO()
    cv_to_pil(img_cv).save(img_bytes, format="PNG")

    # Download option
    st.sidebar.download_button("Download Image", data=img_bytes.getvalue(), file_name="edited_image.png", mime="image/png")
