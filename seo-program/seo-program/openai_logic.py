from openai import OpenAI
import re
import requests
import os
import sqlite3
import random
from bs4 import BeautifulSoup
from translations import translate_html_content

def count_words_without_html(text):
    """Count the number of words in a text excluding HTML elements."""
    clean_text = BeautifulSoup(text, "html.parser").get_text()
    words = re.findall(r'\b\w+\b', clean_text)
    return len(words), clean_text 

def generate_seo_metadata(topic, content_type, client, language="tr"):
    """Generate SEO metadata using OpenAI."""
    try:
        seo_prompt = f"""Could you please write me a Focus Keyword, SEO Title, Meta Description and URL Slug in this format for {content_type}:
        1. Focus Keyword:
        2. SEO Title:
        3. Meta Description:
        4. URL Slug:
        Specifications:
        1. Focus Keyword - should be the main idea of the topic, max length 4 words and 30-40 characters strictly, not a char more, can start with the first 4 words from 
        the topic. Separated by the comma add 2 more focus kws that appear in the text often. 
        2. SEO Title - max length 55 characters, starts with focus keyword, have 1 number inside (can be current year 2025).
        3. Meta Description - max length 155 characters, starts with focus keyword.
        4. URL Slug - max length strictly 30-40 characters and not a character more, a full 100% match with main 1st focus keyword. Please make sure that there is no difference between url slug and 
        focus kw, except for the handling encode.
        The format of the output should be as provided and generated content should be in {language} language. Even tho the output should be in the
        {language} language, please make the url slug in the ascii table characters not to have errors. 
        Please dont add any additional messages, just give the output right away. Thank you. 
        The Topic: {topic}"""

        seo_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a SEO Specialist and a copywriter."},
                {"role": "user", "content": seo_prompt}
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

def generate_article(topic, seo_metadata, client, account_id=None, content_type='article', language="tr"):
    """Generate an article using OpenAI."""
    try:
        if content_type == "product_description":
            article_prompt = f"""Could you please write me a product description for 2000 words length. Product description text has to be formatted in HTML 
            (only text, no need for <!DOCTYPE html> or anything, imagine it as the body), should have headings too consisting with Focus Keyword, 
            include heading h1, h2, h3 and h4. Focus Keyword has to appear at least 50 times in the product description text. Preferably every 3rd or 4th sentence 
            should contain focus keyword. Only give me the product description, no need for any additional messages. Also add why customers will want
            and should by this product from us, write tha it is what they really need and we can sell it or something like this please. 
            The Topic for the product description: {topic}
            Additional SEO information for the product description:
            {seo_metadata}
            The output text should be in {language} language. 
            """
        else:
            article_prompt = f"""Could you please write me an article for 2000 words length. article text has to be formatted in HTML 
            (only text, no need for <!DOCTYPE html> or anything, imagine it as the body), should have headings too consisting with Focus Keyword, 
            include heading h1, h2, h3 and h4. Focus Keyword has to appear at least 50 times in the article text. Preferably every 3rd or 4th sentence 
            should contain focus keyword. Only give me the article, no need for any additional messages.
            The Topic for the article: {topic}
            Additional SEO information for the article:
            {seo_metadata}
            The output text should be in {language} language. 
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

        # Count words in the generated article
        generated_word_count, cleaned_html_content_text = count_words_without_html(cleaned_html_content)
        total_word_count = generated_word_count  # Initialize total word count
        additional_content = "<hr>"
        additional_fk = ""
        deficit = 2750 - total_word_count  # Words needed to reach 2500

        if account_id:
            # Fetch account details
            conn = sqlite3.connect("accounts.db")
            cursor = conn.cursor()
            cursor.execute("SELECT add_data_available, add_data_folder FROM accounts WHERE id = ?", (account_id,))
            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                add_data_folder = result[1]

                # Add words from company.html
                html_file_path = os.path.join(add_data_folder, "company.html")
                if os.path.exists(html_file_path) and deficit > 0:
                    try:
                        with open(html_file_path, "r", encoding="utf-8") as html_file:
                            html_content = html_file.read()
                            html_word_count, html_clean_text = count_words_without_html(html_content)

                            total_word_count += html_word_count
                            additional_content += html_content
                            deficit -= html_word_count
                    except Exception as e:
                        print(f"Error reading HTML file: {e}")

                if content_type == "product_description":
                    # Add words from summaries.db
                    summaries_db_path = os.path.join(add_data_folder, "product_summaries.db")
                    if os.path.exists(summaries_db_path) and deficit > 0:
                        try:
                            conn = sqlite3.connect(summaries_db_path)
                            cursor = conn.cursor()
                            cursor.execute("SELECT summary FROM product_summaries")
                            summaries = cursor.fetchall()
                            conn.close()

                            if summaries:
                                random.shuffle(summaries)  # Shuffle summaries for randomness
                                summary_index = 0  # Keep track of the current index in the summaries list

                                # Keep adding summaries, allowing reuse if necessary
                                while deficit > 0:
                                    summary_text = summaries[summary_index][0]
                                    summary_word_count, summary_clean_text = count_words_without_html(summary_text)

                                    # Translate summary text if necessary
                                    # if language != "en":  # Assuming English is the default language
                                    summary_text = translate_html_content(summary_text, language)

                                    # Add the entire summary if it fits within the deficit
                                    total_word_count += summary_word_count
                                    additional_content += f"<hr>{summary_text}<hr>"
                                    deficit -= summary_word_count

                                    # Move to the next summary, loop back to the beginning if necessary
                                    summary_index = (summary_index + 1) % len(summaries)
                            else:
                                print("No summaries found in the database.")
                        except Exception as e:
                            print(f"Error retrieving summaries: {e}")
                else:
                    # Add words from summaries.db
                    summaries_db_path = os.path.join(add_data_folder, "article_summaries.db")
                    if os.path.exists(summaries_db_path) and deficit > 0:
                        try:
                            conn = sqlite3.connect(summaries_db_path)
                            cursor = conn.cursor()
                            cursor.execute("SELECT summary FROM article_summaries")
                            summaries = cursor.fetchall()
                            conn.close()

                            if summaries:
                                random.shuffle(summaries)  # Shuffle summaries for randomness
                                summary_index = 0  # Keep track of the current index in the summaries list

                                # Keep adding summaries, allowing reuse if necessary
                                while deficit > 0:
                                    summary_text = summaries[summary_index][0]
                                    summary_word_count, summary_clean_text = count_words_without_html(summary_text)

                                    # Translate summary text if necessary
                                    # if language != "en":  # Assuming English is the default language
                                    summary_text = translate_html_content(summary_text, language)

                                    # Add the entire summary if it fits within the deficit
                                    total_word_count += summary_word_count
                                    additional_content += f"<hr>{summary_text}<hr>"
                                    deficit -= summary_word_count

                                    # Move to the next summary, loop back to the beginning if necessary
                                    summary_index = (summary_index + 1) % len(summaries)
                            else:
                                print("No summaries found in the database.")
                        except Exception as e:
                            print(f"Error retrieving summaries: {e}")

                # Add focus keywords from company.txt
                txt_file_path = os.path.join(add_data_folder, "company.txt")
                if os.path.exists(txt_file_path):
                    try:
                        with open(txt_file_path, "r", encoding="utf-8") as txt_file:
                            txt_txt = translate_html_content(txt_file.read().strip(), language)
                            additional_fk += txt_txt
                    except Exception as e:
                        print(f"Error reading TXT file: {e}")

        tags_prompt = f"""Could you please write me at least 15 tags for this text: {cleaned_html_content}
                    The Topic: {topic}
                    Additional SEO information for the text:
                    {seo_metadata}
                    The output text should be in {language} language.
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

        return {
            "article": cleaned_html_content,
            "additional_content": additional_content,
            "additional_fk": additional_fk,
            "tags": tags_list,
        }
    except Exception as e:
        print(f"Error generating article: {e}")
        raise

def generate_image_prompts_and_images(topic, seo_metadata, content_type, client, language="tr"):
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
        The Topic for the {content_type}: {topic}
        Additional SEO information for the images:
        {seo_metadata}
        The format of the output should be as provided. But the content of the output should be in {language} language please.
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
