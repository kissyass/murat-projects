# Automated WordPress Content Creator

This project is an automated content creator designed to generate and post SEO-optimized articles and product descriptions to a WordPress site. It leverages OpenAI's language models to create rich content—including SEO metadata, images via DALL-E, and formatted HTML—and integrates with the Rank Math SEO plugin for enhanced on-site optimization. The application features a user-friendly Tkinter-based GUI and supports multiple languages (English and Turkish).

---

## Table of Contents

- [Features](#features)
- [Configuration](#configuration)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

---

## Features

- **Content Generation:**  
  - Generate articles and product descriptions in HTML format.
  - Auto-generate SEO metadata including focus keyword, SEO title, meta description, and URL slug.
  - Use user input for the article title while generating a separate meta title.

- **Image Generation:**  
  - Create image prompts with full metadata.
  - Integrate with DALL-E for image generation and upload them to WordPress.

- **Bulk Article Generation:**  
  - Upload or paste a list of topics for scheduled bulk posting.
  - Schedule posts with random delays within a configurable time range.

- **Account Management:**  
  - Securely store and retrieve WordPress account credentials and OpenAI API keys.
  - Encrypt sensitive data using Fernet encryption.

- **Translation Support:**  
  - Interface and generated content support multiple languages (currently English and Turkish) using GoogleTranslator.

- **Rank Math SEO Integration:**  
  - Automatically update meta fields for posts, products, and tags to include Rank Math SEO data.
  - Register and update custom meta fields via the WordPress REST API.

- **User-Friendly GUI:**  
  - Built with Tkinter for easy navigation between account creation, content generation, and bulk posting.

---

## Configuration

- **WordPress Credentials:**  
  Input your WordPress site URL, username, and API password (application password) through the GUI when adding a new account.

- **OpenAI API Key:**  
  Enter your OpenAI API key when setting up a new account. Ensure that your API key is valid and has the required permissions.

- **Additional Data Folder:**  
  If you have extra content or company data (e.g., `company.html` and `company.txt`), you can upload or change the additional data folder via the UI.

- **Rank Math SEO Meta Fields:**  
  Ensure your WordPress site has the Rank Math SEO plugin installed and that the custom meta fields (e.g., `rank_math_title`, `rank_math_description`, etc.) are registered. See the provided PHP snippet in the project for registering these fields via the REST API.

---

## Usage

1. **Launch the Application:**

   ```bash
   python main.py
   ```

2. **Select Language:**  
   Choose your preferred language (English or Turkish) upon startup.

3. **Account Management:**
   - Create a new account by entering your WordPress site URL, username, password, and OpenAI API key.
   - Alternatively, log into an existing account saved in the local SQLite database.

4. **Content Generation:**
   - Enter the article topic (this will also be used as the article title).
   - Optionally, enter Elementor elements for additional formatting.
   - Generate SEO metadata, content, and images.
   - The generated SEO meta title (used for Rank Math) remains auto-generated, while the article title is taken directly from your input.

5. **Posting to WordPress:**
   - Once content is generated, the program will upload images, create tags (with Rank Math meta data), and post the article or product description to your WordPress site.
   - For bulk posting, you can upload a file or paste multiple topics and schedule them for posting.

---

## File Structure

- **main.py:**  
  Entry point of the application.

- **ui_logic.py:**  
  Contains the Tkinter-based user interface logic and interactions with WordPress.

- **openai_logic.py:**  
  Handles content generation, SEO metadata creation, and image prompt generation using OpenAI’s API.

- **translations.py:**  
  Provides translation functions and language support for the UI and generated content.

- **database.py:**  
  Manages the SQLite database for storing and retrieving account credentials securely.

- **login_logic.py:**  
  Contains functions to verify WordPress credentials via the REST API.

- **env.txt:**  
  Contains configuration details, API keys, and additional instructions.

---

## Security Considerations

- **Encryption:**  
  Sensitive data such as passwords and API keys are encrypted using Fernet.  
  **Note:** The encryption key is hard-coded for development purposes; for production, load it from a secure environment variable or secrets manager.

- **API Keys:**  
  Avoid storing API keys in plaintext. Use environment variables and secure storage practices.

---

## Troubleshooting

- **UI Freezing:**  
  If the UI becomes unresponsive during long operations (like bulk generation), consider running API calls in separate threads.

- **API Errors:**  
  Ensure your API keys (both OpenAI and WordPress) are valid and that your network connection is stable. Review error messages in the console for guidance.

- **Tag Meta Update Issues:**  
  Verify that your WordPress site supports the custom Rank Math meta fields and that they are correctly registered using the provided PHP snippet.
