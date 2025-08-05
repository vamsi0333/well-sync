from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

def create_gradient_background(width, height, color1, color2):
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        r = int(color1[0] + (color2[0] - color1[0]) * y / height)
        g = int(color1[1] + (color2[1] - color1[1]) * y / height)
        b = int(color1[2] + (color2[2] - color1[2]) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return image

def add_overlay_pattern(image):
    pattern = Image.new('RGBA', image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(pattern)
    
    for _ in range(100):
        x = random.randint(0, image.width)
        y = random.randint(0, image.height)
        size = random.randint(5, 20)
        opacity = random.randint(10, 30)
        draw.ellipse([x, y, x+size, y+size], fill=(255, 255, 255, opacity))
    
    return Image.alpha_composite(image.convert('RGBA'), pattern)

def create_professional_image(filename, title, color1, color2):
    width, height = 800, 600
    
    # Create base image with gradient
    image = create_gradient_background(width, height, color1, color2)
    
    # Add some abstract patterns
    pattern_layer = add_overlay_pattern(image)
    
    # Apply subtle blur
    pattern_layer = pattern_layer.filter(ImageFilter.GaussianBlur(1))
    
    # Save the image
    pattern_layer.convert('RGB').save(f'static/images/{filename}.jpg', quality=95)

# Generate images for each card
create_professional_image('benefits', 'Benefits', (41, 128, 185), (52, 152, 219))  # Blue theme
create_professional_image('culture', 'Culture', (46, 204, 113), (39, 174, 96))     # Green theme
create_professional_image('diversity', 'Diversity', (155, 89, 182), (142, 68, 173))  # Purple theme
create_professional_image('flexible-work', 'Flexible Work', (230, 126, 34), (211, 84, 0))  # Orange theme

print("Images generated successfully!")
