import streamlit as st
import re
import io
import json
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
import math

def install_chromium():
    try:
        result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                                capture_output=True, text=True, check=True)
        st.write(result.stdout)
    except subprocess.CalledProcessError as e:
        st.error("Failed to install Chromium.")
        st.error(e.stderr)
        raise

def parse_text(text):
    places = []
    pattern = r'(.*?)\n(\d+[,\.]\d+)\((\d+(?:\.\d+)?)\)(.*?)(?=\n\n|\Z)'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for match in matches:
        lines = match[0].strip().split('\n')
        name = lines[-1] if lines else ""
        rating = float(match[1].replace(',', '.'))
        reviews = int(float(match[2].replace('.', '')))
        
        address_match = re.search(r'(Jl\.?|Jalan|[Rr]uko).*', match[3])
        address = address_match.group(0) if address_match else ""
        
        places.append({
            'name': name,
            'rating': rating,
            'reviews': reviews,
            'address': address
        })
    
    return places

def create_html(places, title):
    top_10 = sorted(places, key=lambda x: x['reviews'], reverse=True)[:10]
    top_10 = sorted(top_10, key=lambda x: x['rating'], reverse=True)

    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                background-color: #ffffff;
            }}
            .container {{
                width: 100%;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                box-sizing: border-box;
                border: 1px solid #E5E7EB;
                background-color: #ffffff;
            }}
            h1 {{
                text-align: center;
                color: #1F2937;
                margin-bottom: 20px;
                font-size: 24px;
            }}
            .place {{
                border-bottom: 1px solid #E5E7EB;
                padding: 10px 0;
            }}
            .place:last-child {{
                border-bottom: none;
            }}
            .place-name {{
                font-size: 16px;
                font-weight: bold;
                color: #1F2937;
            }}
            .address {{
                color: #6B7280;
                font-size: 12px;
                margin: 5px 0;
            }}
            .rating {{
                display: flex;
                align-items: center;
            }}
            .stars {{
                display: flex;
                align-items: center;
            }}
            .reviews {{
                color: #6B7280;
                font-size: 12px;
                margin-left: 10px;
            }}
            .footer {{
                text-align: center;
                color: #6B7280;
                font-size: 10px;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container poster-container">
            <h1>{title}</h1>
            <div id="placesList"></div>
            <div class="footer">@TangerangSelatanSateLovers • Data akurat per Juli 2024</div>
        </div>

        <script>
            const places = {places_json};

            function createStarRating(rating, index) {{
                let stars = '';
                for (let i = 0; i < 5; i++) {{
                    const percentage = Math.max(0, Math.min(100, (rating - i) * 100));
                    stars += `
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <defs>
                                <linearGradient id="star-${{index}}-${{i}}">
                                    <stop offset="${{percentage}}%" stop-color="#F2C94C" />
                                    <stop offset="${{percentage}}%" stop-color="#E0E0E0" />
                                </linearGradient>
                            </defs>
                            <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
                                  fill="url(#star-${{index}}-${{i}})" stroke="#F2C94C" stroke-width="1" />
                        </svg>`;
                }}
                return stars;
            }}

            const placesList = document.getElementById('placesList');
            places.forEach((place, index) => {{
                placesList.innerHTML += `
                    <div class="place">
                        <div class="place-name">${{index + 1}}. ${{place.name}}</div>
                        <div class="address"><i class="fas fa-map-marker-alt"></i> ${{place.address}}</div>
                        <div class="rating">
                            <div class="stars">
                                ${{createStarRating(place.rating, index)}}
                                <span style="margin-left: 5px;">${{place.rating.toFixed(1)}}</span>
                            </div>
                            <span class="reviews">(${{place.reviews}} reviews)</span>
                        </div>
                    </div>
                `;
            }});
        </script>
    </body>
    </html>
    '''

    return html_template.format(
        title=title,
        places_json=json.dumps(top_10)
    )

def create_poster_image(place_type, area):
    width, height = 600, 800
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Italic.ttf", 18)
    except IOError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    title = f"{place_type} terbaik di {area}"
    subtitle = "Menurut google reviews"

    # Calculate text positions using textbbox
    title_bbox = draw.textbbox((0, 0), title, font=font_large)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]

    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=font_small)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]

    title_position = ((width - title_width) // 2, (height - title_height - subtitle_height) // 2)
    subtitle_position = ((width - subtitle_width) // 2, title_position[1] + title_height + 20)

    # Draw text
    draw.text(title_position, title, font=font_large, fill='black')
    draw.text(subtitle_position, subtitle, font=font_small, fill='black')

    return image

def html_to_image(html_content):
    target_width = 600
    min_height = 800  # Minimum height, can be increased if needed

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html_content)
            
            # Set initial viewport size
            page.set_viewport_size({"width": target_width, "height": min_height})
            
            # Evaluate content height
            content_height = page.evaluate("""() => {
                const posterContainer = document.querySelector('.poster-container');
                return posterContainer ? posterContainer.getBoundingClientRect().height : 0;
            }""")
            
            if content_height == 0:
                raise ValueError("Could not determine content height")

            # Adjust the height to fit all content, rounding up to the nearest 10 pixels
            adjusted_height = max(min_height, math.ceil(content_height / 10) * 10)

            # Set the container style to ensure all content is visible and centered
            page.evaluate(f"""() => {{
                const container = document.querySelector('.poster-container');
                if (container) {{
                    container.style.width = '{target_width}px';
                    container.style.minHeight = '{adjusted_height}px';
                    container.style.backgroundColor = 'white';
                    container.style.display = 'flex';
                    container.style.flexDirection = 'column';
                    container.style.alignItems = 'center';
                    container.style.justifyContent = 'flex-start';
                    container.style.padding = '20px';
                    container.style.boxSizing = 'border-box';
                }}
            }}""")
            
            # Adjust viewport to match the content
            page.set_viewport_size({"width": target_width, "height": adjusted_height})

            # Take the screenshot of the specific element
            screenshot_bytes = page.locator('.poster-container').screenshot()
            browser.close()
            
            return screenshot_bytes, adjusted_height
    except Exception as e:
        st.error(f"An error occurred while generating the image: {str(e)}")
        return None, None
        
def main():
    install_chromium()

    st.title("Top 10 Places Generator")

    st.header("Cara Kerja:")
    st.write("""1. Cari tempat yang ingin kamu extract top 10-nya di google maps. Buka google maps.
    2. Ketik nama Area-nya misal "Bandung", "Bintaro", dsb. Nama tempat harus yang berupa area, contoh tidak bisa "BSD" karena "BSD" bukan nama area resmi, bisanya "Serpong".
    3. Klik pada opsi menu "Di Sekitar" atau "Nearby" jika settinganmu bahasa Enggres.
    4. Ketik nama tempat yang ingin kamu extract. Kamu bisa juga filter dulu misal yg ratingnya > 4.5, atau yang harganya murah ($-nya satu), bebas lah.
    5. Copy semua hasilnya dengan block semua text dari tempat pertama sampai selesai, biarkan dia scroll down terus sampe habis.
    6. Paste di kolom Place Data dibawah.
    7. Tunggu hasilnya akan berupa image yang siap kamu download.
    """)

    area = st.text_input("Enter the area name (untuk judul posternya nanti):")
    place_type = st.text_input("Enter the type of place (untuk judul juga):")
    text_input = st.text_area("Enter the place data (untuk diparsing dan dibuatkan poster):", height=300)

    if st.button("Generate Images"):
        if area and place_type and text_input:
            places = parse_text(text_input)
            html_output = create_html(places, f"Top 10 {place_type} in {area}")

            # Display HTML content
            st.components.v1.html(html_output, height=800, scrolling=True)
            st.markdown("### Top 10 Places")
            st.info("The image above shows the top 10 places. You can take a screenshot of this for sharing.")
            
            # Create and display poster image
            poster_image = create_poster_image(place_type, area)
            st.image(poster_image, caption="Poster", use_column_width=True)

            # Provide download link for poster image
            buffered_poster = io.BytesIO()
            poster_image.save(buffered_poster, format="PNG")
            poster_image_bytes = buffered_poster.getvalue()

            st.download_button(
                label="Download Poster Image",
                data=poster_image_bytes,
                file_name=f"poster_{place_type}_{area}.png",
                mime="image/png"
            )

            # Convert HTML to image and provide download link
            with st.spinner("Generating Top 10 image..."):
                try:
                    html_image, image_height = html_to_image(html_output)
                    
                    if html_image is not None and image_height is not None:
                        st.download_button(
                            label="Download Top 10 as Image",
                            data=html_image,
                            file_name=f"top_10_{place_type}_{area}.png",
                            mime="image/png"
                        )
                        st.success(f"Top 10 image generated successfully! Image size: 600x{image_height} pixels")
                    else:
                        st.warning("Failed to generate the Top 10 image. You can still use the HTML version above.")
                except Exception as e:
                    st.error(f"An error occurred while generating the image: {str(e)}")
                    st.info("You can still use the HTML version above.")
        else:
            st.error("Please fill in all fields before generating the images.")

if __name__ == "__main__":
    main()
