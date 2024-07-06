import streamlit as st
import re
import json
import io
import base64

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
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            position: relative;
        }}
        h1 {{
            text-align: center;
            color: #1F2937;
            margin-bottom: 30px;
        }}
        .place {{
            border-bottom: 1px solid #E5E7EB;
            padding: 15px 0;
        }}
        .place:last-child {{
            border-bottom: none;
        }}
        .place-name {{
            font-size: 1.2em;
            font-weight: bold;
            color: #1F2937;
        }}
        .address {{
            color: #6B7280;
            font-size: 0.9em;
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
            font-size: 0.9em;
            margin-left: 10px;
        }}
        .footer {{
            text-align: center;
            color: #6B7280;
            font-size: 0.8em;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
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
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
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
                    <div class="address">📍 ${{place.address}}</div>
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

def create_preview_html(places, title):
    top_10 = sorted(places, key=lambda x: x['reviews'], reverse=True)[:10]
    top_10 = sorted(top_10, key=lambda x: x['rating'], reverse=True)
    
    html = f'''
    <h1 style="text-align: center; color: #1F2937;">{title}</h1>
    <div style="max-width: 600px; margin: 0 auto;">
    '''
    
    for i, place in enumerate(top_10, 1):
        stars_html = create_star_rating_svg(place['rating'], i)
        html += f'''
        <div style="border-bottom: 1px solid #E5E7EB; padding: 15px 0;">
            <h3 style="margin: 0; color: #1F2937;">{i}. {place['name']}</h3>
            <p style="color: #6B7280; font-size: 0.9em; margin: 5px 0;">📍 {place['address']}</p>
            <div style="display: flex; align-items: center;">
                <div style="display: flex; align-items: center;">
                    {stars_html}
                    <span style="margin-left: 5px;">{place['rating']:.1f}</span>
                </div>
                <span style="color: #6B7280; font-size: 0.9em; margin-left: 10px;">({place['reviews']} reviews)</span>
            </div>
        </div>
        '''
    
    html += '''
    </div>
    <p style="text-align: center; color: #6B7280; font-size: 0.8em; margin-top: 20px;">@TangerangSelatanSateLovers • Data akurat per Juli 2024</p>
    '''
    return html

def create_star_rating_svg(rating, index):
    stars = ''
    for i in range(5):
        percentage = max(0, min(100, (rating - i) * 100))
        stars += f'''
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
                <linearGradient id="star-{index}-{i}">
                    <stop offset="{percentage}%" stop-color="#F2C94C" />
                    <stop offset="{percentage}%" stop-color="#E0E0E0" />
                </linearGradient>
            </defs>
            <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
                  fill="url(#star-{index}-{i})" stroke="#F2C94C" stroke-width="1" />
        </svg>'''
    return stars

def main():
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

    if st.button("Generate HTML"):
        if area and place_type and text_input:
            places = parse_text(text_input)
            html_output = create_html(places, f"Top 10 {place_type} in {area}")
            preview_html = create_preview_html(places, f"Top 10 {place_type} in {area}")
            
            # Display preview
            st.markdown("### Preview")
            st.components.v1.html(preview_html, height=600)
            
            # Display HTML
            st.markdown("### Generated HTML")
            st.code(html_output, language='html')
            
            # Provide download link for HTML
            b64 = base64.b64encode(html_output.encode()).decode()
            href = f'<a href="data:text/html;base64,{b64}" download="top_10_{place_type}_{area}.html">Download HTML</a>'
            st.markdown(href, unsafe_allow_html=True)
        else:
            st.error("Please fill in all fields before generating the HTML.")

if __name__ == "__main__":
    main()
