#!/usr/bin/env python3
"""Create app icon for InputSourceToggle"""

from PIL import Image, ImageDraw, ImageFont
import os
import subprocess

def create_icon():
    # Create a 1024x1024 image with transparent background
    size = 1024
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a rounded rectangle background with gradient-like effect
    padding = 80
    corner_radius = 200

    # Background - nice blue gradient effect (simulated with solid color)
    bg_color = (59, 130, 246)  # Nice blue

    # Draw rounded rectangle
    draw.rounded_rectangle(
        [padding, padding, size - padding, size - padding],
        radius=corner_radius,
        fill=bg_color
    )

    # Add a subtle inner shadow/highlight
    highlight_color = (96, 165, 250)  # Lighter blue
    draw.rounded_rectangle(
        [padding + 10, padding + 10, size - padding - 10, size - padding - 40],
        radius=corner_radius - 10,
        fill=None,
        outline=highlight_color,
        width=8
    )

    # Draw globe circle
    center = size // 2
    globe_radius = 280
    globe_color = (255, 255, 255)  # White

    # Globe outline
    draw.ellipse(
        [center - globe_radius, center - globe_radius - 30,
         center + globe_radius, center + globe_radius - 30],
        fill=None,
        outline=globe_color,
        width=25
    )

    # Globe horizontal lines (latitude)
    for offset in [-140, 0, 140]:
        y = center + offset - 30
        # Calculate width at this latitude
        if offset == 0:
            width = globe_radius
        else:
            width = int(globe_radius * 0.7)
        draw.arc(
            [center - width, y - 40, center + width, y + 40],
            start=0, end=180,
            fill=globe_color,
            width=12
        )

    # Globe vertical line (meridian)
    draw.ellipse(
        [center - 100, center - globe_radius - 30,
         center + 100, center + globe_radius - 30],
        fill=None,
        outline=globe_color,
        width=12
    )

    # Add "EN" and Hebrew letter on either side
    try:
        # Try to use a nice font
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 160)
        font_hebrew = ImageFont.truetype("/System/Library/Fonts/Arial Hebrew.ttc", 180)
    except:
        font_large = ImageFont.load_default()
        font_hebrew = font_large

    # Draw "A" on left side
    draw.text((padding + 100, size - padding - 280), "A",
              fill=(255, 255, 255, 200), font=font_large)

    # Draw Hebrew letter "א" (Aleph) on right side
    draw.text((size - padding - 220, size - padding - 300), "א",
              fill=(255, 255, 255, 200), font=font_hebrew)

    # Add swap arrows at bottom
    arrow_y = size - padding - 120
    arrow_color = (255, 255, 255, 230)

    # Left arrow
    draw.polygon([
        (center - 80, arrow_y),
        (center - 40, arrow_y - 30),
        (center - 40, arrow_y + 30)
    ], fill=arrow_color)

    # Right arrow
    draw.polygon([
        (center + 80, arrow_y),
        (center + 40, arrow_y - 30),
        (center + 40, arrow_y + 30)
    ], fill=arrow_color)

    # Save as PNG
    icon_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(icon_dir, "AppIcon.png")
    img.save(png_path, "PNG")
    print(f"Created {png_path}")

    # Create iconset directory
    iconset_dir = os.path.join(icon_dir, "AppIcon.iconset")
    os.makedirs(iconset_dir, exist_ok=True)

    # Generate all required sizes for .icns
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    for s in sizes:
        resized = img.resize((s, s), Image.Resampling.LANCZOS)
        resized.save(os.path.join(iconset_dir, f"icon_{s}x{s}.png"))
        if s <= 512:
            # Also save @2x versions
            resized_2x = img.resize((s * 2, s * 2), Image.Resampling.LANCZOS)
            resized_2x.save(os.path.join(iconset_dir, f"icon_{s}x{s}@2x.png"))

    # Convert to .icns using iconutil
    icns_path = os.path.join(icon_dir, "AppIcon.icns")
    subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", icns_path], check=True)
    print(f"Created {icns_path}")

    # Clean up iconset
    import shutil
    shutil.rmtree(iconset_dir)

    return icns_path

if __name__ == "__main__":
    create_icon()
