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

def create_poster_html(place_type, area):
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Poster</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: white;
            }}
            .poster-container {{
                width: 600px;
                height: 800px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                padding: 20px;
                box-sizing: border-box;
            }}
            .title {{
                font-size: 48px;
                font-weight: bold;
                margin-bottom: 20px;
                color: #1F2937;
            }}
            .subtitle {{
                font-size: 24px;
                font-style: italic;
                color: #6B7280;
            }}
        </style>
    </head>
    <body>
        <div class="poster-container">
            <h1 class="title">{place_type} terbaik<br>di {area}</h1>
            <p class="subtitle">Menurut google reviews</p>
        </div>
    </body>
    </html>
    '''
    return html_template.format(place_type=place_type, area=area)

def create_poster_image(place_type, area):
    html_content = create_poster_html(place_type, area)
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 600, 'height': 800})
        page.set_content(html_content)
        
        # Wait for any animations or fonts to load
        page.wait_for_timeout(1000)
        
        # Capture the screenshot
        screenshot = page.screenshot()
        browser.close()
    
    # Convert the screenshot to a PIL Image
    image = Image.open(io.BytesIO(screenshot))
    
    return image

def html_to_image(html_content):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 600, 'height': 800})
        page.set_content(html_content)
        
        # Wait for any animations or lazy-loaded content to finish
        page.wait_for_timeout(1000)
        
        # Get the bounding box of the content
        bounding_box = page.evaluate('''() => {
            const body = document.body;
            const html = document.documentElement;
            const height = Math.max(
                body.scrollHeight, body.offsetHeight,
                html.clientHeight, html.scrollHeight, html.offsetHeight
            );
            return {
                width: document.documentElement.clientWidth,
                height: height
            };
        }''')
        
        # Calculate the aspect ratio
        aspect_ratio = 800 / 600
        content_ratio = bounding_box['height'] / bounding_box['width']
        
        if content_ratio > aspect_ratio:
            # Content is taller, adjust width
            new_width = math.ceil(bounding_box['height'] / aspect_ratio)
            page.set_viewport_size({'width': new_width, 'height': bounding_box['height']})
        else:
            # Content is wider, adjust height
            new_height = math.ceil(bounding_box['width'] * aspect_ratio)
            page.set_viewport_size({'width': bounding_box['width'], 'height': new_height})
        
        # Capture the screenshot
        screenshot = page.screenshot(full_page=True)
        browser.close()
        
        return screenshot, bounding_box['height']
        
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

            # Create and display poster image
            poster_image = create_poster_image(place_type, area)
            st.image(poster_image, caption="Poster", use_column_width=True)
            
            # Display HTML content
            st.components.v1.html(html_output, height=800, scrolling=True)
            st.markdown("### Top 10 Places")
            st.info("The image above shows the top 10 places. You can take a screenshot of this for sharing.")
            
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
                        st.success(f"Top 10 image generated successfully! Image size: 1200x1600 pixels")
                    else:
                        st.warning("Failed to generate the Top 10 image. You can still use the HTML version above.")
                except Exception as e:
                    st.error(f"An error occurred while generating the image: {str(e)}")
                    st.info("You can still use the HTML version above.")
        else:
            st.error("Please fill in all fields before generating the images.")

if __name__ == "__main__":
    main()
