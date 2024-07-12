import streamlit as st
import re
import io
import json
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright
import math
import zipfile
import json
import time
import requests
from instabot import Bot
import os
import tempfile

def upload_to_instagram(username, password, image_paths):
    with tempfile.TemporaryDirectory() as tmp_dir:
        bot = Bot()
        bot.login(username=username, password=password)
        
        for i, image_path in enumerate(image_paths):
            # Simpan gambar ke direktori sementara
            temp_image_path = os.path.join(tmp_dir, f"image_{i}.png")
            with open(temp_image_path, "wb") as f:
                f.write(requests.get(image_path).content)
            
            # Unggah gambar
            caption = f"Automatically uploaded image {i+1}"
            bot.upload_photo(temp_image_path, caption=caption)
        
        bot.logout()


def create_scatter_plot_html(places, title):
    if not places:
        return "<p>No data available for scatter plot</p>"
    # Calculate dynamic scales
    min_reviews = min(place['reviews'] for place in places)
    max_reviews = max(place['reviews'] for place in places)
    min_rating = min(place['rating'] for place in places)
    max_rating = max(place['rating'] for place in places)
    # Add some padding to the scales
    reviews_padding = (max_reviews - min_reviews) * 0.1
    rating_padding = (max_rating - min_rating) * 0.1
    x_min = max(0, min_reviews - reviews_padding)
    x_max = max_reviews + reviews_padding
    y_min = max(0, min_rating - rating_padding)
    y_max = min(5, max_rating + rating_padding)
    
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            body {{
                font-family: 'Inter', sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: white;
            }}
            #chart {{
                width: 800px;
                height: 600px;
            }}
        </style>
    </head>
    <body>
        <div id="chart"></div>
        <script>
            var data = [{data}];
            var layout = {{
                title: {{
                    text: '{title}',
                    font: {{ size: 24 }}
                }},
                xaxis: {{
                    title: 'Number of Reviews',
                    range: [{x_min}, {x_max}]
                }},
                yaxis: {{
                    title: 'Rating',
                    range: [{y_min}, {y_max}]
                }},
                hovermode: 'closest',
                showlegend: false,
                margin: {{ t: 50, r: 50, b: 50, l: 50 }}
            }};
            Plotly.newPlot('chart', data, layout, {{responsive: true}});
        </script>
    </body>
    </html>
    '''
    scatter_data = {
        'x': [place['reviews'] for place in places],
        'y': [place['rating'] for place in places],
        'mode': 'markers+text',
        'type': 'scatter',
        'text': [f"{place['name']}<br>{place['rating']} ★<br>{place['reviews']} reviews" for place in places],
        'textposition': 'top center',
        'marker': { 'size': 10 },
        'textfont': { 'size': 10 }
    }
    return html_template.format(
        title=title,
        data=json.dumps([scatter_data]),
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max
    )
    return html_template.format(
        title=title,
        data=json.dumps([scatter_data]),
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max
    )
def create_html(places, title, area, place_type, top_n):
    top_places = sorted(places, key=lambda x: x['reviews'], reverse=True)[:top_n]
    top_places = sorted(top_places, key=lambda x: x['rating'], reverse=True)
    
    # Find the place with the most reviews and highest rating
    most_reviews = max(top_places, key=lambda x: x['reviews'])['reviews']
    highest_rating = max(top_places, key=lambda x: x['rating'])['rating']
    
    # Remove spaces from area and place_type for the footer
    footer_area = area.replace(" ", "")
    footer_place_type = place_type.replace(" ", "")
    
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            body {{
                font-family: 'Inter', sans-serif;
                margin: 0;
                padding: 20px;
                box-sizing: border-box;
                background-color: #ffffff;
            }}
            .container {{
                width: 100%;
                max-width: 600px;
                margin: 0 auto;
                box-sizing: border-box;
            }}
            h1 {{
                text-align: center;
                color: #1F2937;
                margin-bottom: 20px;
                font-size: 24px;
            }}
            .place {{
                background-color: #F3F4F6;
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                display: flex;
                justify-content: space-between;
                position: relative;
            }}
            .place-info {{
                flex-grow: 1;
                padding-right: 10px;
            }}
            .place-name {{
                font-size: 16px;
                font-weight: bold;
                color: #1F2937;
                margin-bottom: 5px;
            }}
            .address {{
                color: #6B7280;
                font-size: 12px;
                margin-bottom: 5px;
            }}
            .rating-info {{
                text-align: right;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: flex-end;
            }}
            .rating {{
                font-size: 24px;
                font-weight: bold;
                color: #1F2937;
            }}
            .reviews {{
                color: #6B7280;
                font-size: 12px;
            }}
            .stars {{
                display: flex;
                align-items: center;
            }}
            .footer {{
                text-align: center;
                color: #6B7280;
                font-size: 10px;
                margin-top: 10px;
            }}
            .label {{
                position: absolute;
                top: -10px;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                color: white;
            }}
            .perfect, .highest-rating {{
                background-color: #10B981;
                left: 10px;
            }}
            .favorite {{
                background-color: #3B82F6;
                right: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{title}</h1>
            <div id="placesList"></div>
            <div class="footer">@{footer_area}{footer_place_type}Lovers • Data akurat per Juli 2024</div>
        </div>
        <script>
            const places = {places_json};
            const mostReviews = {most_reviews};
            const highestRating = {highest_rating};
            function createStarRating(rating, index) {{
                let stars = '';
                for (let i = 0; i < 5; i++) {{
                    const percentage = Math.max(0, Math.min(100, (rating - i) * 100));
                    stars += `
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <defs>
                                <linearGradient id="star-${{index}}-${{i}}">
                                    <stop offset="${{percentage}}%" stop-color="#F59E0B" />
                                    <stop offset="${{percentage}}%" stop-color="#E5E7EB" />
                                </linearGradient>
                            </defs>
                            <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
                                  fill="url(#star-${{index}}-${{i}})" stroke="#F59E0B" stroke-width="1" />
                        </svg>`;
                }}
                return stars;
            }}
            const placesList = document.getElementById('placesList');
            places.forEach((place, index) => {{
                const isPerfect = place.rating === 5;
                const isHighestRating = place.rating === highestRating && !isPerfect;
                const isMostFavorite = place.reviews === mostReviews;
                let labels = '';
                if (isPerfect) {{
                    labels += '<span class="label perfect">Perfect!</span>';
                }} else if (isHighestRating) {{
                    labels += '<span class="label highest-rating">Highest Rating!</span>';
                }}
                if (isMostFavorite) {{
                    labels += '<span class="label favorite">Most Favorite!</span>';
                }}
                placesList.innerHTML += `
                    <div class="place">
                        ${{labels}}
                        <div class="place-info">
                            <div class="place-name">${{index + 1}}. ${{place.name}}</div>
                            <div class="address"><i class="fas fa-map-marker-alt"></i> ${{place.address}}</div>
                        </div>
                        <div class="rating-info">
                            <div class="rating">${{place.rating.toFixed(1)}}</div>
                            <div class="stars">${{createStarRating(place.rating, index)}}</div>
                            <div class="reviews">dari ${{place.reviews}} reviews</div>
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
        places_json=json.dumps(top_places),
        most_reviews=most_reviews,
        highest_rating=highest_rating,
        footer_area=footer_area,
        footer_place_type=footer_place_type
    )

    
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
        reviews = int(float(match[2].replace('.', '').replace(',', '')))
        
        # Improved address extraction logic
        address = ""
        if match[3].strip():
            address_lines = match[3].strip().split('\n')
            if address_lines:
                first_line = address_lines[0]
                if '· $' in first_line or '· $$' in first_line or '· $$$' in first_line:
                    # Handle case with price indicators
                    if len(address_lines) > 1:
                        second_line = address_lines[1]
                        last_dot_index = second_line.rfind('· ')
                        if last_dot_index != -1 and last_dot_index + 2 < len(second_line):
                            address = second_line[last_dot_index + 2:].strip()
                        else:
                            address = second_line.strip()
                else:
                    # Handle case without price indicators
                    last_dot_index = first_line.rfind('· ')
                    if last_dot_index != -1 and last_dot_index + 2 < len(first_line):
                        address = first_line[last_dot_index + 2:].strip()
                    else:
                        address = first_line.strip()
        
        places.append({
            'name': name,
            'rating': rating,
            'reviews': reviews,
            'address': address
        })
    
    return places
    
def create_poster_html(place_type, area, top_n):
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Poster</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            body {{
                font-family: 'Inter', sans-serif;
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
            <h1 class="title">Top {top_n} {place_type} terbaik<br>di {area}</h1>
            <p class="subtitle">Menurut google reviews</p>
        </div>
    </body>
    </html>
    '''
    return html_template.format(place_type=place_type, area=area, top_n=top_n)

def create_poster_image(place_type, area, top_n):
    html_content = create_poster_html(place_type, area, top_n)
    
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
def html_to_image_top10(html_content):
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
def html_to_image(html_content):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 600, 'height': 800})
        page.set_content(html_content)
        
        # Wait for any animations or lazy-loaded content to finish
        page.wait_for_timeout(1000)
        
        # Capture the screenshot
        screenshot = page.screenshot(full_page=True)
        browser.close()
        
        return screenshot
def create_final_poster_html():
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Poster</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            body {{
                font-family: 'Inter', sans-serif;
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
            <h1 class="title"><br><br><br><br><br><br><br><br>Komen dibawah, spot apa lagi yang harus di-ranking?</h1>
            <p class="subtitle"></p>
        </div>
    </body>
    </html>
    '''
    return html_template
def create_final_poster_image():
    html_content = create_final_poster_html()
    
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
    
def main():
    install_chromium()
    st.title("Top Places Generator")
    st.header("Cara Kerja:")
    st.write("""1. Cari tempat yang ingin kamu extract top-nya di google maps. Buka google maps.
    \n2. Ketik nama Area-nya misal "Bandung", "Bintaro", dsb. Nama tempat harus yang berupa area, contoh tidak bisa "BSD" karena "BSD" bukan nama area resmi, bisanya "Serpong".
    \n3. Klik pada opsi menu "Di Sekitar" atau "Nearby" jika settinganmu bahasa Enggres.
    \n4. Ketik nama tempat yang ingin kamu extract. Kamu bisa juga filter dulu misal yg ratingnya > 4.5, atau yang harganya murah ($-nya satu), bebas lah.
    \n5. Copy semua hasilnya dengan block semua text dari tempat pertama sampai selesai, biarkan dia scroll down terus sampe habis.
    \n6. Paste di kolom Place Data dibawah.
    \n7. Tunggu hasilnya akan berupa image yang siap kamu download.
    """)
    area = st.text_input("Enter the area name (untuk judul posternya nanti):")
    place_type = st.text_input("Enter the type of place (untuk judul juga):")
    top_n = st.radio("Choose the number of top places:", ("5", "10"))
    top_n = int(top_n)
    text_input = st.text_area("Enter the place data (untuk diparsing dan dibuatkan poster):", height=300)

    username = st.text_input("Instagram Username (fill this if u want to upload to your instagram.)")
    password = st.text_input("Instagram Password (fill this if u want to upload to your instagram.)", type="password")
    if st.button("Generate Images"):
        if area and place_type and text_input:
            places = parse_text(text_input)
            
            # Log data yang diproses
            # st.write("Processed data:")
            # st.write(places)
            
            if not places:
                st.error("No valid data found. Please check your input.")
                return
            
            # Update this line to include top_n
            html_output = create_html(places, f"Top {top_n} {place_type} in {area}", area, place_type, top_n)
            
            # Create and display poster image
            poster_image = create_poster_image(place_type, area, top_n)
            st.image(poster_image, caption="Poster", use_column_width=True)
            
            # Display HTML content
            st.components.v1.html(html_output, height=800, scrolling=True)
            st.markdown(f"### Top {top_n} Places")
            st.info(f"The image above shows the top {top_n} places.")
            
            # Convert HTML to image
            with st.spinner(f"Generating Top {top_n} image..."):
                try:
                    html_image, html_height = html_to_image_top10(html_output)
                    
                    if html_image is not None:
                        st.success(f"Top {top_n} image generated successfully!")
                    else:
                        st.warning(f"Failed to generate the Top {top_n} image. You can still use the HTML version above.")
                except Exception as e:
                    st.error(f"An error occurred while generating the image: {str(e)}")
                    st.info("You can still use the HTML version above.")
            
            # Display the final poster
            final_poster_image = create_final_poster_image()
            st.image(final_poster_image, caption="Final Poster", use_column_width=True)
            
            # Create a zip file containing all images
            with io.BytesIO() as zip_buffer:
                with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
                    # Convert PIL Image to bytes
                    poster_bytes = io.BytesIO()
                    poster_image.save(poster_bytes, format='PNG')
                    poster_bytes = poster_bytes.getvalue()
        
                    zip_file.writestr("poster.png", poster_bytes)
                    zip_file.writestr(f"top_{top_n}.png", html_image)
                    
                    # Add the new final poster
                    final_poster_bytes = io.BytesIO()
                    final_poster_image.save(final_poster_bytes, format='PNG')
                    final_poster_bytes = final_poster_bytes.getvalue()
                    zip_file.writestr("final_poster.png", final_poster_bytes)
                
                zip_buffer.seek(0)
                st.download_button(
                    label="Download All Images",
                    data=zip_buffer.getvalue(),
                    file_name=f"top_{top_n}_{place_type}_{area}_images.zip",
                    mime="application/zip"
                )
            
            if username and password and text_input:
                st.header("Upload to Instagram")
                image_paths = ["poster.png", f"top_{top_n}.png", "final_poster.png"]
                try:
                    upload_to_instagram(username, password, image_paths)
                    st.success("Images uploaded to Instagram successfully!")
                except Exception as e:
                    st.error(f"Failed to upload images to Instagram. Error: {str(e)}")
                    
if __name__ == "__main__":
    main()
