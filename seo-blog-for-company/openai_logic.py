import re
import requests
from bs4 import BeautifulSoup

def count_words_without_html(text):
    """Count the number of words in a text excluding HTML elements."""
    clean_text = BeautifulSoup(text, "html.parser").get_text()
    words = re.findall(r'\b\w+\b', clean_text)
    return len(words), clean_text 

def generate_seo_metadata(seometa_data, client):
    """Generate SEO metadata using OpenAI."""
    try:
        current_year = seometa_data['year']
        seourl_slug = seometa_data['url_slug']
        topic = seometa_data['topic']
        content = seometa_data['content']
        location = seometa_data['location']

        meta_prompt = f"""Could you please write me a Focus Keyword, SEO Title, Meta Description and URL Slug in this format 
                for an article:
                1. Focus Keyword:
                2. SEO Title:
                3. Meta Description:
                4. URL Slug:
                Specifications:
                1. Focus Keyword - should be the main idea of the topic, max length 4 words and 30-40 characters strictly, not a char more, can start with the first 4 words from 
                the topic. The main first focus kw should be 100% url slug: {seourl_slug}. Separated by the comma add 4 more focus kws that will appear in the text often. 
                2. SEO Title - max length 55 characters, starts with focus keyword, have 1 number inside (can be current year {current_year}).
                3. Meta Description - max length 155 characters, starts with focus keyword.
                4. URL Slug - old url slug: {seourl_slug}. Dont need to be improved but make sure that main focus kw has the same kws as in the url slug. 
                The format of the output should be as provided. Please dont add any additional messages, just give the output right away. Thank you. 
                The Topic: {topic}
                The services: {content}
                Location: {location}
                Please make output text in turkish language, only the content in turkish, the format as given in english.
                """
        seo_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a SEO Specialist and a copywriter."},
                {"role": "user", "content": meta_prompt}
            ]
        )
        
        metadata_text = seo_completion.choices[0].message.content
        
        # Step 1: Remove all '*' characters (if there are any in the text)
        cleaned_text = metadata_text.replace('*', '')
        
        # Clean and process the metadata text
        meta_data = {}
        for line in cleaned_text.strip().split('\n'):
            match = re.match(r'\d+\.\s*(.+?):\s*(.+)', line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                meta_data[key] = value

        if "URL Slug" in meta_data:
            url_slug = meta_data["URL Slug"]
            if len(url_slug) > 45:
                meta_data["URL Slug"] = url_slug[:45]  
        return meta_data
    except Exception as e:
        print(f"Error generating SEO metadata: {e}")
        raise

def generate_html_info(links, additional_info, client):
    """Generate an article using OpenAI."""

    prompt = f"""Could you please write me a text promoting this website {links}. The length of the text should be minimum 2000 words.
                The text has to be formatted in HTML format (starting directly from the body part, no need for <!DOCTYPE html> or anything), 
                should have headings h2, h3 and h4. The text has to promote the company. Only give me the text right away, no need for any 
                additional messages. Make the text engaging, so that potential customers would want to use our services. For additional 
                information use this info: {additional_info}. 
                Also add 1 or 2 links on outsource websites like Wikipedia related to the company. 
                Please make sure that output is in HTML format and has all necessary headings (h2-h4) and tags and divs and so on. 
                No need for additional messages.
                And make the text in turkish language please."""

    try:
        article_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a SEO Specialist and a copywriter."},
                {"role": "user", "content": prompt}
            ]
        )

        article_text = article_completion.choices[0].message.content
        cleaned_html_content = article_text.replace("```html", "").replace("```", "").strip()

        return cleaned_html_content
    except Exception as e:
        print(f"Error generating html content: {e}")
        raise

def generate_article_summary(link, client):
    """Generate an article using OpenAI."""

    prompt = f"""Could you please write me a summary on this article {link}. The length of the summary should be minimum 700 characters.
                The text has to be formatted in HTML format (starting directly from the body part, no need for <!DOCTYPE html> or anything), 
                should have headings h2, h3 and h4. The text has to promote the company. Only give me the text right away, no need for any 
                additional messages. Make the summary engaging, so that potential customers would want to read it all.
                At the end of the summary add text Read more... with the link {link}, make text in turkish and link HTML formatted with <a> tag.
                Please make sure that output is in HTML format and has all necessarytags and divs and so on. 
                No need for additional messages.
                And make the text in turkish language please."""

    try:
        article_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a SEO Specialist and a copywriter."},
                {"role": "user", "content": prompt}
            ]
        )

        article_text = article_completion.choices[0].message.content
        cleaned_html_content = article_text.replace("```html", "").replace("```", "").strip()

        return cleaned_html_content
    except Exception as e:
        print(f"Error generating html content: {e}")
        raise

def generate_article(article_data, client):
    """Generate an article using OpenAI."""
    try:
        topic = article_data["topic"]
        content = article_data["content"]
        location = article_data["location"]
        seo_metadata = article_data["seo_metadata"]

        article_prompt = f"""Could you please write me a product description for 2000 words length. Product description text has to be formatted in HTML 
                    (only text, no need for <!DOCTYPE html> or anything, imagine it as the body), should have headings too consisting with Focus Keyword, 
                    include heading h1, h2, h3 and h4. Focus Keyword has to appear at least 30 times in the product description text. Preferably every 4th or 5th sentence 
                    should contain focus keyword. Only give me the product description, no need for any additional messages. Also add why customers will want
                    and should by this product from us, write as if it is what they really need and we can sell it or something like this please. 
                    The Topic for the article: {topic}
                    The Services they do: {content}
                    Location of the place: {location}
                    Inlcude this info as we are promoting thei business and dont forget to mention the place.
                    Additional SEO information for the product description:
                    {seo_metadata}
                    Please make sure that output is in HTML format and has all necessary headings (h2-h4) and tags and divs and so on. No need for additional messages.
                    Also make the output text in turkish please.  
                    """
        article_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a SEO Specialist and a copywriter."},
                {"role": "user", "content": article_prompt}
            ]
        )

        article_text = article_completion.choices[0].message.content
        cleaned_html_content = article_text.replace("```html", "").replace("```", "").strip()

        return cleaned_html_content
    except Exception as e:
        print(f"Error generating article: {e}")
        raise

def generate_tags(tags_data, client):
    try:
        topic = tags_data["topic"]
        content = tags_data["content"]
        location = tags_data["location"]
        seo_metadata = tags_data["seo_metadata"]
        article_data = tags_data["article_data"]

        tags_prompt = f"""Could you please write me at least 10 tags for this text: {article_data}
                    The Topic: {topic}
                    The Services they do: {content}
                    Location of the place: {location}
                    Additional SEO information for the text:
                    {seo_metadata}
                    The format of the output should be without any additional text, phrases or whatsoever, just a comma separated list of the
                    tags for this article."""
        tags_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a SEO Specialist and a copywriter."},
                {"role": "user", "content": tags_prompt}
            ]
        )

        tags_text = tags_completion.choices[0].message.content
        tags_list = [tag.strip() for tag in tags_text.split(",")]

        return tags_list
    except Exception as e:
        print(f"Error generating tags: {e}")
        raise

def generate_image_prompts_and_images(topic, seo_metadata, article, client):
    """Generate image prompts, metadata, and images using OpenAI."""
    try:
        image_prompt = f"""Could you please write me prompts for 2 images with full meta data for them. Metadata, especially the alt text for the 
        first image has to be the focus keyword. The output has to look like this:
        ### First Image Prompt:
        Prompt:
        Metadata:
        Title:
        Alt Text:
        Description:
        Focus Keyword:

        -----
        
        ### Second Image Prompt:
        Prompt:
        Metadata:
        Title: 
        Alt Text:
        Description:
        Focus Keyword:
        The Topic for the article: {topic}
        Additional SEO information for the images:
        {seo_metadata}
        The article: {article}
        The format of the output should be as provided. 
        Please dont add any additional messages, just the output right away. Thank you. """

        image_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a SEO Specialist and a copywriter."},
                {"role": "user", "content": image_prompt}
            ]
        )

        image_text = image_completion.choices[0].message.content
        
        # Remove asterisks (*) and split the text into two sections
        cleaned_data = image_text.replace("*", "").strip()
        sections = cleaned_data.split("-----")

        # Function to process each section and extract the information into a dictionary
        def process_section(section):
            lines = section.strip().split("\n")
            data = {}
            for line in lines:
                if line.startswith("### "):
                    # Image identifier (e.g., First Image Prompt or Second Image Prompt)
                    data["prompt"] = line[4:].strip()
                elif "Prompt:" in line:
                    data["prompt"] = line.split("Prompt:", 1)[1].strip()
                elif "Title:" in line:
                    data["title"] = line.split("Title:", 1)[1].strip()
                elif "Alt Text:" in line:
                    data["alt_text"] = line.split("Alt Text:", 1)[1].strip()
                elif "Description:" in line:
                    data["description"] = line.split("Description:", 1)[1].strip()
                elif "Focus Keyword:" in line:
                    data["focus_keyword"] = line.split("Focus Keyword:", 1)[1].strip()
            return data

        # Process each section and create a list of dictionaries
        images = [process_section(section) for section in sections]

        
        # Generate images using OpenAI's DALL-E API
        for i, image in enumerate(images):
            response = client.images.generate(
                model="dall-e-3",
                prompt=image["prompt"],
                size="1024x1024",
                quality="standard",
                n=1,
            )

            image_url = response.data[0].url

            # Download and save the image locally
            image_name = f"{seo_metadata['URL Slug']}_image_{i + 1}.png"
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                with open(image_name, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                image["local_path"] = image_name
                print(f"Image saved as '{image_name}'.")
            else:
                print(f"Failed to download the image: {response.status_code}, {response.text}")
        return images
    
    except Exception as e:
        print(f"Error generating image prompts and metadata: {e}")
        raise
